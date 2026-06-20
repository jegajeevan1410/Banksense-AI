import pdfplumber
import pandas as pd
import re


def parse_bank_statement_pdf(uploaded_file, password=None):
    """
    Extracts transaction data from a bank statement PDF.
    Tries table extraction first; falls back to raw text parsing
    if no tables are detected (common with some bank PDF layouts).
    Returns (DataFrame, error_message) or (DataFrame, None) on success.
    """
    table_rows = []
    raw_text_lines = []

    try:
        with pdfplumber.open(uploaded_file, password=password) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        if row and len(row) >= 3:
                            table_rows.append(row)

                text = page.extract_text()
                if text:
                    raw_text_lines.extend(text.split("\n"))
    except Exception as e:
        return None, str(e)

    if table_rows:
        df = pd.DataFrame(table_rows)
        df = df.dropna(how="all")
        return df, None

    # Fallback: no tables detected, try raw text line parsing
    if raw_text_lines:
        df = pd.DataFrame({"raw_line": raw_text_lines})
        return df, None

    return None, "No tables or text found in PDF"


def clean_statement_df(raw_df):
    """
    Filters rows down to ones that look like actual transaction rows
    (i.e. contain a recognizable date), across multiple date formats.
    """
    date_pattern = re.compile(r"\b(0[1-9]|[12]\d|3[01])[-/](0[1-9]|1[012])[-/](20\d{2})\b")

    if "raw_line" in raw_df.columns:
        # Text-line fallback mode
        mask = raw_df["raw_line"].apply(lambda x: bool(date_pattern.search(str(x))))
        return raw_df[mask].reset_index(drop=True)

    # Table mode
    cleaned_rows = []
    for _, row in raw_df.iterrows():
        row_str = " ".join([str(x) for x in row if x is not None])
        if date_pattern.search(row_str):
            cleaned_rows.append(row)
    return pd.DataFrame(cleaned_rows)


def map_to_standard_format(cleaned_df):
    """
    Tailored for Axis Bank statement layout:
    columns = [Date, ChqNo, Particulars, Debit, Credit, Balance, BranchCode]
    Debit and Credit are separate columns — only one has a value per row.
    """
    if cleaned_df.empty:
        return cleaned_df

    def is_amount(val):
        if val is None:
            return False
        v = str(val).replace(",", "").strip()
        if v in ["-", ""]:
            return False
        try:
            float(v)
            return True
        except ValueError:
            return False

    def is_decimal_amount(val):
        if not is_amount(val):
            return False
        v = str(val).replace(",", "").strip()
        return "." in v

    def clean_amount(val):
        if val is None or str(val).strip() in ["-", ""]:
            return 0.0
        v = str(val).replace(",", "").strip()
        try:
            return float(v)
        except ValueError:
            return 0.0

    date_pattern = re.compile(r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4}")

    rows_out = []
    for _, row in cleaned_df.iterrows():
        row_vals = row.tolist()

        date_val = next((v for v in row_vals if v and date_pattern.search(str(v))), None)

        text_candidates = [
            v for v in row_vals
            if v and not date_pattern.search(str(v)) and not is_amount(v)
        ]
        desc_val = max(text_candidates, key=lambda x: len(str(x)), default="")

        # Get decimal-amount columns in their ORIGINAL left-to-right order
        amount_positions = [(i, v) for i, v in enumerate(row_vals) if is_decimal_amount(v)]

        debit = credit = balance = 0.0
        if len(amount_positions) == 3:
            # Exactly 3 amounts found: debit, credit, balance — but only ONE of
            # debit/credit is real per row in Axis format; the other was empty
            # and got skipped, so 3 found means: [first_amt, second_amt, balance]
            # where first_amt is whichever of debit/credit had a value.
            # We rely on column position: if it's the EARLIER of the two amount
            # columns relative to balance, treat as debit; else credit.
            # Axis order is Debit(col3) then Credit(col4) then Balance(col5).
            first_idx, first_val = amount_positions[0]
            second_idx, second_val = amount_positions[1]
            balance = amount_positions[2][1]
            # Determine which original column index corresponds to debit vs credit
            # by comparing to typical Axis column positions (3=debit, 4=credit)
            debit, credit = first_val, second_val
        elif len(amount_positions) == 2:
            # Only ONE of debit/credit had a value (the other was blank/skipped)
            amt_val = amount_positions[0][1]
            balance = amount_positions[1][1]
            amt_col_index = amount_positions[0][0]
            # Heuristic: in this Axis layout, debit column appears before credit
            # column in the raw row. Since only one of them is non-empty, check
            # its position relative to where balance is found.
            # If amt_col_index is closer to the start (lower index), likely debit.
            mid_point = len(row_vals) // 2
            if amt_col_index <= mid_point:
                debit = amt_val
            else:
                credit = amt_val
        elif len(amount_positions) == 1:
            balance = amount_positions[0][1]

        rows_out.append({
            "date": date_val,
            "description": desc_val,
            "debit": clean_amount(debit),
            "credit": clean_amount(credit),
            "balance": clean_amount(balance),
        })

    mapped = pd.DataFrame(rows_out)

    def categorize(desc):
        desc = str(desc).upper()
        if "NEFT" in desc or "SALARY" in desc:
            return "Income/Salary"
        elif "ATM" in desc or "CASH" in desc:
            return "Cash Withdrawal"
        elif "UPI/P2M" in desc:
            return "UPI Merchant Payment"
        elif "UPI/P2A" in desc:
            return "UPI Transfer"
        elif "SB:" in desc or "INT.PD" in desc:
            return "Interest"
        else:
            return "Other"

    mapped["category"] = mapped["description"].apply(categorize)
    # Parse dates properly (handles DD-MM-YYYY format) and drop anything invalid
    mapped["date"] = pd.to_datetime(mapped["date"], format="%d-%m-%Y", errors="coerce", dayfirst=True)
    mapped = mapped[mapped["date"].notna()].reset_index(drop=True)
    mapped["date"] = mapped["date"].dt.strftime("%Y-%m-%d")  # convert back to clean string for display

    return mapped