import os
import re


RULE_REPLACEMENTS = {
    r"\bbest\b": "highly skilled",
    r"\bworst\b": "least effective",
    r"\bunmatched\b": "strong",
    r"\bworld[- ]class\b": "high-quality",
    r"\brevolutioni[sz]e\b": "significantly improve",
    r"\bdominate\b": "compete effectively",
    r"\balways\b": "consistently",
    r"\bnever\b": "rarely",
    r"\bdefinitely\b": "likely",
    r"\bcertainly\b": "with confidence",
    r"\bcompletely\b": "substantially",
}


def _rule_based_rewrite(text: str) -> tuple[str, list[str]]:
    rewritten = text
    changes: list[str] = []

    for pattern, replacement in RULE_REPLACEMENTS.items():
        updated = re.sub(pattern, replacement, rewritten, flags=re.IGNORECASE)
        if updated != rewritten:
            changes.append(f"Replaced '{pattern}' with '{replacement}'.")
            rewritten = updated

    # Improve common passive constructs.
    passive_updates = [
        (r"\bwas implemented by\b", "the team implemented"),
        (r"\bwere delivered by\b", "the team delivered"),
        (r"\bwas led by me\b", "I led"),
    ]
    for pattern, replacement in passive_updates:
        updated = re.sub(pattern, replacement, rewritten, flags=re.IGNORECASE)
        if updated != rewritten:
            changes.append("Converted passive phrasing to active voice.")
            rewritten = updated

    # Add evidence prompt if no measurable data is present.
    if not re.search(r"\b\d+(\.\d+)?%?\b", rewritten):
        rewritten = rewritten.strip()
        if rewritten and not rewritten.endswith("."):
            rewritten += "."
        rewritten += " Add measurable outcomes (e.g., percentages, timelines, or impact metrics)."
        changes.append("Added measurable-outcomes prompt.")

    return rewritten, changes


def _llm_rewrite(text: str) -> tuple[str, list[str]] | None:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None

    try:
        from openai import OpenAI  # type: ignore
    except Exception:
        return None

    try:
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=os.getenv("OPENAI_REWRITE_MODEL", "gpt-4.1-mini"),
            input=(
                "Rewrite the following text professionally. Keep factual meaning unchanged, "
                "reduce exaggeration/absolute claims, improve credibility and clarity, and keep it concise.\n\n"
                f"Text:\n{text}"
            ),
            temperature=0.2,
        )
        rewritten = (response.output_text or "").strip()
        if not rewritten:
            return None
        return rewritten, ["LLM rewrite applied with professional-tone constraints."]
    except Exception:
        return None


def rewrite_professionally(text: str) -> dict[str, object]:
    mode = os.getenv("LIELENS_REWRITE_MODE", "rule").strip().lower()
    if mode == "llm":
        llm_result = _llm_rewrite(text)
        if llm_result:
            rewritten, changes = llm_result
            return {"rewritten_text": rewritten, "rewrite_method": "llm", "rewrite_changes": changes}

    rewritten, changes = _rule_based_rewrite(text)
    return {"rewritten_text": rewritten, "rewrite_method": "rule", "rewrite_changes": changes}
