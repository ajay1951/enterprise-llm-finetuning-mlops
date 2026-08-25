import logging
try:
    import pynvml
    HAS_PYNVML = True
except ImportError:
    HAS_PYNVML = False

logger = logging.getLogger(__name__)

class GPUMonitor:
    def __init__(self):
        self.initialized = False
        if HAS_PYNVML:
            try:
                pynvml.nvmlInit()
                self.initialized = True
                self.device_count = pynvml.nvmlDeviceGetCount()
                logger.info(f"Initialized pynvml, found {self.device_count} GPUs.")
            except Exception as e:
                logger.warning(f"Failed to initialize pynvml: {e}")

    def get_metrics(self):
        if not self.initialized:
            return []
            
        metrics = []
        try:
            for i in range(self.device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
                temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                
                # Power usage in milliwatts, convert to W
                try:
                    power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0
                except pynvml.NVMLError:
                    power = 0.0

                metrics.append({
                    "id": i,
                    "utilization": float(util.gpu),
                    "memory_used_gb": mem.used / (1024**3),
                    "memory_total_gb": mem.total / (1024**3),
                    "temperature": float(temp),
                    "power_usage_w": float(power)
                })
        except Exception as e:
            logger.error(f"Error reading GPU metrics: {e}")
            
        return metrics

gpu_monitor = GPUMonitor()
