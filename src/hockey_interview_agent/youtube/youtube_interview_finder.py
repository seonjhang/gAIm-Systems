#!/usr/bin/env python3
"""
YouTube Interview Finder
Given a player name, return the most relevant YouTube interview.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv

from url_validator import HockeyInterviewValidator
try:
    import pandas as pd
except Exception:
    pd = None  # We'll handle missing pandas gracefully

load_dotenv()

logger = logging.getLogger(__name__)


class YouTubeInterviewFinder:
    """Finds the most relevant YouTube interview for a hockey player"""

    SEARCH_ENDPOINT = "https://www.googleapis.com/youtube/v3/search"
    VIDEOS_ENDPOINT = "https://www.googleapis.com/youtube/v3/videos"

    def __init__(self, api_key: Optional[str] = None, strict: bool = False):
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY")
        if not self.api_key:
            raise ValueError("YOUTUBE_API_KEY is required. Set it in your environment or .env file.")

        self.session = requests.Session()
        self.validator = HockeyInterviewValidator()
        self._draft_cache: Dict[str, Dict[str, Any]] = {}
        self.strict = strict

    def find_best_interview(self, player_name: str) -> Optional[Dict[str, Any]]:
        """
        Search YouTube for interviews and return the best match.

        Returns dict with: title, url, channel, publishedAt, videoId, score.
        """
        candidates = self._search_youtube(player_name)
        if not candidates:
            return None

        ranked = self._validate_and_rank(player_name, candidates)
        if not ranked:
            return None

        top = ranked[0]
        return {
            "title": top["title"],
            "url": top["url"],
            "channel": top["channel"],
            "publishedAt": top.get("publishedAt"),
            "videoId": top["videoId"],
            "score": top.get("score", 0),
        }

    def find_top_interviews(self, player_name: str, top_n: int = 5, draft_year: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Return the top N most relevant interviews, preferring pre-draft content if draft_year is provided.
        """
        candidates = self._search_youtube(player_name, max_results=50, draft_year=draft_year)
        # If draft_year not explicitly provided, try to resolve from Draft.xlsx
        cutoff_dt = None
        if draft_year is None:
            cutoff_dt = self._lookup_draft_cutoff(player_name)
        ranked = self._validate_and_rank(player_name, candidates, draft_year=draft_year, draft_cutoff_dt=cutoff_dt)
        return [
            {
                "title": r["title"],
                "url": r["url"],
                "channel": r["channel"],
                "publishedAt": r.get("publishedAt"),
                "videoId": r["videoId"],
                "score": r.get("score", 0),
            }
            for r in ranked[:max(1, top_n)]
        ]

    def _search_youtube(self, player_name: str, max_results: int = 15, draft_year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Query YouTube Data API for likely interview videos."""
        year_suffix = f" {draft_year}" if draft_year else ""
        quoted = f'"{player_name}"'
        queries = [
            f"{quoted} interview nhl{year_suffix}",
            f"{quoted} media availability{year_suffix}",
            f"{quoted} press conference nhl{year_suffix}",
            f"{quoted} post-game interview{year_suffix}",
            f"{quoted} draft interview",
            f"{quoted} combine interview",
            f"{quoted} prospect interview",
            f"{quoted} draft combine scrum",
        ]

        items: List[Dict[str, Any]] = []
        for q in queries:
            params = {
                "part": "snippet",
                "q": q,
                "type": "video",
                "maxResults": 10,
                "order": "relevance",
                "safeSearch": "none",
                "key": self.api_key,
            }
            try:
                resp = self.session.get(self.SEARCH_ENDPOINT, params=params, timeout=15)
                if resp.status_code != 200:
                    error_data = resp.json() if resp.content else {}
                    logger.error(f"YouTube API error (status {resp.status_code}): {error_data.get('error', {}).get('message', 'Unknown error')}")
                    if resp.status_code == 403:
                        logger.error("API key may be invalid or quota exceeded. Check YOUTUBE_API_KEY.")
                    continue
                data = resp.json()
                if 'error' in data:
                    logger.error(f"YouTube API error: {data['error'].get('message', 'Unknown error')}")
                    continue
            except Exception as e:
                logger.error(f"Exception during YouTube search: {type(e).__name__}: {e}")
                continue

            for it in data.get("items", []):
                vid = it.get("id", {}).get("videoId")
                sn = it.get("snippet", {})
                if not vid:
                    continue
                items.append({
                    "videoId": vid,
                    "title": sn.get("title", ""),
                    "channel": sn.get("channelTitle", ""),
                    "publishedAt": sn.get("publishedAt"),
                })

        # De-duplicate by videoId
        seen = set()
        unique: List[Dict[str, Any]] = []
        for it in items:
            if it["videoId"] in seen:
                continue
            seen.add(it["videoId"])
            unique.append(it)

        return unique[:max_results]

    def _fetch_video_details(self, video_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Fetch additional details like description and duration to help validation."""
        if not video_ids:
            return {}
        params = {
            "part": "snippet,contentDetails,statistics",
            "id": ",".join(video_ids),
            "key": self.api_key,
            "maxWidth": 50,
        }
        try:
            resp = self.session.get(self.VIDEOS_ENDPOINT, params=params, timeout=15)
            if resp.status_code != 200:
                return {}
            data = resp.json()
        except Exception:
            return {}
        out: Dict[str, Dict[str, Any]] = {}
        for it in data.get("items", []):
            vid = it.get("id")
            sn = it.get("snippet", {})
            out[vid] = {
                "description": sn.get("description", ""),
                "categoryId": sn.get("categoryId"),
                "liveBroadcastContent": sn.get("liveBroadcastContent"),
                "contentDetails": it.get("contentDetails", {}),
                "statistics": it.get("statistics", {}),
            }
        return out

    def _validate_and_rank(self, player_name: str, candidates: List[Dict[str, Any]], draft_year: Optional[int] = None, draft_cutoff_dt: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Apply validation, AI-generated filtering, and ranking heuristics."""
        ai_terms = [
            "ai-generated", "ai generated", "artificial intelligence", "deepfake", "voice clone",
            "voice-clone", "tts", "text-to-speech", "11labs", "not real", "fake interview",
        ]
        non_interview_terms = [
            "highlight", "goal", "goals", "compilation", "mix", "edit", "edits", "shorts",
            "mic'd up", "micd up", "trailer", "teaser", "reaction",
        ]
        interview_terms = [
            "interview", "media availability", "press conference", "availability", "scrum",
            "post-game", "post game", "pre-game", "pre game", "q&a", "qa",
        ]
        official_channel_hints = [
            "nhl", "tsn", "sportsnet", "espn", "cbc", "rogers place", "oilers", "maple leafs",
            "penguins", "blackhawks", "canadiens", "rangers", "bruins", "lightning", "avalanche",
            "red wings", "kings", "ducks", "flames", "canucks", "jets", "wild", "predators",
            "capitals", "devils", "islanders", "sabres", "senators", "sharks", "stars",
        ]

        # Fetch details for better filtering
        details = self._fetch_video_details([c["videoId"] for c in candidates])

        ranked: List[Dict[str, Any]] = []
        name_lower = player_name.lower()
        first_last = [p for p in player_name.lower().split() if p]
        first = first_last[0] if first_last else ""
        last = first_last[-1] if first_last else ""
        for c in candidates:
            url = f"https://www.youtube.com/watch?v={c['videoId']}"
            validation = self.validator.validate_url(url, player_name)
            score = validation.get("score", 0)

            title = c["title"] or ""
            channel = c["channel"] or ""
            title_lower = title.lower()
            channel_lower = channel.lower()
            published_at = c.get("publishedAt") or ""

            det = details.get(c["videoId"], {})
            desc_lower = (det.get("description") or "").lower()

            # Strict name presence: require both first and last in title (or description if not in title)
            has_full_name_in_title = first in title_lower and last in title_lower
            has_full_name_any = has_full_name_in_title or (first in desc_lower and last in desc_lower)
            if self.strict and not has_full_name_in_title:
                # drop if strict and title doesn't have the full name
                continue
            if not has_full_name_any:
                # soft drop unless channel is official and mentions player
                if first not in channel_lower and last not in channel_lower:
                    continue

            # Must look like an interview
            looks_like_interview = any(t in title_lower or t in desc_lower for t in interview_terms)
            if not looks_like_interview:
                # soft filter: big penalty instead of removal
                score -= 2

            # Player match
            if name_lower in title_lower or name_lower in desc_lower:
                score += 2
            else:
                score -= 1

            # Official channel hint
            if any(h in channel_lower for h in official_channel_hints):
                score += 2

            # Penalize AI-generated indicators
            if any(t in title_lower or t in desc_lower for t in ai_terms):
                score -= 4

            # Penalize non-interview content
            if any(t in title_lower for t in non_interview_terms):
                score -= 2

            # Penalize generic/top-prospect lists and videos centered on someone else
            generic_penalty_terms = [
                "top prospects", "meeting", "panel", "roundtable", "mic'd up", "micd up",
                "postgame availability", "availability: ", "media availability: ",
            ]
            if any(t in title_lower for t in generic_penalty_terms):
                score -= 1

            # If title indicates interview of another named person, exclude
            # Simple heuristic: patterns like "Interview: <Other Name>" or "<Other Name> Interview"
            if "interview" in title_lower and not has_full_name_in_title:
                continue

            # Draft constraints
            # 1) Explicit draft_year provided: enforce published year <= draft_year
            if draft_year and published_at:
                try:
                    year = int(published_at[:4])
                    if year > draft_year:
                        # hard filter post-draft when required
                        continue
                    else:
                        score += 2
                except Exception:
                    pass

            # 2) If we looked up draft cutoff datetime from file, ensure publishedAt <= cutoff
            if draft_cutoff_dt and published_at:
                try:
                    pub_dt = datetime.fromisoformat(published_at.replace("Z", "+00:00")).replace(tzinfo=None)
                    if pub_dt > draft_cutoff_dt:
                        # exclude post-draft videos
                        continue
                    else:
                        score += 2
                except Exception:
                    pass

            # If no explicit cutoff, a small boost for draft/combine/prospect indicators
            if not draft_year and not draft_cutoff_dt:
                if any(t in title_lower for t in ["draft", "combine", "prospect"]):
                    score += 1

            ranked.append({
                **c,
                "url": url,
                "score": score,
                "validated": validation.get("valid", False),
            })

        # Sort by: validated, score, recentness
        ranked.sort(key=lambda x: (
            1 if x.get("validated", False) else 0,
            x.get("score", 0),
            x.get("publishedAt", ""),
        ), reverse=True)

        # Final filter: keep items with score >= 0 to widen results
        return [r for r in ranked if r.get("score", 0) >= 0]

    def _lookup_draft_cutoff(self, player_name: str) -> Optional[datetime]:
        """
        Read data/Draft.xlsx and compute a draft cutoff datetime for the player.
        Heuristic: NHL draft typically late June. Use June 25 of draft Year,
        and subtract small offset by Round (earlier rounds earlier):
        cutoff = June 25 + (round-1) hours. Then use that datetime as limit.
        """
        if player_name in self._draft_cache:
            info = self._draft_cache[player_name]
            if info:
                return info.get("cutoff")
            return None

        draft_path = os.path.join(os.path.dirname(__file__), "data", "Draft.xlsx")
        # Fallback to project root path in case __file__ different
        if not os.path.exists(draft_path):
            draft_path = os.path.join(os.getcwd(), "data", "Draft.xlsx")

        if not os.path.exists(draft_path) or pd is None:
            self._draft_cache[player_name] = None
            return None

        try:
            df = pd.read_excel(draft_path)
        except Exception:
            self._draft_cache[player_name] = None
            return None

        # Normalize columns and player name
        cols = {c.lower(): c for c in df.columns}
        player_col = cols.get("player") or cols.get("name")
        year_col = cols.get("year")
        round_col = cols.get("round")
        if not player_col or not year_col:
            self._draft_cache[player_name] = None
            return None

        # Case-insensitive match on player
        mask = df[player_col].astype(str).str.lower() == player_name.lower()
        row = df[mask].head(1)
        if row.empty:
            self._draft_cache[player_name] = None
            return None

        try:
            year = int(row.iloc[0][year_col])
        except Exception:
            self._draft_cache[player_name] = None
            return None

        try:
            rnd = int(row.iloc[0][round_col]) if round_col else 1
        except Exception:
            rnd = 1

        # Draft heuristic date: June 25 of that year, with round offset (hours)
        base_dt = datetime(year, 6, 25, 12, 0, 0)
        cutoff = base_dt + timedelta(hours=(rnd - 1))

        self._draft_cache[player_name] = {"cutoff": cutoff, "year": year, "round": rnd}
        return cutoff


def main():
    import sys
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="Find top YouTube interviews for a hockey player")
    parser.add_argument("player_name", nargs="+", help="Player name, e.g., Connor McDavid")
    parser.add_argument("--top", type=int, default=5, help="Number of results (3-5 recommended)")
    parser.add_argument("--draft-year", type=int, default=None, help="Prefer videos on or before this year")
    parser.add_argument("--strict", action="store_true", help="Require player's full name in the title")
    args = parser.parse_args()

    player_name = " ".join(args.player_name)
    finder = YouTubeInterviewFinder(strict=bool(args.strict))

    results = finder.find_top_interviews(player_name, top_n=args.top, draft_year=args.draft_year)
    if not results:
        print("No interviews found.")
        return

    print(f"Top {len(results)} interviews for {player_name}:")
    for i, r in enumerate(results, 1):
        print(f"\n{i}. {r['title']}")
        print(f"   Channel  : {r['channel']}")
        print(f"   Published: {r.get('publishedAt')}")
        print(f"   Score    : {r.get('score')}")
        print(f"   URL      : {r['url']}")


if __name__ == "__main__":
    main()