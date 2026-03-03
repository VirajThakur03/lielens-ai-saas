import re
from collections import Counter

from textblob import TextBlob

SUPERLATIVES = {"best", "worst", "greatest", "most", "least", "always", "never"}
CERTAINTY_WORDS = {"definitely", "certainly", "undeniably", "clearly", "guaranteed"}
HEDGING_WORDS = {"maybe", "possibly", "perhaps", "likely", "might"}
ABSOLUTE_WORDS = {"always", "never", "must", "everyone", "nobody", "certainly", "definitely"}
BE_VERBS = {"was", "were", "is", "are", "been", "be"}


def extract_features(text: str) -> dict[str, float]:
    tokens = re.findall(r"\b[a-zA-Z']+\b", text.lower())
    token_count = max(len(tokens), 1)
    token_freq = Counter(tokens)

    superlative_ratio = sum(token_freq[w] for w in SUPERLATIVES) / token_count
    certainty_ratio = sum(token_freq[w] for w in CERTAINTY_WORDS) / token_count
    hedging_ratio = sum(token_freq[w] for w in HEDGING_WORDS) / token_count

    passive_matches = re.findall(r"\b(?:was|were|is|are|been|be)\s+\w+ed\b", text.lower())
    passive_voice_pct = len(passive_matches) / max(len(re.findall(r"[.!?]+", text)), 1)

    blob = TextBlob(text)
    sentiment_polarity = abs(blob.sentiment.polarity)

    # Avoid TextBlob sentence tokenization dependency on NLTK punkt corpora.
    raw_sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    sentence_polarities = [abs(TextBlob(sentence).sentiment.polarity) for sentence in raw_sentences]
    emotional_volatility = 0.0
    if sentence_polarities:
        emotional_volatility = max(sentence_polarities) - min(sentence_polarities)

    quantification_presence = 1.0 if re.search(r"\b\d+(\.\d+)?%?\b", text) else 0.0

    return {
        "superlative_ratio": round(superlative_ratio, 4),
        "passive_voice_pct": round(passive_voice_pct, 4),
        "sentiment_intensity": round(sentiment_polarity, 4),
        "emotional_volatility": round(emotional_volatility, 4),
        "certainty_ratio": round(certainty_ratio, 4),
        "hedging_ratio": round(hedging_ratio, 4),
        "quantification_presence": round(quantification_presence, 4),
    }


def build_token_annotations(text: str) -> list[dict[str, str | float]]:
    chunks = re.findall(r"\w+|\s+|[^\w\s]", text)
    annotations: list[dict[str, str | float]] = []

    # First pass: lexical features and sentiment spikes.
    for chunk in chunks:
        if chunk.isspace():
            annotations.append({"text": chunk, "risk_type": "none", "intensity": 0.0, "reason": ""})
            continue

        if not re.match(r"^\w+$", chunk):
            annotations.append({"text": chunk, "risk_type": "none", "intensity": 0.0, "reason": ""})
            continue

        lower = chunk.lower()
        risk_type = "none"
        intensity = 0.0
        reason = ""

        if lower in SUPERLATIVES:
            risk_type = "superlative"
            intensity = 0.9
            reason = "Superlative wording may increase exaggeration risk."
        elif lower in CERTAINTY_WORDS or lower in ABSOLUTE_WORDS:
            risk_type = "absolute_claim"
            intensity = 0.8
            reason = "High-certainty phrase increases confidence and exaggeration signals."
        elif lower in HEDGING_WORDS:
            risk_type = "hedging"
            intensity = 0.35
            reason = "Hedging can reduce overclaiming but may weaken confidence."
        else:
            local_sentiment = abs(TextBlob(chunk).sentiment.polarity)
            if local_sentiment >= 0.6:
                risk_type = "emotional_spike"
                intensity = min(0.95, round(0.5 + local_sentiment / 2, 2))
                reason = "Emotionally intense word contributes to tone volatility."

        annotations.append(
            {
                "text": chunk,
                "risk_type": risk_type,
                "intensity": float(intensity),
                "reason": reason,
            }
        )

    # Second pass: passive voice pattern "be + verb-ed".
    word_indices = [idx for idx, item in enumerate(annotations) if re.match(r"^\w+$", str(item["text"]))]
    for i in range(len(word_indices) - 1):
        first_idx = word_indices[i]
        second_idx = word_indices[i + 1]
        first = str(annotations[first_idx]["text"]).lower()
        second = str(annotations[second_idx]["text"]).lower()
        if first in BE_VERBS and second.endswith("ed"):
            annotations[second_idx] = {
                "text": annotations[second_idx]["text"],
                "risk_type": "passive_voice",
                "intensity": 0.6,
                "reason": "Passive voice can reduce clarity and accountability.",
            }
    return annotations
