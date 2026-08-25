import torch
from forgellm.training.config import QuantizationConfig

def get_quantization_config(config: QuantizationConfig):
    if not config.enabled:
        return None

    if not torch.cuda.is_available():
        raise RuntimeError(
            "ERROR: QLoRA requires a compatible CUDA/bitsandbytes environment.\n"
            "Detected:\n"
            "CUDA: unavailable\n"
            "GPU: CPU\n\n"
            "Suggested action:\n"
            "Run ForgeLLM on a CUDA-enabled GPU environment or\n"
            "disable 4-bit quantization for a compatible training configuration."
        )
    
    try:
        import bitsandbytes
    except ImportError:
        raise RuntimeError(
            "ERROR: QLoRA requires bitsandbytes to be installed.\n"
            "Suggested action:\n"
            "pip install bitsandbytes"
        )
        
    try:
        from transformers import BitsAndBytesConfig
    except ImportError:
        raise RuntimeError("ERROR: transformers library is missing or outdated.")
        
    if config.bits == 4:
        return BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
        )
    elif config.bits == 8:
        return BitsAndBytesConfig(
            load_in_8bit=True,
        )
    else:
        raise ValueError(f"Unsupported quantization bits: {config.bits}. Use 4 or 8.")
