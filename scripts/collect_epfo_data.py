from pathlib import Path
import re
import pandas as pd
import pdfplumber 


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

EPFO_RAW_DIR = BASE_DIR / "data" / "raw" / "epfo"
OUTPUT_DIR = BASE_DIR / "data" / "processed"

OUTPUT_FILE = OUTPUT_DIR / "epfo_employment.csv"

EPFO_RAW_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# MONTH MAPPING
# ============================================================

MONTH_MAP = {
    "JAN": 1,
    "FEB": 2,
    "MAR": 3,
    "APR": 4,
    "MAY": 5,
    "JUN": 6,
    "JUL": 7,
    "AUG": 8,
    "SEP": 9,
    "OCT": 10,
    "NOV": 11,
    "DEC": 12,
}


# ============================================================
# CLEAN NUMBER
# ============================================================

def clean_number(value):
    """
    Convert values such as:

        '1,234,567'
        '1234567'
        '1,234'

    into integers.
    """

    if value is None:
        return None

    value = str(value).strip()

    if value == "":
        return None

    value = value.replace(",", "")
    value = value.replace(" ", "")

    # Keep digits only
    match = re.search(r"-?\d+", value)

    if not match:
        return None

    try:
        return int(match.group())
    except ValueError:
        return None


# ============================================================
# EXTRACT TABLES FROM PDF
# ============================================================

def extract_pdf_tables(pdf_path):
    """
    Extract tables from an EPFO PDF.

    Returns a list of pandas DataFrames.
    """

    tables = []

    print(f"\nReading: {pdf_path.name}")

    with pdfplumber.open(pdf_path) as pdf:

        print(f"Pages: {len(pdf.pages)}")

        for page_number, page in enumerate(pdf.pages, start=1):

            try:
                page_tables = page.extract_tables()

                if not page_tables:
                    continue

                for table in page_tables:

                    if not table:
                        continue

                    df = pd.DataFrame(table)

                    if not df.empty:
                        tables.append(df)

            except Exception as error:
                print(
                    f"Warning: Could not read page "
                    f"{page_number}: {error}"
                )

    return tables


# ============================================================
# SEARCH FOR PAYROLL TABLE
# ============================================================

def find_payroll_table(tables):
    """
    Try to identify the EPFO table containing
    monthly payroll information.
    """

    keywords = [
        "payroll",
        "net",
        "subscriber",
        "members",
        "establishment",
        "monthly",
    ]

    candidates = []

    for df in tables:

        text = " ".join(
            df.astype(str)
            .fillna("")
            .values
            .flatten()
        ).lower()

        score = sum(
            1 for keyword in keywords
            if keyword in text
        )

        if score >= 2:
            candidates.append((score, df))

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: item[0],
        reverse=True
    )

    return candidates[0][1]


# ============================================================
# NORMALIZE EPFO TABLE
# ============================================================

def normalize_table(df, source_file):
    """
    Convert an extracted EPFO table into a normalized
    dataframe.

    NOTE:
    EPFO PDF layouts can change between reports.
    Therefore this function is intentionally conservative.
    """

    df = df.copy()

    # Remove completely empty rows/columns
    df = df.dropna(
        axis=0,
        how="all"
    )

    df = df.dropna(
        axis=1,
        how="all"
    )

    if df.empty:
        return None

    # Convert everything to strings
    df = df.astype(str)

    # Replace PDF artifacts
    df = df.replace(
        {
            "nan": None,
            "None": None,
            "": None,
        }
    )

    # Add source information
    df["source_file"] = source_file

    return df


# ============================================================
# PROCESS ALL PDF FILES
# ============================================================

def process_epfo_files():

    pdf_files = sorted(
        EPFO_RAW_DIR.rglob("*.pdf")
    )

    if not pdf_files:
        print(
            "\nNo EPFO PDF files found."
        )

        print(
            f"Put official EPFO PDF reports inside:\n"
            f"{EPFO_RAW_DIR}"
        )

        return

    all_tables = []

    for pdf_file in pdf_files:

        tables = extract_pdf_tables(
            pdf_file
        )

        print(
            f"Tables found: {len(tables)}"
        )

        payroll_table = find_payroll_table(
            tables
        )

        if payroll_table is None:

            print(
                f"No payroll table detected "
                f"in {pdf_file.name}"
            )

            continue

        normalized = normalize_table(
            payroll_table,
            pdf_file.name
        )

        if normalized is not None:
            all_tables.append(normalized)

    if not all_tables:

        print(
            "\nNo usable EPFO payroll tables found."
        )

        return

    # Combine extracted tables
    combined = pd.concat(
        all_tables,
        ignore_index=True,
        sort=False
    )

    # Remove duplicate rows
    combined = combined.drop_duplicates()

    # Save intermediate extraction
    intermediate_file = (
        OUTPUT_DIR /
        "epfo_extracted_raw.csv"
    )

    combined.to_csv(
        intermediate_file,
        index=False
    )

    print(
        f"\nIntermediate data saved to:"
        f"\n{intermediate_file}"
    )

    print(
        f"Rows extracted: {len(combined)}"
    )

    return combined


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("EPFO EMPLOYMENT DATA COLLECTION")
    print("=" * 60)

    data = process_epfo_files()

    if data is not None:

        print("\nExtraction completed.")

        print("\nColumns detected:")

        for column in data.columns:
            print(f" - {column}")

        print("\nFirst records:")

        print(
            data.head(10).to_string(
                index=False
            )
        )

        print("\nNext step:")
        print(
            "Inspect epfo_extracted_raw.csv "
            "and map the exact EPFO columns."
        )