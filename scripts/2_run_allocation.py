import sys
import os

# Adjust path to import from the src directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.utils.file_io import load_dataframe, save_dataframe
from src.allocator.processor import AddDropProcessor

def main():
    """
    Main function to run the course allocation algorithm.
    """
    seats_file = "data/input/ElectiveSeats.xlsx"
    registration_file = "data/input/RegistrationData.xlsx"
    output_file = "data/output/Result.xlsx"
    
    print("--- Starting Course Allocation Process ---")
    
    df_seats = load_dataframe(seats_file)
    df_reg = load_dataframe(registration_file)

    if df_seats is None or df_reg is None:
        print("Could not load necessary files. Aborting.")
        return

    # Initialize and run the processor
    processor = AddDropProcessor(courses_df=df_seats, registrations_df=df_reg)
    result_df = processor.run()
    
    # Save the results
    save_dataframe(result_df, output_file)
    
    print("\n--- Course Allocation Process Completed ---")

if __name__ == "__main__":
    main()