#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
import time
import rumps
import psutil
import schedule
from pathlib import Path
import shutil
import os

APP_NAME = "Broom"
REFRESH_SEC = 5

# مسارات تنظيف شائعة على macOS
CLEAN_PATHS = [
    "/Library/Logs",
    "/System/Volumes/Data/Library/Logs",
    str(Path.home() / "Library/Logs"),
    str(Path.home() / "Library/Caches"),
    "/private/var/log",
    "/private/var/tmp",
]

def humanize_bytes(n):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"

def get_stats():
    cpu = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    return cpu, mem, disk

def safe_size(path):
    total = 0
    try:
        for root, _, files in os.walk(path):
            for f in files:
                try:
                    fp = os.path.join(root, f)
                    if os.path.islink(fp):
                        continue
                    total += os.path.getsize(fp)
                except Exception:
                    pass
    except Exception:
        pass
    return total

def scan_junk():
    """رجّع الحجم التقريبي للمخلفات قبل التنظيف."""
    total = 0
    for p in CLEAN_PATHS:
        if os.path.exists(p):
            total += safe_size(p)
    return total

def clean_junk():
    """تنظيف بسيط (حذف محتوى المجلدات المؤقتة)."""
    freed = 0
    for p in CLEAN_PATHS:
        if not os.path.exists(p):
            continue
        # احذف الملفات فقط واترك المجلدات نفسها
        for root, dirs, files in os.walk(p):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    size = os.path.getsize(fp)
                    os.remove(fp)
                    freed += size
                except Exception:
                    pass
            # خيار: تفريغ المجلدات الفارغة
            for d in dirs:
                dp = os.path.join(root, d)
                try:
                    if not os.listdir(dp):
                        shutil.rmtree(dp, ignore_errors=True)
                except Exception:
                    pass
    return freed

class BroomTray(rumps.App):
    def __init__(self):
        super(BroomTray, self).__init__(APP_NAME, template=True)
        self.icon = None  # يمكن وضع أيقونة لاحقًا .icns
        self.menu = [
            rumps.MenuItem("Scan (Estimate Junk)"),
            rumps.MenuItem("Clean Now"),
            None,
            rumps.MenuItem("Auto Clean: Off"),
            rumps.MenuItem("Run at Login (via LaunchAgent)…"),
            None,
            rumps.MenuItem("Quit")
        ]
        # جدولة تنظيف يومي افتراضيًا (مغلقة حتى تُفعّل)
        self.auto_clean_enabled = False
        schedule.clear()

        # تحديث العنوان بشكل دوري
        self.timer = rumps.Timer(self.refresh_title, REFRESH_SEC)
        self.timer.start()

        # خيط منفصل لتشغيل schedule بدون حجب واجهة rumps
        self.scheduler_thread = threading.Thread(target=self._run_schedule, daemon=True)
        self.scheduler_thread.start()

    def _run_schedule(self):
        while True:
            schedule.run_pending()
            time.sleep(1)

    @rumps.clicked("Scan (Estimate Junk)")
    def scan_clicked(self, _):
        size = scan_junk()
        rumps.notification(APP_NAME, "Scan complete", f"Estimated junk: {humanize_bytes(size)}")

    @rumps.clicked("Clean Now")
    def clean_clicked(self, _):
        size_before = scan_junk()
        freed = clean_junk()
        msg = f"Freed {humanize_bytes(freed)} (was ~{humanize_bytes(size_before)})"
        rumps.notification(APP_NAME, "Cleanup done", msg)

    @rumps.clicked("Auto Clean: Off")
    def toggle_auto_clean(self, item):
        self.auto_clean_enabled = not self.auto_clean_enabled
        if self.auto_clean_enabled:
            item.title = "Auto Clean: On (daily at 03:00)"
            schedule.clear("autoclean")
            schedule.every().day.at("03:00").do(clean_junk).tag("autoclean")
        else:
            item.title = "Auto Clean: Off"
            schedule.clear("autoclean")

    @rumps.clicked("Run at Login (via LaunchAgent)…")
    def show_launch_agent_help(self, _):
        txt = ("To run Broom at login on macOS:\n"
               "1) Save a LaunchAgent plist at ~/Library/LaunchAgents/com.broom.tray.plist\n"
               "2) Load it with: launchctl load ~/Library/LaunchAgents/com.broom.tray.plist\n"
               "3) Unload with: launchctl unload ~/Library/LaunchAgents/com.broom.tray.plist")
        rumps.alert(txt)

    @rumps.clicked("Quit")
    def quit_clicked(self, _):
        rumps.quit_application()

    def refresh_title(self, _):
        cpu, mem, disk = get_stats()
        self.title = f"🧹 {int(cpu)}% CPU | {int(mem)}% RAM | {int(disk)}% Disk"

if __name__ == "__main__":
    BroomTray().run()