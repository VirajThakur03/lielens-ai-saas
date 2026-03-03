def generate_summary_and_suggestions(
    risk_scores: dict[str, float], features: dict[str, float]
) -> tuple[str, list[str]]:
    risk = risk_scores["final_risk_score"]
    credibility = risk_scores["credibility_score"]

    if risk >= 0.7:
        summary = "High risk profile. Language appears potentially exaggerated and emotionally volatile."
    elif risk >= 0.4:
        summary = "Moderate risk profile. Some indicators suggest potential credibility concerns."
    else:
        summary = "Low risk profile. Text appears relatively grounded and consistent."

    suggestions: list[str] = []
    if features["superlative_ratio"] > 0.05:
        suggestions.append("Reduce superlative claims and use evidence-backed phrasing.")
    if features["certainty_ratio"] > 0.04:
        suggestions.append("Replace absolute certainty terms with measurable facts.")
    if features["hedging_ratio"] < 0.005:
        suggestions.append("Add nuanced qualifiers where appropriate to avoid overclaiming.")
    if features["quantification_presence"] == 0.0:
        suggestions.append("Include numbers or sources to strengthen objective credibility.")
    if credibility < 0.5:
        suggestions.append("Balance emotional language with verifiable statements.")

    if not suggestions:
        suggestions.append("Maintain this style and keep citing concrete evidence.")
    return summary, suggestions
