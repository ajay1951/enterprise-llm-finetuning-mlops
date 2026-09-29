import argparse
import sys
from forgellm.training.config import load_config
from forgellm.training.trainer import ForgeTrainer


def main():
    parser = argparse.ArgumentParser(description="Run ForgeLLM Training")
    parser.add_argument(
        "--config", type=str, required=True, help="Path to training config YAML"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="data/processed/hf_dataset",
        help="Path to processed dataset",
    )
    args = parser.parse_args()

    print("ForgeLLM Training Script")
    print("-" * 28)

    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"ERROR: Failed to load configuration: {e}")
        sys.exit(1)

    try:
        trainer = ForgeTrainer(config, args.dataset)
        trainer.train()
    except Exception as e:
        print(f"\nTraining Failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
