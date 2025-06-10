import pandas as pd
from typing import List, Dict, Set
from src.utils.helpers import extract_course_code

class ResultVerifier:
    """
    Verifies the output of the allocation algorithm against the original registration data.
    """
    def __init__(self, registration_df: pd.DataFrame, result_df: pd.DataFrame):
        self._result_df = result_df
        self._student_requests = self._parse_student_requests(registration_df)
        self.discrepancies: List[str] = []

    def _parse_student_requests(self, df: pd.DataFrame) -> Dict[str, Dict[str, Set]]:
        """Parses registration data into a lookup structure for easy verification."""
        reg_info = {}
        for _, row in df.iterrows():
            student_id = str(row.iloc[2]).strip().upper()
            if student_id not in reg_info:
                reg_info[student_id] = {"drops": set(), "adds": set()}

            # Gather all possible courses a student might drop
            for i in range(3):
                drop_col = 10 + (i * 4)
                course = extract_course_code(row.iloc[drop_col])
                if course != 'N/A':
                    reg_info[student_id]["drops"].add(course)
            
            # Gather all possible courses a student might be assigned
            add_prefs = {extract_course_code(row.iloc[c]) for c in range(6, 10)}
            repl_prefs1 = {extract_course_code(row.iloc[c]) for c in range(11, 14)}
            repl_prefs2 = {extract_course_code(row.iloc[c]) for c in range(15, 18)}
            repl_prefs3 = {extract_course_code(row.iloc[c]) for c in range(19, 22)}
            
            all_adds = add_prefs.union(repl_prefs1, repl_prefs2, repl_prefs3)
            all_adds.discard('N/A')
            reg_info[student_id]["adds"].update(all_adds)

        return reg_info

    def verify(self) -> bool:
        """
        Runs all verification checks and populates the discrepancies list.
        Returns True if no discrepancies are found, otherwise False.
        """
        if self._result_df is None:
            self.discrepancies.append("Result file could not be read. Verification aborted.")
            return False

        for row_idx, row in self._result_df.iterrows():
            student_id = str(row.get("Student ID", "")).strip().upper()
            dropped = str(row.get("Dropped Course", "")).strip().upper()
            added = str(row.get("Replacement Course", "")).strip().upper()
            
            if not student_id: continue

            if student_id not in self._student_requests:
                self.discrepancies.append(f"Row {row_idx+2}: Student {student_id} not found in registration data.")
                continue

            student_info = self._student_requests[student_id]

            # Check if the dropped course was valid
            if dropped and dropped != "NAN":
                if dropped not in student_info["drops"]:
                    self.discrepancies.append(
                        f"Row {row_idx+2}: Student {student_id} dropped '{dropped}', but this was not a specified drop."
                    )
            
            # Check if the added/replacement course was valid
            if added and added != "NAN":
                if added not in student_info["adds"]:
                     self.discrepancies.append(
                        f"Row {row_idx+2}: Student {student_id} was assigned '{added}', but this was not in their preferences."
                    )

        return not self.discrepancies

    def report(self):
        """Prints a summary of the verification results."""
        if self.discrepancies:
            print("\nVerification found the following discrepancies:")
            for d in self.discrepancies:
                print(f"  - {d}")
        else:
            print("\nVerification complete. All result entries appear to be valid.")