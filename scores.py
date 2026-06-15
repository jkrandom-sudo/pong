"""Score persistence for Pong — save/load scores.json, top 10 ranking.

No curses imports — fully testable with plain pytest.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

SCORES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           'scores.json')


def _get_default_path() -> str:
    """Return the default path to scores.json."""
    return SCORES_FILE


def load_scores(path: Optional[str] = None) -> List[Dict]:
    """Load scores from JSON file.

    Returns an empty list if the file doesn't exist or is corrupted.
    """
    filepath = path or _get_default_path()
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        # Validate each entry
        validated = []
        for entry in data:
            if (isinstance(entry, dict) and
                    'date' in entry and
                    'winner' in entry and
                    'score1' in entry and
                    'score2' in entry and
                    'mode' in entry and
                    'speed_level' in entry):
                validated.append(entry)
        return validated
    except (json.JSONDecodeError, IOError, ValueError):
        return []


def save_scores(entry: Dict, path: Optional[str] = None) -> None:
    """Append a score entry to the JSON file.

    Entry format:
        {
            'date': '2024-01-01 12:00:00',
            'winner': 1,          # 1 or 2
            'score1': 11,
            'score2': 5,
            'mode': 'ai',         # 'ai' or '2p'
            'speed_level': 3
        }
    """
    filepath = path or _get_default_path()
    scores = load_scores(filepath)
    scores.append(entry)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(scores, f, ensure_ascii=False, indent=2)


def get_top10(scores: Optional[List[Dict]] = None,
              path: Optional[str] = None) -> List[Dict]:
    """Return top 10 scores sorted by winner's score descending.

    Accepts either a list of scores or a path to load from.
    """
    if scores is None:
        scores = load_scores(path)

    def winner_score(entry: Dict) -> int:
        if entry['winner'] == 1:
            return entry['score1']
        return entry['score2']

    sorted_scores = sorted(scores, key=winner_score, reverse=True)
    return sorted_scores[:10]


def format_score_entry(entry: Dict, language: str = 'zh') -> str:
    """Format a single score entry for display."""
    mode_str = {'ai': '单人AI', '2p': '双人对战'}.get(
        entry['mode'], entry['mode'])
    if language == 'en':
        mode_str = {'ai': 'vs AI', '2p': '2-Player'}.get(
            entry['mode'], entry['mode'])
    winner_str = f"P{entry['winner']}"
    score_str = f"{entry['score1']}:{entry['score2']}"
    return (f"{entry['date']} | {winner_str} | {score_str} | "
            f"{mode_str} | Lv.{entry['speed_level']}")


def make_score_entry(winner: int, score1: int, score2: int,
                     mode: str, speed_level: int) -> Dict:
    """Create a score entry dict with current timestamp."""
    return {
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'winner': winner,
        'score1': score1,
        'score2': score2,
        'mode': mode,
        'speed_level': speed_level,
    }
