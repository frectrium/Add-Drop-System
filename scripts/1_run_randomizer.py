import pandas as pd
import sys
import os

# Adjust path to import from the src directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.utils.file_io import load_dataframe, save_dataframe

def main():
    """
    Main function to shuffle the original registration data.
    """
    input_file = "data/input/RegistrationData_Original.xlsx"
    output_file = "data/input/RegistrationData.xlsx"

    print("--- Starting Registration Data Randomization ---")
    
    df = load_dataframe(input_file)
    if df is None or df.empty:
        print("Input file is empty or could not be read. Aborting.")
        return

    # Shuffle the DataFrame rows and reset the index
    df_randomized = df.sample(frac=1).reset_index(drop=True)
    
    save_dataframe(df_randomized, output_file)
    print("\nRandomization process completed successfully.")
    print(f"Shuffled data saved to '{output_file}'")

if __name__ == "__main__":
    main()