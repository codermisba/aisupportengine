

# app.py
import streamlit as st
import requests
import pandas as pd
import altair as alt
import os

# =========================================================
# PATH SETUP
# =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))

USAGE_PATH = os.path.join(PROJECT_ROOT, "backend", "data", "kb_usage_store.csv")

# =========================================================
# HELPER FUNCTIONS
# =========================================================
@st.cache_data
def load_usage_store():
    if os.path.exists(USAGE_PATH):
        return pd.read_csv(USAGE_PATH)
    return pd.DataFrame(columns=["article_id", "usage_count", "avg_score"])

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="AI Knowledge Engine",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# GLOBAL STYLES
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
.stApp {background: linear-gradient(135deg, #F8FAFC, #EEF2FF); font-family: 'Inter', sans-serif;}
h1, h2, h3 {text-align:center; color:#0F172A; font-weight:700;}
p, span, label {text-align:center; color:#475569;}
textarea {border-radius:14px !important; border:1px solid #CBD5E1 !important; font-size:15px !important;}
.stButton > button {display:block; margin:1rem auto; background: linear-gradient(135deg, #1E40AF, #2563EB); color:white; border-radius:14px; padding:0.75em 1.6em; font-weight:600; box-shadow:0 10px 25px rgba(37,99,235,0.3);}
.stButton > button:hover {background: linear-gradient(135deg, #1E3A8A, #1D4ED8); transform: translateY(-2px);}
[data-testid="metric-container"] {background:white; border-radius:16px; padding:16px; text-align:center; box-shadow:0 10px 25px rgba(0,0,0,0.08);}
div[data-baseweb="tab-list"] {justify-content:center;}
</style>
""", unsafe_allow_html=True)

# =========================================================
# HEADER
# =========================================================
st.title("AI-Powered Knowledge Engine")
st.caption("Centralized intelligence for support ticket analysis, knowledge discovery, and content gap insights")

# =========================================================
# API CONFIG
# =========================================================
API_BASE = "http://127.0.0.1:8000"

# =========================================================
# RECOMMENDATION CARD
# =========================================================
def recommendation_card(title, category, tags, score):
    percent = int(score * 100)
    if percent >= 60: color, label = "#16A34A", "High Match"
    elif percent >= 30: color, label = "#F59E0B", "Medium Match"
    else: color, label = "#DC2626", "Content Gap"

    html = f"""
    <div style="background:white; border-radius:20px; padding:24px; margin:24px auto; max-width:720px; box-shadow:0 12px 28px rgba(0,0,0,0.1); text-align:center;">
        <h4 style="margin-bottom:6px;">{title}</h4>
        <div style="display:inline-block; background:{color}; color:white; padding:6px 16px; border-radius:999px; font-size:12px; font-weight:600; margin-bottom:10px;">{label}</div>
        <p><b>Category:</b> {category}</p>
        <div style="margin-bottom:12px;">{" ".join(f"<span style='background:#EEF2FF;padding:6px 12px;border-radius:999px;margin:4px;display:inline-block;font-size:12px;color:#3730A3;'>{t.strip()}</span>" for t in tags.split(","))}</div>
        <div style="font-size:13px;margin-bottom:6px;">Relevance Score</div>
        <div style="height:10px;background:#E5E7EB;border-radius:999px;">
            <div style="width:{percent}%;height:100%;background:{color};border-radius:999px;"></div>
        </div>
    </div>
    """
    st.components.v1.html(html, height=280)



# =========================================================
# TABS
# =========================================================
tab1, tab2, tab3 = st.tabs(["Ticket Analyzer", "Knowledge Base", "Insights"])

# =========================================================
# TAB 1 — TICKET ANALYZER
# =========================================================
with tab1:
    st.subheader("Ticket Analysis")

    # Single-column layout
    ticket_text = st.text_input(
        "Ticket Content",
        placeholder="Describe the customer issue in detail",
        key="ticket_input"
    )

    top_k = st.selectbox(
        "Number of Recommendations",
        [1, 3, 5],
        index=1
    )

    # Analyze button
    analyze_button = st.button("Analyze Ticket", key="analyze_btn")

    if analyze_button:
        if not ticket_text.strip():
            st.warning("Please enter ticket content.")
        else:
            with st.spinner("Analyzing ticket..."):
                try:
                    payload = {"ticket_text": ticket_text, "top_k": top_k}

                    response = requests.post(
                        f"{API_BASE}/recommend",
                        json=payload,
                        timeout=30
                    )

                    if response.status_code != 200:
                        st.error("Backend error: unable to fetch recommendations.")
                        st.stop()

                    data = response.json()

                    # ---------------- AI RESPONSE ----------------
                    st.subheader("AI Suggested Resolution")
                    st.info(
                        data.get("ai_response", "No AI-generated solution available.")
                    )

                    confidence = data.get("confidence", "low")
                    st.caption(f"Confidence level: {confidence.upper()}")

                    # ---------------- RECOMMENDATIONS ----------------
                    results = data.get("recommendations", [])
                    st.subheader("Recommended Articles")

                    if not results:
                        st.warning("No relevant knowledge base articles found.")
                        st.stop()

                    usage_df = load_usage_store()

                    for rec in results:
                        recommendation_card(
                            rec["title"],
                            rec["category"],
                            rec["tags"],
                            rec["score"]
                        )

                        mask = usage_df["article_id"] == rec["article_id"]

                        if mask.any():
                            prev_count = int(usage_df.loc[mask, "usage_count"].values[0])
                            prev_avg = float(usage_df.loc[mask, "avg_score"].values[0])
                            new_count = prev_count + 1
                            new_avg = ((prev_avg * prev_count) + rec["score"]) / new_count
                            usage_df.loc[mask, "usage_count"] = new_count
                            usage_df.loc[mask, "avg_score"] = round(new_avg, 3)
                        else:
                            usage_df.loc[len(usage_df)] = {
                                "article_id": rec["article_id"],
                                "usage_count": 1,
                                "avg_score": round(rec["score"], 3)
                            }

                    usage_df.to_csv(USAGE_PATH, index=False)

                except requests.exceptions.RequestException as e:
                    st.error("Could not connect to backend API.")
                    st.exception(e)

    # =========================================================
    # CSS FOR INPUT AND BUTTON
    # =========================================================
    st.markdown("""
    <style>
    /* Single-line input styling */
    div.stTextInput > div > input {
        height: 44px;
        font-size: 15px;
        border-radius: 10px;
        padding: 0 12px;
        border: 1px solid #CBD5E1;
        background-color: #F8FAFC;
    }

    /* Button styling */
    div.stButton > button {
        background: linear-gradient(135deg, #2563EB, #1E3A8A);
        color: white;
        font-weight: 600;
        width: 100%;
        height: 48px;
        border-radius: 12px;
        margin-top: 8px;
        box-shadow: 0 6px 18px rgba(37,99,235,0.25);
        font-size: 16px;
    }

    div.stButton > button:hover {
        background: linear-gradient(135deg, #1D4ED8, #1E40AF);
        transform: translateY(-1px);
    }
    </style>
    """, unsafe_allow_html=True)

# =========================================================
# TAB 2 — KNOWLEDGE BASE
# =========================================================
with tab2:
    st.subheader("Knowledge Base Health Overview")

    # =========================================================
    # FETCH KB HEALTH
    # =========================================================
    try:
        response = requests.get(f"{API_BASE}/report/kb-health")
        if response.status_code != 200:
            st.error("Failed to fetch KB health report.")
            st.stop()

        kb_health = response.json()

        total_articles = max(0, int(kb_health.get("total_articles", 0)))
        actively_used = max(0, int(kb_health.get("actively_used_articles", 0)))
        unused_articles = max(0, total_articles - actively_used)
        avg_score = round(float(kb_health.get("average_relevance_score", 0.0)), 3)

        # ---------------- METRICS ----------------
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Articles", total_articles)
        col2.metric("Actively Used", actively_used)
        col3.metric("Unused Articles", unused_articles)
        col4.metric("Avg Relevance Score", avg_score)

    except Exception as e:
        st.error(f"Error connecting to backend: {e}")
        st.stop()

    st.markdown("---")

    # =========================================================
    # ARTICLE USAGE DISTRIBUTION
    # =========================================================
    st.subheader("How Articles Are Being Used")

    usage_df = load_usage_store()

    if usage_df.empty:
        st.info("No usage data available yet.")
    else:
        usage_df["Usage Category"] = pd.cut(
            usage_df["usage_count"],
            bins=[-1, 0, 3, 10, 1_000_000],
            labels=[
                "Unused (0)",
                "Low Usage (1–3)",
                "Medium Usage (4–10)",
                "High Usage (10+)"
            ]
        )

        dist_df = (
            usage_df["Usage Category"]
            .value_counts()
            .reset_index()
        )

        dist_df.columns = ["Usage Category", "Number of Articles"]

        usage_chart = (
            alt.Chart(dist_df)
            .mark_bar(size=40, cornerRadius=6)
            .encode(
                y=alt.Y("Usage Category:N", sort=None, title=""),
                x=alt.X("Number of Articles:Q", title="Article Count"),
                tooltip=["Usage Category", "Number of Articles"]
            )
            .properties(height=280)
        )

        st.altair_chart(usage_chart, use_container_width=True)

        st.caption(
            "This distribution shows how frequently knowledge base articles are used during ticket resolution."
        )

    st.markdown("---")

    # =========================================================
    # TOP PERFORMING ARTICLES
    # =========================================================
    st.subheader("Most Helpful Knowledge Articles")

    try:
        response = requests.get(f"{API_BASE}/report/article-performance")

        if response.status_code != 200:
            st.info("Article performance data not available.")
        else:
            perf_df = pd.DataFrame(response.json())

            # Defensive cleaning
            perf_df = perf_df.dropna(subset=["avg_score"])
            perf_df = perf_df[perf_df["usage_count"] > 0]

            if perf_df.empty:
                st.info("No article has sufficient usage data yet.")
            else:
                top_articles = (
                    perf_df
                    .sort_values(["usage_count", "avg_score"], ascending=False)
                    .head(8)
                )

                perf_chart = (
                    alt.Chart(top_articles)
                    .mark_bar(size=38, cornerRadius=6)
                    .encode(
                        y=alt.Y(
                            "article_id:N",
                            sort="-x",
                            title="Article ID"
                        ),
                        x=alt.X(
                            "usage_count:Q",
                            title="Times Used"
                        ),
                        color=alt.Color(
                            "avg_score:Q",
                            scale=alt.Scale(scheme="blues"),
                            title="Avg Relevance"
                        ),
                        tooltip=[
                            "article_id",
                            "usage_count",
                            alt.Tooltip("avg_score:Q", format=".2f")
                        ]
                    )
                    .properties(height=320)
                )

                st.altair_chart(perf_chart, use_container_width=True)

                st.caption(
                    "Articles used frequently with higher relevance scores contribute most to successful resolutions."
                )

    except Exception:
        st.info("Unable to load article performance data.")

    st.markdown("---")

    # =========================================================
    # KEY INSIGHTS SUMMARY
    # =========================================================
    st.subheader("Key Insights & Recommendations")

    insights = []

    if unused_articles > 0:
        insights.append(
            f"{unused_articles} articles are currently unused and may need content review or better tagging."
        )

    if avg_score < 0.4:
        insights.append(
            "Average relevance score is low, indicating gaps between ticket queries and available knowledge."
        )
    else:
        insights.append(
            "Knowledge base content shows good alignment with incoming ticket queries."
        )

    usage_ratio = actively_used / max(total_articles, 1)

    if usage_ratio < 0.5:
        insights.append(
            "Less than half of the knowledge base is actively used, suggesting scope for optimization or consolidation."
        )

    for insight in insights:
        st.write(f"- {insight}")

# =========================================================
# TAB 3 — INSIGHTS / Content Gaps
# =========================================================
with tab3:
    st.subheader("Content Gaps & Operational Insights")

    # =========================================================
    # FETCH CONTENT GAPS
    # =========================================================
    try:
        response = requests.get(f"{API_BASE}/report/content-gaps")
        if response.status_code != 200:
            st.error("Failed to fetch content gap report.")
            st.stop()

        gaps_df = pd.DataFrame(response.json())

        if gaps_df.empty:
            st.info("No content gaps detected.")
            total_gaps = 0
        else:
            total_gaps = len(gaps_df)
            st.write(f"Total content gaps detected: **{total_gaps}**")

    except Exception as e:
        st.error(f"Error connecting to backend: {e}")
        st.stop()

    st.markdown("---")

    # =========================================================
    # OPERATIONAL INSIGHTS (Sample Ticket Data)
    # =========================================================
    st.subheader("Operational Ticket Trends")

    df_tickets = pd.DataFrame({
        "Category": ["Password", "Billing", "Subscription", "Login"],
        "Tickets": [42, 15, 8, 27]
    })

    tickets_chart = (
        alt.Chart(df_tickets)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
        .encode(
            x=alt.X("Category:N", title="Category"),
            y=alt.Y("Tickets:Q", title="Number of Tickets"),
            color=alt.Color("Tickets:Q", scale=alt.Scale(scheme="tealblues")),
            tooltip=["Category", "Tickets"]
        )
        .properties(height=300)
    )

    st.altair_chart(tickets_chart, use_container_width=True)
    st.caption("This chart shows ticket volume trends across categories to identify areas needing KB updates.")

    st.markdown("---")

    # =========================================================
    # KEY INSIGHTS
    # =========================================================
    st.subheader("Key Insights & Recommendations")
    insights = []

    if total_gaps > 0:
        insights.append(f"{total_gaps} content gaps detected. Prioritize updating knowledge base in these areas.")

    high_ticket_categories = df_tickets[df_tickets["Tickets"] > 20]["Category"].tolist()
    if high_ticket_categories:
        insights.append(
            f"High ticket volume in categories: {', '.join(high_ticket_categories)}. These may require KB optimization."
        )

    if total_gaps > 0 and len(high_ticket_categories) > 0:
        insights.append("Focus on aligning KB content with high ticket categories to reduce resolution time.")

    if not insights:
        insights.append("All categories appear well-covered. Continue monitoring for gaps.")

    for insight in insights:
        st.write(f"- {insight}")
