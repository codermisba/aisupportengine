import streamlit as st

def recommendation_card(title, category, tags, score):
    percent = int(score * 100)

    if percent >= 60:
        color = "#16A34A"
        label = "High Match"
    elif percent >= 30:
        color = "#F59E0B"
        label = "Medium Match"
    else:
        color = "#DC2626"
        label = "Content Gap"

    st.markdown(
        f"""
        <div style="
            background: rgba(255,255,255,0.75);
            backdrop-filter: blur(12px);
            border-radius:18px;
            padding:20px;
            margin-bottom:18px;
            box-shadow: 0 12px 32px rgba(0,0,0,0.08);
        ">
            <div style="display:flex; justify-content:space-between;">
                <h4>📄 {title}</h4>
                <span style="
                    background:{color};
                    color:white;
                    padding:4px 12px;
                    border-radius:999px;
                    font-size:12px;
                ">
                    {label}
                </span>
            </div>

            <p style="color:#475569;"><b>Category:</b> {category}</p>

            <div>
                {" ".join([
                    f"<span style='background:#E0E7FF;padding:4px 10px;border-radius:999px;margin-right:6px;font-size:12px;'>{t}</span>"
                    for t in tags.split(",")
                ])}
            </div>

            <div style="margin-top:12px;">
                <div style="font-size:13px;">Relevance Score</div>
                <div style="
                    height:8px;
                    background:#E5E7EB;
                    border-radius:999px;
                ">
                    <div style="
                        width:{percent}%;
                        height:100%;
                        background:{color};
                        border-radius:999px;
                    "></div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
