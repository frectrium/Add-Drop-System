import pandas as pd
import os

def load_dataframe(file_path: str) -> pd.DataFrame | None:
    """Loads an Excel file into a pandas DataFrame."""
    try:
        print(f"Loading data from '{file_path}'...")
        df = pd.read_excel(file_path)
        print(f"Successfully loaded {len(df)} rows.")
        return df
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while reading '{file_path}': {e}")
        return None

def save_dataframe(df: pd.DataFrame, file_path: str, index: bool = False):
    """Saves a pandas DataFrame to an Excel file."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        df.to_excel(file_path, index=index)
        print(f"Data successfully saved to '{file_path}'.")
    except Exception as e:
        print(f"Error writing to '{file_path}': {e}")