import json
import re
from llm import query_llm


def extract_json(text: str) -> dict:
    """
    Extracts first JSON object found in text.
    """
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None

    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return None


def auto_tag_article(article_text: str) -> dict:
    prompt = f"""
You are an AI that classifies customer support knowledge articles.

Return ONLY valid JSON.
Do NOT include schema, titles, or extra fields.

Required fields:
- category (string)
- tags (array of strings)

Article:
{article_text}
"""

    response = query_llm(prompt)
    parsed = extract_json(response)

    if not parsed:
        return {"category": "Uncategorized", "tags": []}

    category = parsed.get("category", "Uncategorized")
    tags = parsed.get("tags", [])

    # Ensure tags are clean strings
    if isinstance(tags, list):
        tags = [str(t).strip() for t in tags][:5]
    else:
        tags = []

    return {
        "category": category,
        "tags": tags
    }
