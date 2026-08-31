import os
import shutil


def _mem_used_percent():
    try:
        info = {}
        with open("/proc/meminfo", "r", encoding="utf-8") as f:
            for line in f:
                parts = line.split(":")
                if len(parts) == 2:
                    info[parts[0].strip()] = int(parts[1].strip().split()[0])
        total = info.get("MemTotal")
        available = info.get("MemAvailable")
        if not total:
            return None
        return round((total - available) / total * 100, 1)
    except (OSError, ValueError, KeyError):
        return None


def get_system_stats():
    try:
        load1 = os.getloadavg()[0]
    except (OSError, AttributeError):
        load1 = None

    try:
        disk = shutil.disk_usage("/")
        disk_percent = round(disk.used / disk.total * 100, 1)
    except OSError:
        disk_percent = None

    return {
        "load1": load1,
        "mem_used_percent": _mem_used_percent(),
        "disk_used_percent": disk_percent,
    }
