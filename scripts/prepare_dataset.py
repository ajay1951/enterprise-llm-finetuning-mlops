import argparse
import os
import sys

from forgellm.dataset.cleaner import DatasetCleaner
from forgellm.dataset.formatter import DatasetFormatter
from forgellm.dataset.splitter import DatasetSplitter
from forgellm.training.config import load_config


def main():
    parser = argparse.ArgumentParser(description="Prepare ForgeLLM dataset")
    parser.add_argument(
        "--config", type=str, required=True, help="Path to training config YAML"
    )
    args = parser.parse_args()

    print("ForgeLLM Dataset Preparation")
    print("-" * 28)

    try:
        config = load_config(args.config)
        print(f"Loaded config from {args.config}")
    except Exception as e:
        print(f"ERROR: Failed to load configuration: {e}")
        sys.exit(1)

    raw_path = config.dataset.train_file
    cleaned_path = "data/processed/cleaned.jsonl"

    # 1. Clean dataset
    print(f"Cleaning dataset: {raw_path}")
    cleaner = DatasetCleaner()
    try:
        report = cleaner.clean(raw_path, cleaned_path)
        print(f"Clean report: {report}")
    except Exception as e:
        print(f"ERROR: Failed to clean dataset: {e}")
        sys.exit(1)

    # 2. Format to Hugging Face Dataset
    print("Formatting dataset...")
    formatter = DatasetFormatter()
    try:
        dataset = formatter.format_dataset(cleaned_path)
        print(f"Formatted dataset with {len(dataset)} examples.")
    except Exception as e:
        print(f"ERROR: Failed to format dataset: {e}")
        sys.exit(1)

    # 3. Split dataset
    print(f"Splitting dataset (validation split: {config.dataset.validation_split})...")
    splitter = DatasetSplitter(
        validation_split=config.dataset.validation_split, seed=config.dataset.seed
    )
    split_dataset = splitter.split(dataset)

    # 4. Save processed split
    output_dir = "data/processed/hf_dataset"
    print(f"Saving dataset to {output_dir}")
    split_dataset.save_to_disk(output_dir)
    print("Status: PASSED")


if __name__ == "__main__":
    main()
