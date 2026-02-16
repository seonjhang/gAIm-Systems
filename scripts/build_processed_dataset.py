"""
build_processed_dataset.py

Rebuild structured dataset from raw JSON files.

Example:
    python scripts/build_processed_dataset.py
"""

import argparse
from datetime import datetime
from pathlib import Path

from hockey_interview_agent.export.structured_exporter import StructuredExporter


def main():
    parser = argparse.ArgumentParser(description="Build structured dataset from raw artifacts.")
    parser.add_argument("--use_player_speech", action="store_true", default=True)
    args = parser.parse_args()

    exporter = StructuredExporter()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = Path("data/processed") / f"dataset_{timestamp}.tsv"

    created = exporter.export_tsv(
        output_path=output,
        use_player_speech=args.use_player_speech,
    )

    print(f"Structured dataset created at: {created}")


if __name__ == "__main__":
    main()
