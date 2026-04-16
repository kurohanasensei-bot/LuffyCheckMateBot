# utils.py
import zipfile
import json
import aiofiles
from pathlib import Path
from typing import List, Dict
from datetime import datetime
import os

class ResultManager:
    def __init__(self, user_id: int, service: str):
        self.user_id = user_id
        self.service = service
        self.results = {"hits": [], "valid": [], "invalid": []}
        self.details = {"hits": [], "valid": [], "invalid": []}
        self.temp_dir = Path(f"temp/{user_id}/{datetime.now().timestamp()}")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.http_count = 0
        self.browser_count = 0

    def add_result(self, account: str, result_type: str, details: str, method: str = "http"):
        self.results[result_type].append(account)
        self.details[result_type].append(f"{account} ({details})")
        if method == "http":
            self.http_count += 1
        else:
            self.browser_count += 1

    async def save_files(self) -> str:
        """Save results to files and create ZIP"""
        hits_file = self.temp_dir / "hits.txt"
        valid_file = self.temp_dir / "valid.txt"
        invalid_file = self.temp_dir / "invalid.txt"
        summary_file = self.temp_dir / "summary.json"

        async with aiofiles.open(hits_file, 'w', encoding='utf-8') as f:
            await f.write("\n".join(self.details["hits"]))

        async with aiofiles.open(valid_file, 'w', encoding='utf-8') as f:
            await f.write("\n".join(self.details["valid"]))

        async with aiofiles.open(invalid_file, 'w', encoding='utf-8') as f:
            await f.write("\n".join(self.details["invalid"]))

        summary = {
            "service": self.service,
            "timestamp": datetime.now().isoformat(),
            "total": len(self.results["hits"]) + len(self.results["valid"]) + len(self.results["invalid"]),
            "hits": len(self.results["hits"]),
            "valid": len(self.results["valid"]),
            "invalid": len(self.results["invalid"]),
            "success_rate": (len(self.results["hits"]) / max(1, len(self.results["hits"]) + len(self.results["valid"]) + len(self.results["invalid"]))) * 100,
            "http_checks": self.http_count,
            "browser_checks": self.browser_count,
            "hits_list": self.results["hits"][:50],
            "valid_list": self.results["valid"][:50]
        }

        async with aiofiles.open(summary_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(summary, indent=2))

        zip_path = self.temp_dir / "results.zip"
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.write(hits_file, "hits.txt")
            zipf.write(valid_file, "valid.txt")
            zipf.write(invalid_file, "invalid.txt")
            zipf.write(summary_file, "summary.json")

        return str(zip_path)

    async def cleanup(self):
        """Clean up temporary files"""
        import shutil
        shutil.rmtree(self.temp_dir.parent, ignore_errors=True)

class ProgressTracker:
    def __init__(self, total: int):
        self.total = total
        self.completed = 0
        self.hits = 0
        self.valid = 0
        self.invalid = 0
        self.current_account = ""
        self.last_found = ""
        self.start_time = datetime.now()
        self.last_update_time = datetime.now()

    def update(self, hits=0, valid=0, invalid=0, current="", last=""):
        self.completed += hits + valid + invalid
        self.hits += hits
        self.valid += valid
        self.invalid += invalid
        if current:
            self.current_account = current
        if last:
            self.last_found = last
        self.last_update_time = datetime.now()

    def get_eta(self) -> float:
        if self.completed == 0:
            return 0
        elapsed = (datetime.now() - self.start_time).total_seconds()
        rate = self.completed / elapsed
        remaining = (self.total - self.completed) / rate if rate > 0 else 0
        return remaining

    def get_percentage(self) -> float:
        return (self.completed / self.total * 100) if self.total > 0 else 0

class FileProcessor:
    @staticmethod
    async def process_uploaded_file(file_path: str) -> List[str]:
        """Process uploaded .txt or .zip file"""
        accounts = []

        if file_path.endswith('.zip'):
            import zipfile
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                for file_info in zip_ref.filelist:
                    if file_info.filename.endswith('.txt'):
                        with zip_ref.open(file_info) as f:
                            content = f.read().decode('utf-8')
                            accounts.extend([line.strip() for line in content.split('\n') if ':' in line])
        else:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                accounts = [line.strip() for line in content.split('\n') if ':' in line]

        return list(dict.fromkeys(accounts))  # Remove duplicates