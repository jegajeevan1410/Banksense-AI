# BankSense AI 💳

A RAG-powered personal finance assistant that parses real bank statement PDFs and provides AI-driven insights, spending analytics, and loan eligibility checks.

Built as a portfolio project to demonstrate Retrieval-Augmented Generation (RAG) applied to a real-world financial use case — combining document parsing, vector search, and LLM reasoning with practical analytics.



**🔗 Live Demo:** [banksense-ai-jegajeevan1410.streamlit.app](https://banksense-ai-jegajeevan1410.streamlit.app)

---

## Features

- **PDF Statement Upload** — Upload password-protected bank statement PDFs and extract transactions automatically, with content-based column detection that adapts across different bank formats
- **RAG-Powered Chat** — Ask natural-language questions about your finances ("What's my debit sum?", "Am I eligible for a ₹5 lakh loan?") and get answers grounded in retrieved banking rules, not hallucinated guesses
- **Spending Dashboard** — Auto-categorized spending breakdown (UPI payments, cash withdrawals, salary credits, interest, etc.) visualized with interactive charts
- **Loan Eligibility Calculator** — EMI calculation and income-based eligibility check using standard banking debt-to-income rules
- **Sample Data Mode** — Works out of the box with synthetic transaction data if no statement is uploaded

---

## Tech Stack

| Layer | Tool |
|---|---|
| LLM | [Groq](https://groq.com) (Llama 3.1 8B Instant) |
| Orchestration | LangChain |
| Embeddings | HuggingFace Sentence Transformers (`all-MiniLM-L6-v2`) |
| Vector Store | ChromaDB |
| PDF Parsing | pdfplumber |
| Frontend | Streamlit |
| Data & Charts | Pandas, Plotly |

---

## How It Works

1. **Ingestion** — Banking rules and guidelines (loan eligibility criteria, savings benchmarks, budgeting rules) are embedded and stored in a local ChromaDB vector store.
2. **Retrieval** — When a user asks a question, the most relevant rules are retrieved via semantic similarity search.
3. **Generation** — The retrieved context, plus a structured summary of the user's actual financial data, is passed to the LLM to generate a grounded, personalized answer.
4. **PDF Parsing** — Uploaded statements are parsed using a content-detection approach (identifying date/text/amount columns by pattern rather than fixed position), making it more robust across different bank statement layouts.

---

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/jegajeevan1410/Banksense-AI.git
cd Banksense-AI
```

### 2. Create a virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up your API key
Create a `.env` file in the project root:
```
GROQ_API_KEY=your_groq_api_key_here
```
Get a free key at [console.groq.com/keys](https://console.groq.com/keys)

### 5. Generate sample data
```bash
python setup.py
```

### 6. Run the app
```bash
streamlit run bank.py
```

---

## Project Structure

```
Banksense-AI/
├── bank.py              # Main Streamlit app (UI, dashboard, chat)
├── pdf_parser.py         # PDF extraction & column-detection logic
├── rag_utils.py          # ChromaDB setup & retrieval functions
├── setup.py              # Generates synthetic sample bank data
├── bank_statement.csv    # Sample transaction data
└── requirements.txt
```

---

## Demo

> Sample data is used for all screenshots/demos below — no real financial data is shown.

*(Add screenshots or a short demo GIF here once available)*

---

## Limitations

- PDF parsing is tuned for common Indian bank statement layouts; highly unusual or scanned (image-only) PDFs may require OCR support not yet implemented
- Free-tier LLM rate limits apply (Groq/Gemini)
- This is a portfolio/demo project — not intended for production financial advice

---

## Author

**Jegajeevan**
[LinkedIn](https://linkedin.com/in/jegajeevan1410) · [GitHub](https://github.com/jegajeevan1410)
