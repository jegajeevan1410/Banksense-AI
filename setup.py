import pandas as pd
import numpy as np

np.random.seed(42)
debits = ["Rent","Groceries","Food & Dining","Entertainment","EMI","Utilities"]

rows = []
for month in range(1, 4):
    rows.append({"date": f"2026-0{month}-01", "description": "Salary Credit",
                 "category": "Salary", "debit": 0, "credit": 45000})
    for _ in range(20):
        cat = np.random.choice(debits)
        amt = np.random.randint(200, 8000)
        rows.append({"date": f"2026-0{month}-{np.random.randint(2,28):02d}",
                     "description": cat, "category": cat,
                     "debit": amt, "credit": 0})

df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
df["balance"] = 50000 + df["credit"].cumsum() - df["debit"].cumsum()
df.to_csv("bank_statement.csv", index=False)
print("✅ bank_statement.csv created!")