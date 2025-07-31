def classify_signal(user_input: str) -> str:
    """Basic keyword-based signal classifier."""
    text = user_input.lower()
    if any(word in text for word in ["maybe", "not sure", "unsure", "confused", "?"]):
        return "uncertain"
    elif any(word in text for word in ["angry", "frustrated", "upset", "stressed"]):
        return "stressed"
    elif any(word in text for word in ["thank", "great", "happy", "awesome", "good"]):
        return "positive"
    else:
        return "neutral"
