"""
collect_player.py

CLI entrypoint for collecting interviews for a single player.

Example:
    python scripts/collect_player.py "Connor McDavid"
"""

import argparse
from hockey_interview_agent.collector import HockeyInterviewCollector


def main():
    parser = argparse.ArgumentParser(description="Collect interviews for a single player.")
    parser.add_argument("player_name")
    parser.add_argument("--youtube_top_n", type=int, default=5)
    args = parser.parse_args()

    collector = HockeyInterviewCollector()

    results = collector.collect_interviews(
        player_name=args.player_name,
        youtube_top_n=args.youtube_top_n,
    )

    path = collector.save_results(results)
    print(f"Raw collection saved to: {path}")


if __name__ == "__main__":
    main()
