import pandas as pd

def extract_course_code(val: any) -> str:
    """
    Extracts the first five characters of the course code in uppercase.
    Returns 'N/A' for blank or NaN values.
    """
    if pd.isna(val):
        return 'N/A'
    val_str = str(val).strip().upper()
    return val_str[:5] if val_str else 'N/A'

def is_no_course(val: str) -> bool:
    """
    Returns True if the value represents "no course".
    Unifies various forms like "N/A", "N/A N", and empty strings.
    """
    return val in ['N/A', 'N/A N', '']