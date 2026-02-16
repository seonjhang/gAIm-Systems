"""
structured_exporter.py

Responsible for converting raw JSON artifacts into
structured datasets ready for NLP/ML usage.

This module does NOT collect data.
It only transforms existing raw data into processed format.
"""

from pathlib import Path
import json


class StructuredExporter:
    """
    Converts transcript or player_speech JSON files
    into a clean TSV dataset.

    Output Format:
        player_name <TAB> text
    """

    def __init__(self):
        self.transcript_dir = Path("data/raw/transcript")
        self.player_speech_dir = Path("data/raw/player_speech")
        self.processed_dir = Path("data/processed")
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def export_tsv(self, output_path: Path, use_player_speech: bool = True) -> Path:
        """
        Build TSV dataset from raw JSON files.

        Parameters
        ----------
        output_path : Path
            Destination file.
        use_player_speech : bool
            If True, use GPT-filtered player speech.
            If False, use full transcript text.

        Returns
        -------
        Path
            Path of created TSV file.
        """

        rows = []

        if use_player_speech and self.player_speech_dir.exists():
            for file in self.player_speech_dir.glob("*_player_speech.json"):
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                rows.append({
                    "player_name": data["player_name"],
                    "text": data["player_speech_text"],
                })

        else:
            for file in self.transcript_dir.glob("*_transcript.json"):
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                rows.append({
                    "player_name": data.get("player_name", "UNKNOWN"),
                    "text": data.get("full_text", ""),
                })

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("player_name\ttext\n")
            for r in rows:
                clean_text = " ".join(r["text"].replace("\n", " ").split())
                f.write(f"{r['player_name']}\t{clean_text}\n")

        return output_path
