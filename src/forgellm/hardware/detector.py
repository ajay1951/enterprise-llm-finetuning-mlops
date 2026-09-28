import platform
from dataclasses import dataclass

import psutil
import torch


@dataclass
class HardwareProfile:
    os_name: str
    cpu_arch: str
    ram_gb: float
    cuda_available: bool
    cuda_version: str
    gpu_count: int
    gpu_names: list[str]
    vram_gb: list[float]
    pytorch_version: str
    bitsandbytes_version: str

class HardwareDetector:
    @staticmethod
    def detect() -> HardwareProfile:
        os_name = platform.system()
        cpu_arch = platform.machine()
        ram_gb = round(psutil.virtual_memory().total / (1024**3), 2)
        
        cuda_available = torch.cuda.is_available()
        cuda_version = torch.version.cuda if cuda_available else "N/A"
        
        gpu_count = torch.cuda.device_count() if cuda_available else 0
        gpu_names = [torch.cuda.get_device_name(i) for i in range(gpu_count)]
        
        vram_gb = []
        for i in range(gpu_count):
            props = torch.cuda.get_device_properties(i)
            vram_gb.append(round(props.total_memory / (1024**3), 2))
            
        try:
            import bitsandbytes
            bnb_version = bitsandbytes.__version__
        except ImportError:
            bnb_version = "Not installed"
            
        return HardwareProfile(
            os_name=os_name,
            cpu_arch=cpu_arch,
            ram_gb=ram_gb,
            cuda_available=cuda_available,
            cuda_version=cuda_version,
            gpu_count=gpu_count,
            gpu_names=gpu_names,
            vram_gb=vram_gb,
            pytorch_version=torch.__version__,
            bitsandbytes_version=bnb_version
        )
