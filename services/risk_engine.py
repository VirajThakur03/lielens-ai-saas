def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def compute_risk(features: dict[str, float], ml_probability: float) -> dict[str, float]:
    superlative_component = features["superlative_ratio"] * 0.25
    sentiment_component = features["sentiment_intensity"] * 0.20
    certainty_component = features["certainty_ratio"] * 0.15
    ml_component = ml_probability * 0.40

    final_risk_score = superlative_component + sentiment_component + certainty_component + ml_component
    emotional_intensity = clamp(
        (features["sentiment_intensity"] + features["emotional_volatility"]) / 2
    )
    exaggeration_score = clamp(
        (features["superlative_ratio"] * 0.7) + (features["certainty_ratio"] * 0.3)
    )
    confidence_score = clamp(ml_probability)
    credibility_score = clamp(1.0 - final_risk_score)
    denominator = max(final_risk_score, 0.0001)

    contribution_breakdown = {
        "superlative_influence_pct": round((superlative_component / denominator) * 100, 2),
        "certainty_influence_pct": round((certainty_component / denominator) * 100, 2),
        "sentiment_influence_pct": round((sentiment_component / denominator) * 100, 2),
        "ml_influence_pct": round((ml_component / denominator) * 100, 2),
    }

    return {
        "confidence_score": round(confidence_score, 4),
        "exaggeration_score": round(exaggeration_score, 4),
        "credibility_score": round(credibility_score, 4),
        "emotional_intensity": round(emotional_intensity, 4),
        "final_risk_score": round(clamp(final_risk_score), 4),
        "contribution_breakdown": contribution_breakdown,
    }
