import chromadb
from sentence_transformers import SentenceTransformer

client = chromadb.PersistentClient(path="./chroma_db")

banking_rules = [
    "Home loan eligibility: Monthly income must be at least 3x the EMI. Minimum salary ₹25,000/month.",
    "Personal loan: Debt-to-income ratio must be below 40%. Existing EMIs should not exceed 40% of income.",
    "Car loan: Minimum 6 months employment history required. Down payment of 10-20% recommended.",
    "Savings health: A savings rate above 20% of income is considered healthy.",
    "Credit score: 750+ is excellent, 700-749 is good, 650-699 is fair, below 650 is poor.",
    "Emergency fund: Recommended to have 3-6 months of expenses saved.",
    "Budget rule: 50% needs, 30% wants, 20% savings (50-30-20 rule).",
]

model = SentenceTransformer("all-MiniLM-L6-v2")
collection = client.get_or_create_collection("banking_kb")

if collection.count() == 0:
    embeddings = model.encode(banking_rules).tolist()
    collection.add(
        documents=banking_rules,
        embeddings=embeddings,
        ids=[f"rule_{i}" for i in range(len(banking_rules))]
    )

def retrieve_rules(query: str, top_k: int = 3):
    qe = model.encode([query]).tolist()
    results = collection.query(query_embeddings=qe, n_results=top_k)
    return "\n".join(results["documents"][0])