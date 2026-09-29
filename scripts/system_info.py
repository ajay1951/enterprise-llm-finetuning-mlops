import sys
import platform
import importlib.util


def check_package(package_name: str) -> str:
    """Check if a package is installed and return its version."""
    try:
        if package_name == "bitsandbytes":
            import bitsandbytes

            return getattr(bitsandbytes, "__version__", "Available")
        elif package_name == "torch":
            import torch

            return torch.__version__
        elif package_name == "transformers":
            import transformers

            return transformers.__version__
        elif package_name == "trl":
            import trl

            return trl.__version__
        elif package_name == "peft":
            import peft

            return peft.__version__
        else:
            spec = importlib.util.find_spec(package_name)
            return "Available" if spec is not None else "Unavailable"
    except ImportError:
        return "Unavailable"
    except Exception:
        return "Error loading"


def main():
    print("ForgeLLM System Information")
    print("-" * 28)
    print(f"Python: {sys.version.split()[0]}")

    packages = ["torch", "transformers", "trl", "peft"]
    for pkg in packages:
        print(f"{pkg.capitalize()}: {check_package(pkg)}")

    print("\nCUDA Information")
    print("-" * 28)
    try:
        import torch

        cuda_available = torch.cuda.is_available()
        print(f"CUDA Available: {'YES' if cuda_available else 'NO'}")

        if cuda_available:
            print(f"CUDA Version: {torch.version.cuda}")
            device_count = torch.cuda.device_count()
            print(f"GPU Count: {device_count}")
            for i in range(device_count):
                props = torch.cuda.get_device_properties(i)
                vram_gb = props.total_memory / (1024**3)
                print(f"GPU {i}: {props.name}")
                print(f"VRAM: {vram_gb:.2f} GB")
    except ImportError:
        print("CUDA Available: NO (PyTorch not installed)")

    print(f"\nbitsandbytes: {check_package('bitsandbytes')}")


if __name__ == "__main__":
    main()
