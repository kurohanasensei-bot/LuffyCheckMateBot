# formatters.py
from typing import List, Dict
from datetime import datetime

class Formatter:
    @staticmethod
    def progress_bar(percentage: float, width: int = 30) -> str:
        filled = int(width * percentage / 100)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}] {percentage:.0f}%"
    
    @staticmethod
    def format_time(seconds: float) -> str:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        if minutes > 0:
            return f"{minutes}m {secs}s"
        return f"{secs}s"
    
    @staticmethod
    def format_number(num: int) -> str:
        return f"{num:,}"
    
    @staticmethod
    def get_spinner(index: int) -> str:
        spinners = ["🔄", "⚙️", "🔧", "⚡", "🎯", "🚀"]
        return spinners[index % len(spinners)]
    
    @staticmethod
    def format_live_progress(
        completed: int,
        total: int,
        hits: int,
        valid: int,
        invalid: int,
        current_account: str,
        last_found: str,
        eta_seconds: float
    ) -> str:
        percentage = (completed / total * 100) if total > 0 else 0
        spinner = Formatter.get_spinner(completed)
        
        return f"""
{spinner} LIVE CHECKING {spinner}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{Formatter.progress_bar(percentage)}

📊 {completed}/{total} accounts • {percentage:.0f}%
⏱️ ETA: {Formatter.format_time(eta_seconds)}

🟢 HITS: {hits}  |  🟡 VALID: {valid}  |  🔴 INVALID: {invalid}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ Current: {current_account[:50]}
✅ Last found: {last_found}
"""
    
    @staticmethod
    def format_results(
        service_name: str,
        hits: List[str],
        valid: List[str],
        invalid: List[str],
        time_taken: float,
        http_count: int,
        browser_count: int
    ) -> str:
        total = len(hits) + len(valid) + len(invalid)
        success_rate = (len(hits) / total * 100) if total > 0 else 0
        
        result_text = f"""
🔥 {service_name.upper()} RESULTS 🔥
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        if hits:
            result_text += f"\n🟢 HITS ({len(hits)})\n"
            for hit in hits[:10]:  # Show first 10
                result_text += f"• {hit}\n"
            if len(hits) > 10:
                result_text += f"... and {len(hits) - 10} more\n"
        
        if valid:
            result_text += f"\n🟡 VALID ({len(valid)})\n"
            for v in valid[:5]:
                result_text += f"• {v}\n"
            if len(valid) > 5:
                result_text += f"... and {len(valid) - 5} more\n"
        
        if invalid:
            result_text += f"\n🔴 INVALID ({len(invalid)})\n"
            for inv in invalid[:5]:
                result_text += f"• {inv}\n"
            if len(invalid) > 5:
                result_text += f"... and {len(invalid) - 5} more\n"
        
        result_text += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Success Rate: {success_rate:.1f}%
⏱️ Time taken: {Formatter.format_time(time_taken)}
⚡ Method: HTTP ({http_count}) / Browser ({browser_count})

📁 ZIP file sent with:
• hits.txt
• valid.txt
• invalid.txt
• summary.json
"""
        
        return result_text
    
    @staticmethod
    def format_stats(user: Dict, daily_used: int, max_checks: int) -> str:
        total_checks = user["total_scans"]
        success_rate = (user["total_hits"] / total_checks * 100) if total_checks > 0 else 0
        
        # Determine rank
        if user["total_hits"] >= 500:
            rank = "👑 Legend"
        elif user["total_hits"] >= 200:
            rank = "💎 Diamond"
        elif user["total_hits"] >= 100:
            rank = "🥇 Gold"
        elif user["total_hits"] >= 50:
            rank = "🥈 Silver"
        elif user["total_hits"] >= 10:
            rank = "🥉 Bronze"
        else:
            rank = "🌱 Newbie"
        
        max_display = "∞" if max_checks == float("inf") else max_checks
        
        return f"""
📊 YOUR STATISTICS 📊
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 User: @{user['username']}
⭐ Plan: {user['plan'].upper()}
📅 Joined: {user['join_date']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 TODAY:
• Used: {daily_used}/{max_display}
• Hits today: {user.get('hits_today', 0)}

📊 LIFETIME:
• Total scans: {Formatter.format_number(user['total_scans'])}
• Total hits: {Formatter.format_number(user['total_hits'])}
• Total valid: {Formatter.format_number(user['total_valid'])}
• Total invalid: {Formatter.format_number(user['total_invalid'])}

🎯 Success rate: {success_rate:.1f}%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏆 Rank: {rank}
"""
    
    @staticmethod
    def format_settings(settings: Dict) -> str:
        return f"""
⚙️ SETTINGS ⚙️
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌐 Proxy Mode: {settings.get('proxy', 'None')}
⏱️ Timeout: {settings.get('timeout', 15)} seconds
🖥️ Headless: {'Yes' if settings.get('headless', True) else 'No'}
💾 Save All: {'Yes' if settings.get('save_all', False) else 'No'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Commands:
/set_proxy - Configure proxy
/set_timeout - Change timeout
/toggle_headless - Browser visibility
/export_settings - Export config
"""
    
    @staticmethod
    def format_help() -> str:
        return """
❓ HELP & SUPPORT ❓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📖 HOW TO USE:

1️⃣ Select service: /services
2️⃣ Send accounts (email:pass per line)
3️⃣ Get results with live progress

🎯 RESULT TYPES:
🟢 HIT = Premium subscription
🟡 VALID = Free account
🔴 INVALID = Wrong credentials

💎 MEMBERSHIP:
• FREE: 25 checks/day
• PREMIUM: Unlimited checks

🆘 Support: @WatashiWaSenseiBot
"""
    
    @staticmethod
    def format_membership(current_plan: str) -> str:
        return f"""
💎 MEMBERSHIP PLANS 💎
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⭐ CURRENT: {current_plan.upper()}

┌─────────────────────────────────┐
│ 🔵 FREE      │ $0     │ 25/day │
│ 🟠 WEEKLY    │ $5     │ 50/day │
│ 🟢 MONTHLY   │ $10    │ ∞/day  │
│ 🟣 YEARLY    │ $50    │ ∞/day  │
└─────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💬 Contact: @WatashiWaSenseiBot
💳 Payment: Crypto / Card / Gift Card
"""
    
    @staticmethod
    def format_services_menu(services: Dict) -> str:
        menu = "🚀 AVAILABLE SERVICES 🚀\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Group services by category
        categories = {
            "🎬 STREAMING": list(services.keys())[:15],
            "🎵 MUSIC": list(services.keys())[15:18],
            "🤖 AI": list(services.keys())[18:22],
            "🛡️ VPN": list(services.keys())[22:25],
            "🎨 PRODUCTIVITY": list(services.keys())[25:26]
        }
        
        for category, service_list in categories.items():
            menu += f"{category}\n"
            for i in range(0, len(service_list), 2):
                row = []
                for j in range(2):
                    if i + j < len(service_list):
                        service_id = service_list[i + j]
                        service = services[service_id]
                        row.append(f"{service['icon']} {service['name']}")
                menu += "        ".join(row) + "\n"
            menu += "\n"
        
        menu += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        menu += "Click any service to start checking"
        
        return menu
