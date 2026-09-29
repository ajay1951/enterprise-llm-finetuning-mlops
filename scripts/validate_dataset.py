import argparse
import sys

from forgellm.dataset.validator import DatasetValidator


def main():
    parser = argparse.ArgumentParser(description="Validate ForgeLLM dataset")
    parser.add_argument(
        "--input", type=str, required=True, help="Path to JSONL dataset"
    )
    args = parser.parse_args()

    validator = DatasetValidator()
    result = validator.validate_file(args.input)

    print(result)

    if result.status == "FAILED":
        sys.exit(1)


if __name__ == "__main__":
    main()
