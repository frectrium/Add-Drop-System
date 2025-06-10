import sys
import os

# Adjust path to import from the src directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.utils.file_io import load_dataframe
from src.verifier.verifier import ResultVerifier

def main():
    """
    Main function to verify the results of the allocation.
    """
    registration_file = "data/input/RegistrationData.xlsx"
    result_file = "data/output/Result.xlsx"
    
    print("\n--- Starting Verification Process ---")
    
    df_reg = load_dataframe(registration_file)
    df_result = load_dataframe(result_file)

    if df_reg is None or df_result is None:
        print("Could not load necessary files for verification. Aborting.")
        return
        
    verifier = ResultVerifier(registration_df=df_reg, result_df=df_result)
    
    if verifier.verify():
        print("\nVerification successful!")
    
    verifier.report()
    print("\n--- Verification Process Completed ---")

if __name__ == "__main__":
    main()