import yaml
from pathlib import Path

# Load keywords from config.yaml
try:
    cfg = yaml.safe_load(Path("config.yaml").read_text())
    KEYWORDS = cfg.get("keywords", {})
except Exception:
    KEYWORDS = {
        "uncertain": ["maybe", "not sure", "unsure", "confused", "?"],
        "stressed":  ["angry", "frustrated", "upset", "stressed"],
        "positive": ["thank", "great", "happy", "awesome", "good"],
        "neutral": []
    }

def classify_signal(user_input: str) -> str:
    """
    Config‐driven keyword classifier.
    Falls back to 'neutral' if no keywords match.
    """
    text = user_input.lower()
    for signal, words in KEYWORDS.items():
        for w in words:
            if w in text:
                return signal
    return "neutral"
