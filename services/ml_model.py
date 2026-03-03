import math

try:
    from sklearn.linear_model import LogisticRegression
except ImportError:  # pragma: no cover
    LogisticRegression = None


FEATURE_KEYS = [
    "superlative_ratio",
    "passive_voice_pct",
    "sentiment_intensity",
    "emotional_volatility",
    "certainty_ratio",
    "hedging_ratio",
    "quantification_presence",
]


class DeceptionModel:
    def __init__(self):
        self._model = None
        if LogisticRegression:
            self._model = LogisticRegression(max_iter=500)
            self._train()

    def _train(self):
        samples = [
            [0.02, 0.1, 0.1, 0.1, 0.02, 0.1, 1.0],
            [0.25, 0.4, 0.6, 0.5, 0.2, 0.01, 0.0],
            [0.01, 0.05, 0.08, 0.03, 0.01, 0.2, 1.0],
            [0.18, 0.35, 0.5, 0.55, 0.28, 0.01, 0.0],
            [0.03, 0.07, 0.09, 0.08, 0.03, 0.15, 1.0],
            [0.22, 0.5, 0.7, 0.6, 0.3, 0.0, 0.0],
        ]
        labels = [0, 1, 0, 1, 0, 1]
        self._model.fit(samples, labels)

    def predict(self, features: dict[str, float]) -> float:
        vector = [features.get(key, 0.0) for key in FEATURE_KEYS]
        if self._model:
            return float(self._model.predict_proba([vector])[0][1])

        # Deterministic fallback when sklearn is unavailable.
        weighted = (
            vector[0] * 3.0
            + vector[2] * 2.0
            + vector[3] * 1.5
            + vector[4] * 1.5
            - vector[5] * 1.2
            - vector[6] * 0.5
        )
        return 1.0 / (1.0 + math.exp(-weighted))


_MODEL = DeceptionModel()


def score_probability(features: dict[str, float]) -> float:
    return round(_MODEL.predict(features), 4)
