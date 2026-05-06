"""
data_loader.py

This file code Loads and preprocesses the visitor preference dataset.

"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pandas as pd


SUPPORTED_DATASET_SUFFIXES = {
    ".csv",
    ".tsv",
    ".txt",
    ".xlsx",
    ".xls",
}


def normalize_column_name(column: str) -> str:
    """
    Normalize column names so matching is easier.

    Example:
    "Bucket list destinations Sri Lanka" -> "bucket list destinations sri lanka"
    """
    text = str(column).strip().lower()
    text = text.replace("_", " ")
    text = re.sub(r"\s+", " ", text)
    return text


def auto_find_column(df: pd.DataFrame, required_words: list[str]) -> str | None:
    """
    Find a column by checking whether all required words appear in the column name.

    Example:
    required_words = ["destination"]
    can match:
    - Bucket list destinations Sri Lanka
    - Destinations
    - Bucket List Destination
    """
    for column in df.columns:
        normalized = normalize_column_name(column)

        if all(word.lower() in normalized for word in required_words):
            return column

    return None


def clean_text_item(value: object) -> str:
    """
    Clean one activity or destination value.

    Example:
    "'historical monuments'" -> "Historical Monuments"
    """
    text = str(value).strip()
    text = re.sub(r"^[\"']|[\"']$", "", text)
    text = re.sub(r"\s+", " ", text)

    return text.title()


def parse_list_cell(value: object) -> list[str]:
    """
    Convert a dataset cell into a list.

    Handles values like:
    - ['cycling', 'historical monuments', 'village homestays']
    - cycling, historical monuments, village homestays
    - cycling; historical monuments; village homestays

    This function does not assume any fixed activity or destination names.
    """
    if pd.isna(value):
        return []

    if isinstance(value, list):
        raw_items = value
    else:
        text = str(value).strip()

        if not text:
            return []

        if text.startswith("[") and text.endswith("]"):
            try:
                parsed = ast.literal_eval(text)

                if isinstance(parsed, list):
                    raw_items = parsed
                else:
                    raw_items = [text]

            except (ValueError, SyntaxError):
                raw_items = re.split(r"[,;|]", text)
        else:
            raw_items = re.split(r"[,;|]", text)

    cleaned_items = []
    seen_items = set()

    for item in raw_items:
        cleaned_item = clean_text_item(item)

        if cleaned_item and cleaned_item.lower() not in seen_items:
            cleaned_items.append(cleaned_item)
            seen_items.add(cleaned_item.lower())

    return cleaned_items


def read_dataset_file(dataset_path: str | Path) -> pd.DataFrame:
    """
    Read CSV, TSV, TXT, XLSX, or XLS file.
    """
    dataset_path = Path(dataset_path)
    suffix = dataset_path.suffix.lower()

    if suffix in [".xlsx", ".xls"]:
        return pd.read_excel(dataset_path)

    if suffix in [".csv", ".tsv", ".txt"]:
        return pd.read_csv(dataset_path, sep=None, engine="python")

    raise ValueError(
        f"Unsupported file type: {suffix}. Use .csv, .tsv, .txt, .xlsx, or .xls"
    )


def resolve_dataset_path(dataset_path: str | Path) -> Path:
    """
    Resolve a dataset file path.

    If a directory is provided, auto-select the single supported dataset file
    inside it. This matches the Streamlit and CLI defaults that pass `data`.
    """
    dataset_path = Path(dataset_path)

    if dataset_path.is_dir():
        dataset_files = sorted(
            file_path
            for file_path in dataset_path.iterdir()
            if file_path.is_file()
            and file_path.suffix.lower() in SUPPORTED_DATASET_SUFFIXES
        )

        if not dataset_files:
            raise FileNotFoundError(
                f"No supported dataset files were found in: {dataset_path}. "
                "Add a .csv, .tsv, .txt, .xlsx, or .xls file."
            )

        if len(dataset_files) > 1:
            available_files = ", ".join(file_path.name for file_path in dataset_files)
            raise ValueError(
                f"Multiple dataset files were found in {dataset_path}: "
                f"{available_files}. Please specify the exact file path."
            )

        return dataset_files[0]

    return dataset_path


def load_visitors_dataset(
    dataset_path: str | Path = "data/user_data_version_3_10K_Users.csv",
    max_users: int | None = 500,
    user_id_col: str | None = None,
    name_col: str | None = None,
    email_col: str | None = None,
    activities_col: str | None = None,
    destinations_col: str | None = None,
) -> pd.DataFrame:
    """
    Load and clean the visitors dataset.

    The column names can be passed manually.
    If not passed, the code tries to detect them from the dataset headers.

    This function does not hardcode activity names or destination names.
    """
    dataset_path = resolve_dataset_path(dataset_path)

    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Dataset file not found: {dataset_path}. "
            "Place your CSV/XLSX file inside the data folder."
        )

    df = read_dataset_file(dataset_path)

    # Auto-detect columns only from the headers.
    # This is not hardcoding destination values.
    user_id_col = user_id_col or auto_find_column(df, ["user", "id"])
    name_col = name_col or auto_find_column(df, ["name"])
    email_col = email_col or auto_find_column(df, ["email"])
    activities_col = activities_col or auto_find_column(df, ["activities"])
    destinations_col = destinations_col or auto_find_column(df, ["destination"])

    missing_columns = []

    if user_id_col is None:
        missing_columns.append("User ID")

    if name_col is None:
        missing_columns.append("Name")

    if email_col is None:
        missing_columns.append("Email")

    if activities_col is None:
        missing_columns.append("Preferred Activities")

    if destinations_col is None:
        missing_columns.append("Bucket list destinations Sri Lanka")

    if missing_columns:
        raise ValueError(
            "Could not detect these required columns: "
            + ", ".join(missing_columns)
            + f"\nAvailable columns are: {list(df.columns)}"
        )

    cleaned = pd.DataFrame()

    cleaned["user_id"] = df[user_id_col].astype(str).str.strip()
    cleaned["name"] = df[name_col].astype(str).str.strip()
    cleaned["email"] = df[email_col].astype(str).str.strip()

    # These two lines dynamically parse all activities and destinations.
    cleaned["activities"] = df[activities_col].apply(parse_list_cell)
    cleaned["destinations"] = df[destinations_col].apply(parse_list_cell)

    cleaned = cleaned.dropna(subset=["user_id", "name"])
    cleaned = cleaned.drop_duplicates(subset=["user_id"])

    cleaned = cleaned[
        cleaned["activities"].apply(len).gt(0)
        | cleaned["destinations"].apply(len).gt(0)
    ]

    if max_users is not None:
        cleaned = cleaned.head(max_users)

    return cleaned.reset_index(drop=True)
