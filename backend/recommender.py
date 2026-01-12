import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class KnowledgeRecommender:
    def __init__(self, kb_path="data/knowledge_base_enriched.csv"):
        self.kb = pd.read_csv(kb_path)
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.article_vectors = self.vectorizer.fit_transform(
            self.kb["content"].fillna("")
        )

    def recommend(self, ticket_text: str, top_k: int = 3):
        ticket_vec = self.vectorizer.transform([ticket_text])
        similarities = cosine_similarity(ticket_vec, self.article_vectors)[0]

        top_indices = similarities.argsort()[::-1][:top_k]

        results = []

        for idx, row in self.kb.iterrows():
            similarity = similarities[idx]

        results.append({
            "article_id": int(row["id"]),
            "title": row["title"],
            "category": row.get("category", "General"),
            "tags": row.get("tags", ""),
            "score": float(similarity)
        })

        results = sorted(results, key=lambda x: x["score"], reverse=True)
        results = results[:top_k]

       
        return results
