"""
app.py - the Streamlit website.
Upload PDFs -> everything runs automatically -> Dashboard tab + Chat tab.
Run with:  streamlit run app.py
"""
import plotly.express as px
import streamlit as st

from analysis import health_flags
from graph import ask
from llm import PROVIDER
from pipeline import process_pdf

st.set_page_config(page_title="DocIntel", layout="wide")
st.title("DocIntel - Credit Rating Report Analyzer")
st.caption(f"AI provider: {PROVIDER}")


@st.cache_resource(show_spinner="Reading and indexing the report...")
def process(file_bytes: bytes):
    """Runs once per unique PDF (cached by its content)."""
    return process_pdf(file_bytes)


files = st.sidebar.file_uploader("Upload rating report PDFs", type="pdf", accept_multiple_files=True)
if not files:
    st.info("Upload one or more credit rating report PDFs in the sidebar to begin.")
    st.stop()

results = {}
for f in files:
    try:
        results[f.name] = process(f.getvalue())
    except Exception as e:
        st.sidebar.error(f"Could not process {f.name}: {e}")
if not results:
    st.stop()

name = st.sidebar.selectbox("Report", list(results))
report, metrics, store = results[name]

dashboard_tab, chat_tab = st.tabs(["Dashboard", "Chat"])

with dashboard_tab:
    st.subheader(f"{report.company_name}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rating", report.rating or "n/a")
    c2.metric("Outlook", report.outlook or "n/a")
    c3.metric("Agency", report.agency or "n/a")
    c4.metric("Report date", report.report_date or "n/a")

    for flag in health_flags(metrics):
        st.warning(flag)

    if metrics.empty:
        st.info("No multi-year financial table was found in this report.")
    else:
        left, right = st.columns(2)
        left.plotly_chart(px.bar(metrics, x="Year", y=["Revenue", "EBITDA", "Net Profit"],
                                 barmode="group", title="Revenue, EBITDA and Net Profit (INR crore)"),
                          width="stretch")
        right.plotly_chart(px.line(metrics, x="Year", y=["EBITDA Margin %", "Net Margin %"],
                                   markers=True, title="Profit margins (%)"), width="stretch")
        left, right = st.columns(2)
        left.plotly_chart(px.line(metrics, x="Year", y="Debt / Equity (x)", markers=True,
                                  title="Debt / Equity (x)"), width="stretch")
        right.plotly_chart(px.line(metrics, x="Year", y="Interest Cover (x)", markers=True,
                                   title="Interest cover (x)"), width="stretch")
        with st.expander("Full metrics table"):
            st.dataframe(metrics.round(2), width="stretch")

    s, r = st.columns(2)
    s.markdown("**Credit strengths**")
    s.markdown("\n".join(f"- {x}" for x in report.strengths) or "_none found_")
    r.markdown("**Credit risks**")
    r.markdown("\n".join(f"- {x}" for x in report.risks) or "_none found_")

with chat_tab:
    history = st.session_state.setdefault("history", {}).setdefault(name, [])
    for role, text in history:
        st.chat_message(role).markdown(text)
    question = st.chat_input("Ask about this report, e.g. 'Why was this rating assigned?'")
    if question:
        st.chat_message("user").markdown(question)
        try:
            reply = ask(question, report, metrics, store)
        except Exception as e:
            reply = f"Sorry, the AI service failed: {e}"
        st.chat_message("assistant").markdown(reply)
        history += [("user", question), ("assistant", reply)]
