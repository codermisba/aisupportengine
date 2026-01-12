import pandas as pd
from tagger import auto_tag_article

# Load KB
kb = pd.read_csv("data/knowledge_base.csv")

categories = []
tags_list = []

print("🔄 Auto-tagging knowledge base articles...")

for _, row in kb.iterrows():
    result = auto_tag_article(row["content"])
    categories.append(result["category"])
    tags_list.append(", ".join(result["tags"]))

kb["category"] = categories
kb["tags"] = tags_list

# Save enriched KB
kb.to_csv("data/knowledge_base_enriched.csv", index=False)

print("✅ Knowledge base enrichment complete")
