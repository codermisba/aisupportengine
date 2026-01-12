

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
    ticket_text = st.text_area("Ticket Content", height=160, placeholder="Describe the customer issue in detail")
    top_k = st.selectbox("Number of Recommendations", [1, 3, 5], index=1)

    if st.button("Analyze Ticket"):
        if not ticket_text.strip():
            st.warning("Please enter ticket content.")
        else:
            with st.spinner("Analyzing ticket..."):
                try:
                    response = requests.post(f"{API_BASE}/recommend", json={"ticket_text": ticket_text, "top_k": top_k})
                    if response.status_code == 200:
                        results = response.json().get("recommendations", [])
                        usage_df = load_usage_store()
                        st.subheader("Recommended Articles")

                        for rec in results:
                            recommendation_card(rec["title"], rec["category"], rec["tags"], rec["score"])

                            # Update usage metrics locally
                            mask = usage_df["article_id"] == rec["article_id"]
                            if mask.any():
                                prev_count = usage_df.loc[mask, "usage_count"].values[0]
                                prev_avg = usage_df.loc[mask, "avg_score"].values[0]
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
                        # Save updated usage
                        usage_df.to_csv(USAGE_PATH, index=False)
                    else:
                        st.error("Backend error: unable to fetch recommendations.")
                except Exception as e:
                    st.error(f"Connection failed: {e}")

# =========================================================
# TAB 2 — KNOWLEDGE BASE
# =========================================================
with tab2:
    st.subheader("Knowledge Base Health")
    try:
        response = requests.get(f"{API_BASE}/report/kb-health")
        if response.status_code == 200:
            kb_health = response.json()
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Articles", kb_health.get("total_articles", 0))
            col2.metric("Actively Used Articles", kb_health.get("actively_used_articles", 0))
            col3.metric("Unused Articles", kb_health.get("unused_articles", 0))
            st.metric("Average Relevance Score", kb_health.get("average_relevance_score", 0.0))
        else:
            st.error("Failed to fetch KB health report.")
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")

    st.markdown("---")
    # Article Performance Table
    st.subheader("Article Performance")
    try:
        response = requests.get(f"{API_BASE}/report/article-performance")
        if response.status_code == 200:
            performance = pd.DataFrame(response.json())
            st.dataframe(performance, use_container_width=True)
        else:
            st.info("No article performance data yet.")
    except:
        st.info("No article performance data yet.")

# =========================================================
# TAB 3 — INSIGHTS / Content Gaps
# =========================================================
with tab3:
    st.subheader("Content Gaps")
    try:
        response = requests.get(f"{API_BASE}/report/content-gaps")
        if response.status_code == 200:
            gaps = pd.DataFrame(response.json())
            if not gaps.empty:
                st.dataframe(gaps, use_container_width=True)
            else:
                st.info("No content gaps detected.")
        else:
            st.error("Failed to fetch content gap report.")
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")

    st.markdown("---")
    # Sample Insights Chart
    st.subheader("Operational Insights")
    df = pd.DataFrame({"Category": ["Password", "Billing", "Subscription", "Login"], "Tickets": [42, 15, 8, 27]})
    chart = alt.Chart(df).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
        x=alt.X("Category", sort=None),
        y="Tickets",
        color=alt.Color("Category", legend=None),
        tooltip=["Category", "Tickets"]
    ).properties(width=600, height=350)
    st.altair_chart(chart, use_container_width=True)

# =========================================================
# FOOTER
# =========================================================
st.markdown("<hr><center style='color:#64748B;font-size:13px;'>AI Knowledge Engine · Internship Project · 2026</center>", unsafe_allow_html=True)
