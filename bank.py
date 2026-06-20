import os
import streamlit as st
import plotly.express as px
import pandas as pd
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from rag_utils import retrieve_rules
from pdf_parser import parse_bank_statement_pdf, clean_statement_df, map_to_standard_format

load_dotenv()
groq_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")

if not groq_key:
    st.error("GROQ_API_KEY not found! Check your .env file.")
    st.stop()

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=groq_key
)


prompt = PromptTemplate.from_template("""
You are a personal finance AI assistant. Here is the user's financial summary:

{financial_summary}

Relevant banking rules and guidelines:
{retrieved_rules}

User question: {query}

Give a clear, helpful, personalized answer. Use ₹ for amounts.
""")

st.set_page_config(page_title="BankSense AI", layout="wide")
st.title("BankSense AI 💳")

st.sidebar.subheader("📄 Upload Your Statement")
uploaded_pdf = st.sidebar.file_uploader("Upload bank statement (PDF)", type=["pdf"])
pdf_password = st.sidebar.text_input("PDF Password (if protected)", type="password")

df = pd.read_csv("bank_statement.csv")
using_sample_data = True

if uploaded_pdf is not None:
    with st.spinner("Extracting transactions..."):
        raw_df, error = parse_bank_statement_pdf(uploaded_pdf, password=pdf_password or None)
        if raw_df is not None:
            cleaned_df = clean_statement_df(raw_df)
            if len(cleaned_df) > 0:
                df = map_to_standard_format(cleaned_df)
                using_sample_data = False
                
                st.dataframe(df)
            
                st.sidebar.success(f"Extracted {len(cleaned_df)} rows from your statement")
                with st.sidebar.expander("Preview extracted data"):
                    st.dataframe(df.head(10))
            else:
                st.sidebar.warning("PDF opened but no transactions detected. Using sample data.")
        else:
            st.sidebar.error(f"Couldn't extract tables: {error}")

if using_sample_data:
    st.sidebar.info("📊 Currently showing sample data. Upload your statement to see your real data.")


tab1, tab2 = st.tabs(["💬 Chat", "📊 Dashboard"])

with tab2:
    st.subheader("Spending Overview")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Debit", f"₹{df['debit'].sum():,.2f}")
    with col2:
        st.metric("Total Credit", f"₹{df['credit'].sum():,.2f}")
    with col3:
        net = df['credit'].sum() - df['debit'].sum()
        st.metric("Net Savings", f"₹{net:,.2f}")

    spend = df[df["debit"] > 0].groupby("category")["debit"].sum().reset_index()
    fig = px.pie(spend, values="debit", names="category", title="Spending by Category")
    st.plotly_chart(fig, use_container_width=True)

    monthly = df.groupby(df["date"].str[:7]).agg(
        income=("credit", "sum"), expenses=("debit", "sum")).reset_index()
    fig2 = px.bar(monthly, x="date", y=["income", "expenses"],
                  barmode="group", title="Monthly Income vs Expenses")
    st.plotly_chart(fig2, use_container_width=True)

total_income = df["credit"].sum()
total_spend = df["debit"].sum()
savings_rate = round((total_income - total_spend) / total_income * 100, 1)
if len(spend) > 0:
    top_category = spend.sort_values('debit', ascending=False).iloc[0]['category']
else:
    top_category = "N/A"

with tab1:
    fin_summary = f"""
    Monthly income: ₹{total_income/3:,.0f}
    Monthly expenses: ₹{total_spend/3:,.0f}
    Savings rate: {savings_rate}%
    Top spending: {top_category}
    """

    query = st.text_input("Ask about your finances or loan eligibility:")
    if st.button("Ask BankSense") and query:
        with st.spinner("Thinking..."):
            rules = retrieve_rules(query)
            response = llm.invoke(prompt.format(
                financial_summary=fin_summary,
                retrieved_rules=rules,
                query=query
            ))
            st.write(response.content)

with st.sidebar:
    st.subheader("Loan Eligibility Check")
    loan_amt = st.number_input("Loan Amount (₹)", value=500000, step=10000)
    tenure = st.slider("Tenure (months)", 12, 240, 60)
    rate = 8.5
    monthly_emi = loan_amt * (rate/1200) / (1-(1+rate/1200)**-tenure)
    monthly_income = total_income / 3
    eligible = monthly_income >= 3 * monthly_emi
    st.metric("Monthly EMI", f"₹{monthly_emi:,.0f}")
    if eligible:
        st.success("✅ Likely eligible!")
    else:
        st.error("❌ Income too low for this loan")