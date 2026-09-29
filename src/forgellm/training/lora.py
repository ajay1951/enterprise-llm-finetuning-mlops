from peft import LoraConfig as PeftLoraConfig

from forgellm.training.config import LoraConfig


def get_lora_config(config: LoraConfig) -> PeftLoraConfig:
    print("\nLoRA Configuration")
    print("-" * 24)
    print(f"Rank:       {config.r}")
    print(f"Alpha:      {config.alpha}")
    print(f"Dropout:    {config.dropout}")

    # In Phase 1, we let PEFT try to auto-detect target modules for common architectures
    # For Qwen, standard target modules include q_proj, k_proj, v_proj, o_proj, up_proj, gate_proj, down_proj
    target_modules = [
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
    ]

    print("\nTarget modules:")
    for mod in target_modules:
        print(mod)

    return PeftLoraConfig(
        r=config.r,
        lora_alpha=config.alpha,
        lora_dropout=config.dropout,
        target_modules=target_modules,
        bias="none",
        task_type="CAUSAL_LM",
    )
