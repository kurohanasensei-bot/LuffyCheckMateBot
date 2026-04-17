# Flask/Web
from flask import Flask
import threading
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_web, daemon=True).start()

# bot.py
from typing import List, Dict, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes
)
import asyncio
import aiosqlite
from datetime import datetime, timedelta
import os
from pathlib import Path
import tempfile
import zipfile

from config import BOT_TOKEN, ADMIN_IDS, PLANS, SERVICES, TIMEOUT_DEFAULT, MAX_CONCURRENT
from database import database
from utils import ResultManager, ProgressTracker, FileProcessor
from formatters import Formatter
from checkers.browser_checkers import BrowserChecker

# Queue system
class CheckQueue:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.active_tasks = []
        self.is_paused = False
        self.current_jobs = {}
        self.worker_task = None

    async def add_job(self, user_id: int, service: str, accounts: List[str]) -> int:
        queue_id = await database.add_to_queue(user_id, service, accounts)
        position = await database.get_queue_position(queue_id)

        # Get user's priority
        user = await database.get_user(user_id)
        priority = PLANS[user["plan"]]["priority"]

        await self.queue.put({
            "queue_id": queue_id,
            "user_id": user_id,
            "service": service,
            "accounts": accounts,
            "priority": priority
        })

        await database.add_log("INFO", f"Job {queue_id} added to queue for user {user_id}", user_id)
        return position

    async def worker(self, bot):
        while True:
            if self.is_paused:
                await asyncio.sleep(1)
                continue

            if len(self.active_tasks) >= MAX_CONCURRENT:
                await asyncio.sleep(1)
                continue

            # Get job with priority
            jobs = []
            while not self.queue.empty():
                jobs.append(await self.queue.get())

            if jobs:
                jobs.sort(key=lambda x: x["priority"])
                job = jobs[0]
                for remaining_job in jobs[1:]:
                    await self.queue.put(remaining_job)

                task = asyncio.create_task(self.process_job(bot, job))
                self.active_tasks.append(task)
                task.add_done_callback(lambda t: self.active_tasks.remove(t))

            await asyncio.sleep(0.5)

    async def process_job(self, bot, job):
        user_id = job["user_id"]
        service = job["service"]
        accounts = job["accounts"]

        # Check user's daily limit
        user = await database.get_user(user_id)
        if not user:
            await bot.send_message(user_id, "❌ User not found! Please use /start")
            return

        plan = user["plan"]
        daily_used = await database.get_daily_usage(user_id)
        max_checks = PLANS[plan]["checks_per_day"]

        if max_checks != float("inf") and daily_used >= max_checks:
            await bot.send_message(
                user_id,
                f"❌ Daily limit reached! You've used {daily_used}/{max_checks} checks today.\nUpgrade to premium for unlimited checks!"
            )
            await database.add_log("WARNING", f"User {user_id} reached daily limit", user_id)
            return

        # Process accounts
        remaining = max_checks - daily_used if max_checks != float("inf") else len(accounts)
        accounts_to_check = accounts[:remaining]

        tracker = ProgressTracker(len(accounts_to_check))
        result_manager = ResultManager(user_id, service)

        # Send initial progress message
        progress_msg = await bot.send_message(
            user_id, 
            Formatter.format_live_progress(
                0, len(accounts_to_check), 0, 0, 0, "Starting...", "None", 0
            )
        )

        # Get user settings
        settings = user.get("settings", {})
        headless = settings.get("headless", True)
        timeout = settings.get("timeout", TIMEOUT_DEFAULT)
        proxy = settings.get("proxy")

        browser_checker = BrowserChecker(headless=headless, timeout=timeout, proxy=proxy)

        hits_count = 0
        valid_count = 0
        invalid_count = 0

        for i, account in enumerate(accounts_to_check):
            if ":" not in account:
                invalid_count += 1
                result_manager.add_result(account, "invalid", "Invalid format (missing :)", "http")
                continue

            email, password = account.split(":", 1)

            # Try to use service-specific checker
            checker_func = getattr(browser_checker, f"check_{service}", None)

            if checker_func:
                try:
                    success, details = await checker_func(email, password)

                    if success:
                        if any(word in details.lower() for word in ["premium", "plus", "pro", "unlimited", "subscription"]):
                            result_manager.add_result(account, "hits", details, "browser")
                            hits_count += 1
                            last_type = f"HIT on {service}"
                        else:
                            result_manager.add_result(account, "valid", details, "browser")
                            valid_count += 1
                            last_type = f"VALID on {service}"
                    else:
                        result_manager.add_result(account, "invalid", details, "browser")
                        invalid_count += 1
                        last_type = f"INVALID on {service}"

                    # Update tracker
                    tracker.update(
                        hits=1 if success and ("premium" in details.lower() or "plus" in details.lower()) else 0,
                        valid=1 if success and not ("premium" in details.lower() or "plus" in details.lower()) else 0,
                        invalid=0 if success else 1,
                        current=account[:50],
                        last=last_type
                    )

                except Exception as e:
                    result_manager.add_result(account, "invalid", f"Error: {str(e)[:50]}", "browser")
                    invalid_count += 1
                    tracker.update(invalid=1, current=account[:50], last=f"ERROR on {service}")
            else:
                result_manager.add_result(account, "invalid", f"Service {service} not implemented", "browser")
                invalid_count += 1
                tracker.update(invalid=1, current=account[:50], last=f"NOT IMPLEMENTED")

            # Update progress every 3 accounts
            if (i + 1) % 3 == 0 or i == len(accounts_to_check) - 1:
                try:
                    await progress_msg.edit_text(
                        Formatter.format_live_progress(
                            tracker.completed,
                            tracker.total,
                            tracker.hits,
                            tracker.valid,
                            tracker.invalid,
                            tracker.current_account,
                            tracker.last_found,
                            tracker.get_eta()
                        )
                    )
                except:
                    pass  # Message might be too old to edit

            await asyncio.sleep(1)  # Rate limiting

        # Save results and send ZIP
        zip_path = await result_manager.save_files()

        # Update database stats
        await database.increment_stats(user_id, hits_count, valid_count, invalid_count)
        await database.increment_daily_usage(user_id, len(accounts_to_check), hits_count)

        # Send final results
        final_message = Formatter.format_results(
            SERVICES[service]['name'],
            result_manager.details["hits"],
            result_manager.details["valid"],
            result_manager.details["invalid"],
            tracker.get_eta(),
            result_manager.http_count,
            result_manager.browser_count
        )

        await bot.send_message(user_id, final_message)

        # Send ZIP file
        with open(zip_path, 'rb') as f:
            await bot.send_document(user_id, f, filename=f"results_{service}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip")

        await result_manager.cleanup()

        # Update queue status
        async with aiosqlite.connect("accounts.db") as db:
            await db.execute(
                "UPDATE queue SET status = 'completed', completed_at = ? WHERE id = ?",
                (datetime.now().isoformat(), job["queue_id"])
            )
            await db.commit()

        await database.add_log("INFO", f"Job {job['queue_id']} completed for user {user_id}", user_id)

queue_system = CheckQueue()

HOME_IMAGE_PATH = Path("attached_assets/IMG_20260414_064820_499_1776330972951.png")

def build_home_keyboard(user_id: int):
    keyboard = [
        [InlineKeyboardButton("🚀 Start Checking", callback_data="services")],
        [InlineKeyboardButton("📊 My Stats", callback_data="stats")],
        [InlineKeyboardButton("💎 Membership", callback_data="membership")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]

    if user_id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel")])

    return InlineKeyboardMarkup(keyboard)

def build_nav_keyboard(back_data: str = "back"):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔙 Back", callback_data=back_data),
            InlineKeyboardButton("🏠 Home", callback_data="home")
        ]
    ])

def build_home_text(user, db_user, daily_used, max_display):
    return (
        f"🎬 Welcome {user.first_name}!\n\n"
        f"Your personal streaming account checker.\n"
        f"Current plan: {db_user['plan'].upper()}\n"
        f"Today's usage: {daily_used}/{max_display}\n\n"
        f"Select an option below:"
    )

async def edit_menu_message(query, text: str, reply_markup=None):
    if query.message and query.message.photo:
        try:
            await query.edit_message_caption(caption=text, reply_markup=reply_markup)
            return
        except Exception:
            pass
    await query.edit_message_text(text=text, reply_markup=reply_markup)

async def show_home(update: Update, context: ContextTypes.DEFAULT_TYPE, edit: bool = False):
    user = update.effective_user
    db_user = await database.get_user(user.id)

    if not db_user:
        await database.create_user(user.id, user.username)
        db_user = await database.get_user(user.id)
        await database.add_log("INFO", f"New user registered: {user.id}", user.id)

    daily_used = await database.get_daily_usage(user.id)
    max_checks = PLANS[db_user["plan"]]["checks_per_day"]
    max_display = "∞" if max_checks == float("inf") else max_checks
    reply_markup = build_home_keyboard(user.id)
    text = build_home_text(user, db_user, daily_used, max_display)

    query = update.callback_query
    if edit and query:
        await edit_menu_message(query, text, reply_markup)
        return

    chat_id = update.effective_chat.id
    if HOME_IMAGE_PATH.exists():
        with HOME_IMAGE_PATH.open("rb") as photo:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=text,
                reply_markup=reply_markup
            )
    else:
        await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)

# Bot command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_home(update, context, edit=False)

async def services_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Create services keyboard
    keyboard = []
    row = []
    for service_id, service_info in SERVICES.items():
        row.append(InlineKeyboardButton(
            f"{service_info['icon']} {service_info['name']}",
            callback_data=f"check_{service_id}"
        ))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton("🔙 Back", callback_data="back"),
        InlineKeyboardButton("🏠 Home", callback_data="home")
    ])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await edit_menu_message(
        query,
        "🚀 Select a service to check:",
        reply_markup
    )

async def check_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    service = query.data.replace("check_", "")
    context.user_data['current_service'] = service

    keyboard = [
        [InlineKeyboardButton("📝 Text Input", callback_data="input_text")],
        [InlineKeyboardButton("📎 Upload .txt", callback_data="input_txt")],
        [InlineKeyboardButton("🗜️ Upload .zip", callback_data="input_zip")],
        [
            InlineKeyboardButton("🔙 Back", callback_data="services"),
            InlineKeyboardButton("🏠 Home", callback_data="home")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await edit_menu_message(
        query,
        f"{SERVICES[service]['icon']} {SERVICES[service]['name']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Choose input method:\n\n"
        f"📝 Text: Send email:pass per line\n"
        f"📎 .txt: Upload file with accounts\n"
        f"🗜️ .zip: Upload zip with .txt files",
        reply_markup
    )

async def handle_input_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    method = query.data
    service = context.user_data.get('current_service')
    back_data = f"check_{service}" if service else "services"
    reply_markup = build_nav_keyboard(back_data)
    if method == "input_text":
        context.user_data['awaiting_input'] = "text"
        await edit_menu_message(
            query,
            "📝 Send your accounts in text format:\n\n"
            "Example:\n"
            "email1@example.com:password1\n"
            "email2@example.com:password2\n\n"
            "Send /cancel to cancel",
            reply_markup
        )
    elif method == "input_txt":
        context.user_data['awaiting_input'] = "file"
        await edit_menu_message(
            query,
            "📎 Upload a .txt file with accounts (one per line, format: email:pass)\n\n"
            "Send /cancel to cancel",
            reply_markup
        )
    elif method == "input_zip":
        context.user_data['awaiting_input'] = "zip"
        await edit_menu_message(
            query,
            "🗜️ Upload a .zip file containing .txt files with accounts\n\n"
            "Send /cancel to cancel",
            reply_markup
        )

async def handle_accounts_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('awaiting_input'):
        return

    service = context.user_data.get('current_service')
    if not service:
        await update.message.reply_text("Please select a service first using /services")
        return

    accounts = []

    if context.user_data['awaiting_input'] == "text":
        accounts = [line.strip() for line in update.message.text.split('\n') if ':' in line]

    elif context.user_data['awaiting_input'] in ["file", "zip"]:
        if not update.message.document:
            await update.message.reply_text("Please upload a file")
            return

        file = await update.message.document.get_file()

        # Download to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{update.message.document.file_name}") as tmp_file:
            await file.download_to_drive(tmp_file.name)
            tmp_path = tmp_file.name

        try:
            if context.user_data['awaiting_input'] == "zip" and update.message.document.file_name.endswith('.zip'):
                accounts = await FileProcessor.process_uploaded_file(tmp_path)
            elif update.message.document.file_name.endswith('.txt'):
                accounts = await FileProcessor.process_uploaded_file(tmp_path)
            else:
                await update.message.reply_text("Please upload a .txt or .zip file")
                os.unlink(tmp_path)
                return
        finally:
            os.unlink(tmp_path)

    if not accounts:
        await update.message.reply_text("No valid accounts found (format: email:pass per line)")
        return

    # Check daily limit
    user = await database.get_user(update.effective_user.id)
    plan = user["plan"]
    daily_used = await database.get_daily_usage(update.effective_user.id)
    max_checks = PLANS[plan]["checks_per_day"]

    if max_checks != float("inf") and daily_used >= max_checks:
        await update.message.reply_text(
            f"❌ Daily limit reached! You've used {daily_used}/{max_checks} today.\n"
            f"Upgrade to premium for unlimited checks: /membership"
        )
        context.user_data['awaiting_input'] = None
        return

    # Add to queue
    position = await queue_system.add_job(update.effective_user.id, service, accounts)

    await update.message.reply_text(
        f"✅ Added to queue!\n"
        f"📊 Position: #{position}\n"
        f"🔍 Service: {SERVICES[service]['name']}\n"
        f"📝 Accounts: {len(accounts)}\n"
        f"⚡ Plan: {plan.upper()}\n\n"
        f"You'll be notified when processing starts..."
    )

    context.user_data['awaiting_input'] = None

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        user_id = query.from_user.id
    else:
        user_id = update.effective_user.id

    user = await database.get_user(user_id)
    if not user:
        if query:
            await edit_menu_message(query, "Please use /start first", build_nav_keyboard())
        else:
            await update.message.reply_text("Please use /start first")
        return

    daily_used = await database.get_daily_usage(user_id)
    max_checks = PLANS[user["plan"]]["checks_per_day"]

    # Get today's hits
    async with aiosqlite.connect("accounts.db") as db:
        async with db.execute(
            "SELECT hits_today FROM daily_usage WHERE user_id = ? AND date = ?",
            (user_id, datetime.now().date().isoformat())
        ) as cursor:
            row = await cursor.fetchone()
            hits_today = row[0] if row else 0
            user['hits_today'] = hits_today

    stats_text = Formatter.format_stats(user, daily_used, max_checks)

    reply_markup = build_nav_keyboard()

    if query:
        await edit_menu_message(query, stats_text, reply_markup)
    else:
        await update.message.reply_text(stats_text, reply_markup=reply_markup)

async def membership_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        user_id = query.from_user.id
    else:
        user_id = update.effective_user.id

    user = await database.get_user(user_id)
    membership_text = Formatter.format_membership(user["plan"])

    reply_markup = build_nav_keyboard()

    if query:
        await edit_menu_message(query, membership_text, reply_markup)
    else:
        await update.message.reply_text(membership_text, reply_markup=reply_markup)

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        user_id = query.from_user.id
    else:
        user_id = update.effective_user.id

    user = await database.get_user(user_id)
    settings_text = Formatter.format_settings(user.get("settings", {}))

    keyboard = [
        [InlineKeyboardButton("🌐 Set Proxy", callback_data="set_proxy")],
        [InlineKeyboardButton("⏱️ Set Timeout", callback_data="set_timeout")],
        [InlineKeyboardButton("🖥️ Toggle Headless", callback_data="toggle_headless")],
        [
            InlineKeyboardButton("🔙 Back", callback_data="back"),
            InlineKeyboardButton("🏠 Home", callback_data="home")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await edit_menu_message(query, settings_text, reply_markup)
    else:
        await update.message.reply_text(settings_text, reply_markup=reply_markup)

async def set_proxy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data['setting_proxy'] = True
    await edit_menu_message(
        query,
        "🌐 Send your proxy in format:\n\n"
        "HTTP: http://host:port\n"
        "SOCKS5: socks5://host:port\n"
        "With auth: http://user:pass@host:port\n\n"
        "Send 'none' to disable proxy\n"
        "Send /cancel to cancel",
        build_nav_keyboard("settings")
    )

async def set_timeout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data['setting_timeout'] = True
    await edit_menu_message(
        query,
        "⏱️ Send timeout in seconds (5-60):\n\n"
        "Default: 15 seconds\n"
        "Send /cancel to cancel",
        build_nav_keyboard("settings")
    )

async def toggle_headless(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = await database.get_user(update.effective_user.id)
    settings = user.get("settings", {})
    settings["headless"] = not settings.get("headless", True)
    await database.update_user_settings(update.effective_user.id, settings)

    await settings_command(update, context)

async def handle_settings_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('setting_proxy'):
        proxy = update.message.text.strip()
        user = await database.get_user(update.effective_user.id)
        settings = user.get("settings", {})

        if proxy.lower() == 'none':
            settings['proxy'] = None
            await update.message.reply_text("✅ Proxy disabled")
        else:
            settings['proxy'] = proxy
            await update.message.reply_text(f"✅ Proxy set to: {proxy}")

        await database.update_user_settings(update.effective_user.id, settings)
        context.user_data['setting_proxy'] = False

        await asyncio.sleep(1)
        await settings_command(update, context)

    elif context.user_data.get('setting_timeout'):
        try:
            timeout = int(update.message.text.strip())
            if 5 <= timeout <= 60:
                user = await database.get_user(update.effective_user.id)
                settings = user.get("settings", {})
                settings['timeout'] = timeout
                await database.update_user_settings(update.effective_user.id, settings)
                await update.message.reply_text(f"✅ Timeout set to {timeout} seconds")
            else:
                await update.message.reply_text("❌ Timeout must be between 5 and 60 seconds")
        except ValueError:
            await update.message.reply_text("❌ Please send a valid number")

        context.user_data['setting_timeout'] = False
        await asyncio.sleep(1)
        await settings_command(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        await edit_menu_message(query, Formatter.format_help(), build_nav_keyboard())
    else:
        await update.message.reply_text(Formatter.format_help(), reply_markup=build_nav_keyboard())

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await show_home(update, context, edit=True)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Cancelled")

# Admin commands
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin access required!")
        return

    admin_text = """
👑 ADMIN PANEL 👑
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Commands:
/stats_all - View all users
/upgrade @username plan - Upgrade user
/downgrade @username - Downgrade to free
/broadcast message - Send to all users
/reset_user @username - Reset daily usage
/view_queue - Show pending jobs
/pause - Pause queue
/resume - Resume queue
/logs - View system logs
/add_credits @username amount - Add extra credits
"""

    await update.message.reply_text(admin_text)

async def stats_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return

    users = await database.get_all_users()
    stats_text = "📊 ALL USERS STATS 📊\n━━━━━━━━━━━━━━━━━━━━\n"

    for user in users:
        daily_used = await database.get_daily_usage(user["user_id"])
        stats_text += f"\n@{user['username']}: {user['plan']} | {daily_used} today"

        if len(stats_text) > 3900:
            await update.message.reply_text(stats_text)
            stats_text = ""

    if stats_text:
        await update.message.reply_text(stats_text)

async def upgrade_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return

    try:
        username = context.args[0].replace("@", "")
        plan = context.args[1].lower()

        if plan not in PLANS:
            await update.message.reply_text("Invalid plan! Options: free/weekly/monthly/yearly/admin")
            return

        # Find user by username
        users = await database.get_all_users()
        target_user = None
        for user in users:
            if user["username"] == username:
                target_user = user
                break

        if not target_user:
            await update.message.reply_text(f"User @{username} not found!")
            return

        expiry = None
        if plan in ["weekly", "monthly", "yearly"]:
            days = {"weekly": 7, "monthly": 30, "yearly": 365}
            expiry = (datetime.now() + timedelta(days=days[plan])).isoformat()

        await database.update_plan(target_user["user_id"], plan, expiry)
        await update.message.reply_text(f"✅ Upgraded @{username} to {plan.upper()}!")

        # Notify user
        try:
            await context.bot.send_message(
                target_user["user_id"],
                f"🎉 Congratulations! Your account has been upgraded to {plan.upper()}!\n\n"
                f"New limits: {PLANS[plan]['checks_per_day'] if PLANS[plan]['checks_per_day'] != float('inf') else 'Unlimited'} checks per day"
            )
        except:
            pass

    except IndexError:
        await update.message.reply_text("Usage: /upgrade @username plan")

async def downgrade_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return

    try:
        username = context.args[0].replace("@", "")

        users = await database.get_all_users()
        target_user = None
        for user in users:
            if user["username"] == username:
                target_user = user
                break

        if not target_user:
            await update.message.reply_text(f"User @{username} not found!")
            return

        await database.update_plan(target_user["user_id"], "free", None)
        await update.message.reply_text(f"✅ Downgraded @{username} to FREE!")

        try:
            await context.bot.send_message(
                target_user["user_id"],
                "⚠️ Your account has been downgraded to FREE plan.\n"
                "You now have 25 checks per day."
            )
        except:
            pass

    except IndexError:
        await update.message.reply_text("Usage: /downgrade @username")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return

    message = " ".join(context.args)
    if not message:
        await update.message.reply_text("Usage: /broadcast message")
        return

    users = await database.get_all_users()
    sent = 0
    failed = 0

    status_msg = await update.message.reply_text(f"📢 Broadcasting to {len(users)} users...")

    for user in users:
        try:
            await context.bot.send_message(
                user["user_id"],
                f"📢 ANNOUNCEMENT\n\n{message}\n\n- Admin"
            )
            sent += 1
            await asyncio.sleep(0.05)
        except:
            failed += 1

    await status_msg.edit_text(f"✅ Broadcast sent!\nSent: {sent}\nFailed: {failed}")

async def reset_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return

    try:
        username = context.args[0].replace("@", "")

        users = await database.get_all_users()
        target_user = None
        for user in users:
            if user["username"] == username:
                target_user = user
                break

        if not target_user:
            await update.message.reply_text(f"User @{username} not found!")
            return

        await database.reset_daily_usage(target_user["user_id"])
        await update.message.reply_text(f"✅ Reset daily usage for @{username}")

    except IndexError:
        await update.message.reply_text("Usage: /reset_user @username")

async def view_queue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return

    jobs = await database.get_pending_queue()

    if not jobs:
        await update.message.reply_text("Queue is empty!")
        return

    queue_text = "📊 QUEUE STATUS\n━━━━━━━━━━━━━━━━\n"
    for i, job in enumerate(jobs[:20], 1):
        user = await database.get_user(job["user_id"])
        queue_text += f"\n{i}. #{job['id']} | @{user['username']} | {SERVICES[job['service']]['name']}"

    if len(jobs) > 20:
        queue_text += f"\n\n... and {len(jobs) - 20} more"

    await update.message.reply_text(queue_text)

async def pause_queue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return

    queue_system.is_paused = True
    await update.message.reply_text("⏸️ Queue paused!")

async def resume_queue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return

    queue_system.is_paused = False
    await update.message.reply_text("▶️ Queue resumed!")

async def view_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return

    logs = await database.get_logs(50)

    if not logs:
        await update.message.reply_text("No logs found")
        return

    log_text = "📋 SYSTEM LOGS\n━━━━━━━━━━━━━━━━\n"
    for log in logs[:30]:
        log_text += f"\n[{log['timestamp'][:19]}] {log['level']}: {log['message'][:50]}"

    await update.message.reply_text(log_text)

async def add_credits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return

    try:
        username = context.args[0].replace("@", "")
        amount = int(context.args[1])

        users = await database.get_all_users()
        target_user = None
        for user in users:
            if user["username"] == username:
                target_user = user
                break

        if not target_user:
            await update.message.reply_text(f"User @{username} not found!")
            return

        # This is a placeholder - implement custom credits system if needed
        await update.message.reply_text(f"✅ Added {amount} credits to @{username}")

    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /add_credits @username amount")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    await database.add_log("ERROR", f"Error: {context.error}", update.effective_user.id if update else None)

    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ An error occurred. Please try again later or contact support."
        )

async def admin_panel_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if update.effective_user.id not in ADMIN_IDS:
        await edit_menu_message(query, "❌ Admin access required!", build_nav_keyboard())
        return

    admin_text = """
👑 ADMIN PANEL 👑
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Commands:
/stats_all - View all users
/upgrade @username plan - Upgrade user
/downgrade @username - Downgrade to free
/broadcast message - Send to all users
/reset_user @username - Reset daily usage
/view_queue - Show pending jobs
/pause - Pause queue
/resume - Resume queue
/logs - View system logs
/add_credits @username amount - Add extra credits
"""
    await edit_menu_message(query, admin_text, build_nav_keyboard())

# Main bot setup
def main():
    # Create temp directory
    Path("temp").mkdir(exist_ok=True)

    # Initialize database
    asyncio.run(database.init_db())

    # Create bot application
    application = Application.builder().token(BOT_TOKEN).build()

    # User commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("services", services_menu))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("membership", membership_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", cancel))

    # Admin commands
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("stats_all", stats_all))
    application.add_handler(CommandHandler("upgrade", upgrade_user))
    application.add_handler(CommandHandler("downgrade", downgrade_user))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("reset_user", reset_user))
    application.add_handler(CommandHandler("view_queue", view_queue))
    application.add_handler(CommandHandler("pause", pause_queue))
    application.add_handler(CommandHandler("resume", resume_queue))
    application.add_handler(CommandHandler("logs", view_logs))
    application.add_handler(CommandHandler("add_credits", add_credits))

    # Settings commands
    application.add_handler(CommandHandler("set_proxy", set_proxy))
    application.add_handler(CommandHandler("set_timeout", set_timeout))
    application.add_handler(CommandHandler("toggle_headless", toggle_headless))

    # Callback handlers
    application.add_handler(CallbackQueryHandler(admin_panel_button, pattern="^admin_panel$"))
    application.add_handler(CallbackQueryHandler(services_menu, pattern="^services$"))
    application.add_handler(CallbackQueryHandler(stats_command, pattern="^stats$"))
    application.add_handler(CallbackQueryHandler(membership_command, pattern="^membership$"))
    application.add_handler(CallbackQueryHandler(settings_command, pattern="^settings$"))
    application.add_handler(CallbackQueryHandler(help_command, pattern="^help$"))
    application.add_handler(CallbackQueryHandler(back_to_menu, pattern="^back$"))
    application.add_handler(CallbackQueryHandler(back_to_menu, pattern="^home$"))
    application.add_handler(CallbackQueryHandler(check_service, pattern="^check_"))
    application.add_handler(CallbackQueryHandler(handle_input_method, pattern="^(input_text|input_txt|input_zip)$"))
    application.add_handler(CallbackQueryHandler(set_proxy, pattern="^set_proxy$"))
    application.add_handler(CallbackQueryHandler(set_timeout, pattern="^set_timeout$"))
    application.add_handler(CallbackQueryHandler(toggle_headless, pattern="^toggle_headless$"))

    # Message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_accounts_input))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_settings_input))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_accounts_input))

    # Error handler
    application.add_error_handler(error_handler)

    # Start queue worker
    async def start_worker():
        asyncio.create_task(queue_system.worker(application.bot))

    # Start bot
    print("🤖 Bot started!")
    print(f"Admin IDs: {ADMIN_IDS}")
    print(f"Services available: {len(SERVICES)}")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(start_worker())
    application.run_polling()

if __name__ == "__main__":
    main()
