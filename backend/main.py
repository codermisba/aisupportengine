import asyncio
from http.client import HTTPException
from fastapi import FastAPI
from pydantic import BaseModel
import os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from llm import kb_engine

from slack_notifier import send_to_slack

# from slack_notifier import send_to_slack   # enable later

# ======================================================
# PATH SETUP
# ======================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
KB_PATH = os.path.join(DATA_DIR, "knowledge_base_enriched.csv")
USAGE_PATH = os.path.join(DATA_DIR, "kb_usage_store.csv")

os.makedirs(DATA_DIR, exist_ok=True)

# ======================================================
# FASTAPI APP
# ======================================================
app = FastAPI(
    title="AI Knowledge Engine",
    description="Smart Support Ticket Resolution API",
    version="1.0"
)

# ======================================================
# GLOBAL STATE (VERY IMPORTANT)
# ======================================================
kb_df = None
tfidf_vectorizer = None
kb_tfidf_matrix = None
usage_df = None   # <-- THIS WAS MISSING BEFORE

# ======================================================
# LOAD KNOWLEDGE BASE
# ======================================================
def load_knowledge_base():
    if not os.path.exists(KB_PATH):
        raise FileNotFoundError(f"KB not found at {KB_PATH}")

    df = pd.read_csv(KB_PATH)

    if "content" not in df.columns:
        raise ValueError("KB must contain a 'content' column")

    return df

# ======================================================
# LOAD / INIT USAGE METRICS
# ======================================================
def load_usage_metrics():
    if os.path.exists(USAGE_PATH):
        df = pd.read_csv(USAGE_PATH)

        # Ensure schema (handles old/broken CSVs)
        for col in ["article_id", "usage_count", "avg_score"]:
            if col not in df.columns:
                df[col] = 0

        return df

    # Fresh file
    return pd.DataFrame(
        columns=["article_id", "usage_count", "avg_score"]
    )

# ======================================================
# UPDATE USAGE METRICS
# ======================================================
def update_usage_metrics(article_id: str, score: float):
    global usage_df

    if article_id in usage_df["article_id"].values:
        idx = usage_df.index[usage_df["article_id"] == article_id][0]

        prev_count = int(usage_df.at[idx, "usage_count"])
        prev_avg = float(usage_df.at[idx, "avg_score"])

        new_count = prev_count + 1
        new_avg = ((prev_avg * prev_count) + score) / new_count

        usage_df.at[idx, "usage_count"] = new_count
        usage_df.at[idx, "avg_score"] = round(new_avg, 3)

    else:
        usage_df.loc[len(usage_df)] = {
            "article_id": article_id,
            "usage_count": 1,
            "avg_score": round(score, 3)
        }

    # Persist to disk
    usage_df.to_csv(USAGE_PATH, index=False)

# ======================================================
# STARTUP EVENT
# ======================================================
async def load_kb_async():
    global kb_df, tfidf_vectorizer, kb_tfidf_matrix, usage_df
    print("🔄 Loading Knowledge Base...")
    kb_df = load_knowledge_base()

    tfidf_vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_features=5000
    )
    kb_tfidf_matrix = tfidf_vectorizer.fit_transform(
        kb_df["content"].fillna("").tolist()
    )

    usage_df = load_usage_metrics()
    print("✅ KB Loaded & Vectorized")
    print("✅ Usage Metrics Loaded")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(load_kb_async())
    print("🚀 FastAPI started, KB loading in background...")
# ======================================================
# REQUEST MODEL
# ======================================================
class TicketRequest(BaseModel):
    ticket_text: str
    top_k: int = 3

# ======================================================
# SIMILARITY
# ======================================================
def compute_similarity(ticket_text: str):
    ticket_vec = tfidf_vectorizer.transform([ticket_text])
    return cosine_similarity(ticket_vec, kb_tfidf_matrix)[0]

# ======================================================
# RECOMMENDATION ENDPOINT
# ======================================================


@app.post("/recommend")
def recommend(payload: TicketRequest):
    if kb_df is None or kb_df.empty:
        raise HTTPException(status_code=500, detail="Knowledge base not loaded")

    # ---------------- Similarity ----------------
    scores = compute_similarity(payload.ticket_text)

    results = []
    for i, row in kb_df.iterrows():
        results.append({
            "article_id": str(row["article_id"]),
            "title": str(row["title"]),
            "category": str(row.get("category", "General")),
            "tags": str(row.get("tags", "")),
            "score": float(scores[i])
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    top_results = results[:payload.top_k]

    # ---------------- Usage Tracking ----------------
    if top_results:
        update_usage_metrics(
            top_results[0]["article_id"],
            top_results[0]["score"]
        )

        if top_results[0]["score"] < 0.3:
            send_to_slack(payload.ticket_text, top_results[0])

    # ---------------- LLM Human Response ----------------
    try:
        ai_response = kb_engine.generate_solution(payload.ticket_text)
    except Exception as e:
        ai_response = (
            "I could not find an exact match in the knowledge base, "
            "but based on experience, please try restarting the service "
            "and checking system logs."
        )

    # ---------------- Confidence Estimation ----------------
    confidence = "low"
    if top_results:
        if top_results[0]["score"] >= 0.7:
            confidence = "high"
        elif top_results[0]["score"] >= 0.4:
            confidence = "medium"

    return {
        "recommendations": top_results,
        "ai_response": ai_response,
        "confidence": confidence
    }

# ======================================================
# REPORTING MODULE (FEATURE 4)
# ======================================================
@app.get("/report/kb-health")
def kb_health():
    if usage_df.empty:
        return {"message": "No usage data yet"}

    return {
        "total_articles": len(kb_df),
        "actively_used_articles": len(usage_df),
        "unused_articles": len(kb_df) - len(usage_df),
        "average_relevance_score": round(usage_df["avg_score"].mean(), 3)
    }

@app.get("/report/article-performance")
def article_performance():
    global usage_df

    if usage_df is None or usage_df.empty:
        return []

    if "usage_count" not in usage_df.columns:
        raise HTTPException(
            status_code=500,
            detail="Column 'usage_count' missing in usage_df"
        )

    # Work on a COPY to avoid pandas side-effects
    df = usage_df.copy()

    # Ensure numeric
    df["usage_count"] = (
        pd.to_numeric(df["usage_count"], errors="coerce")
        .fillna(0)
        .astype(int)
    )

    # Convert everything to native Python types
    result = []
    for row in df.sort_values(by="usage_count", ascending=False).to_dict(orient="records"):
        clean_row = {}
        for k, v in row.items():
            if pd.isna(v):
                clean_row[k] = None
            else:
                clean_row[k] = int(v) if isinstance(v, (int, float)) else str(v)
        result.append(clean_row)

    return result



@app.get("/report/content-gaps")
def content_gaps():
    if usage_df.empty:
        return []

    gaps = usage_df[
        (usage_df["avg_score"] < 0.3) &
        (usage_df["usage_count"] >= 2)
    ]

    return gaps.to_dict(orient="records")
