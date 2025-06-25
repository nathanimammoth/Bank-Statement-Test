import pandas as pd
from tabula import read_pdf
# …plus your helper functions (is_valid_date, merge_descriptions, categorize)…

def process_pdf(pdf_stream) -> pd.DataFrame:
    """Load tables from pdf_stream, clean & return a DataFrame."""
    tables = read_pdf(pdf_stream, pages="all", multiple_tables=True,
                      pandas_options={"header": None})
    combined = pd.DataFrame()
    for table in tables:
        if table is None or table.shape[1] < 5:
            continue
        table.columns = ["Date","Description","Money out","Money in","Balance"]
        # …apply your cleaning logic here…
        combined = pd.concat([combined, table], ignore_index=True)
    # final sort/format…
    return combined