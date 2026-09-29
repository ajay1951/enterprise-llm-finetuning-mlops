import psutil
import logging

logger = logging.getLogger(__name__)


class SystemMonitor:
    def get_metrics(self):
        try:
            cpu_percent = psutil.cpu_percent(interval=None)  # Non-blocking
            ram = psutil.virtual_memory()

            return {
                "cpu_percent": float(cpu_percent),
                "ram_used_gb": float(ram.used / (1024**3)),
                "ram_total_gb": float(ram.total / (1024**3)),
            }
        except Exception as e:
            logger.error(f"Error reading system metrics: {e}")
            return {"cpu_percent": 0.0, "ram_used_gb": 0.0, "ram_total_gb": 0.0}


sys_monitor = SystemMonitor()
