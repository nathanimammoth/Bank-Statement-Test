import os
import tempfile
from datetime import datetime

import pandas as pd
import pytz
from tabula.io import read_pdf

# —— Category setup (adjust path if needed) ——
categories_path = os.path.join(
    os.path.dirname(__file__),
    "Column Header",
    "Bank_Statement_Extraction_Revolut.xlsx"
)
_cat_df = pd.read_excel(categories_path, sheet_name="Categories", engine="openpyxl")
categories = {
    col: _cat_df[col].dropna().str.lower().tolist()
    for col in _cat_df.columns
}

def is_valid_date(value: str, date_format: str = "%d %b %Y") -> bool:
    if not isinstance(value, str):
        return False
    value = value.replace("Sept", "Sep")
    try:
        datetime.strptime(value, date_format)
        return True
    except ValueError:
        return False

def categorize(description: str) -> str:
    if not isinstance(description, str):
        return "Uncategorized"
    desc = description.lower()
    for category, patterns in categories.items():
        for pat in patterns:
            if pat in desc:
                return category
    return "Uncategorized"

def merge_descriptions(df: pd.DataFrame) -> pd.DataFrame:
    merged_rows = []
    last_row = None

    for _, row in df.iterrows():
        if is_valid_date(row["Date"]):
            if last_row is not None:
                merged_rows.append(last_row)
            last_row = row.copy()
        else:
            if last_row is not None:
                last_row["Description"] = f"{last_row['Description']} {row['Description']}".strip()
                for num_col in ["Money out", "Money in", "Balance"]:
                    if pd.isna(row[num_col]):
                        row[num_col] = 0.0

    if last_row is not None:
        merged_rows.append(last_row)

    return pd.DataFrame(merged_rows)

def process_pdf(pdf_stream) -> pd.DataFrame:
    """
    1. Dump the stream to a temp file.
    2. Extract all tables via tabula.io.read_pdf.
    3. Validate, rename, clean, merge, categorize, and concat once.
    """
    # 1) Write stream → temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_stream.read())
        tmp_path = tmp.name

    try:
        # 2) Extract tables
        tables = read_pdf(
            tmp_path,
            pages="all",
            multiple_tables=True,
            pandas_options={"header": None}
        )
    finally:
        os.remove(tmp_path)

    # 3) Process each table into a list
    processed_tables = []
    expected_cols = ["Date", "Description", "Money out", "Money in", "Balance"]

    for table in tables or []:
        # Skip if not a DataFrame or too few columns
        if not isinstance(table, pd.DataFrame) or table.shape[1] < len(expected_cols):
            continue

        # Only keep the first five columns, rename them
        df = table.iloc[:, :5].copy()
        df.columns = expected_cols

        # Skip entirely if no valid date rows
        if not df["Date"].apply(lambda x: is_valid_date(x)).any():
            continue

        # Normalize dates & descriptions
        df["Date"] = df["Date"].fillna("").str.replace("Sept", "Sep", regex=False)
        df["Description"] = df["Description"].fillna("")

        # Merge multi-line rows
        df = merge_descriptions(df)

        # Keep only valid-date rows
        df = df[df["Date"].apply(is_valid_date)].copy()

        # Clean numeric columns
        for col in ["Money out", "Money in", "Balance"]:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(r"[£,]", "", regex=True)
                .replace("", "0")
                .astype(float)
            )

        # Categorize
        df["Category"] = df["Description"].apply(categorize)

        processed_tables.append(df)

    # 4) Concatenate once, sort & return
    if processed_tables:
        combined = pd.concat(processed_tables, ignore_index=True)
        combined["Date"] = pd.to_datetime(
            combined["Date"], format="%d %b %Y", errors="coerce"
        )
        combined = combined.sort_values(by="Date", ascending=False).reset_index(drop=True)
    else:
        # Return an empty DataFrame with all columns if nothing extracted
        combined = pd.DataFrame(columns=expected_cols + ["Category"])

    return combined