import pandas as pd
from typing import List, Dict, Set, Tuple

from .models import Course, Occupant, Registration, DUMMY_COURSE_CODE
from src.utils.helpers import extract_course_code, is_no_course

class AddDropProcessor:
    """
    Manages the entire course allocation process using a Top Trading Cycles (TTC) algorithm.
    """
    def __init__(self, courses_df: pd.DataFrame, registrations_df: pd.DataFrame):
        self._courses: Dict[str, Course] = self._load_courses(courses_df)
        self._registrations: List[Registration] = self._parse_registrations(registrations_df)
        self._occupants: List[Occupant] = []
        self._unconditional_drops: List[Tuple[str, str]] = []
        self._occupant_id_counter = 0

    def _load_courses(self, df: pd.DataFrame) -> Dict[str, Course]:
        """Loads course data from a DataFrame into a dictionary of Course objects."""
        courses = {}
        for _, row in df.iterrows():
            code = extract_course_code(row.iloc[0])
            try:
                seats = int(row.iloc[1])
            except (ValueError, TypeError):
                print(f"Warning: Invalid seat number for course '{code}'. Defaulting to 0.")
                seats = 0
            if code != 'N/A':
                courses[code] = Course(code=code, capacity=seats)
        
        # Add a dummy course with infinite capacity for handling pure 'add' requests.
        courses[DUMMY_COURSE_CODE] = Course(code=DUMMY_COURSE_CODE, capacity=float('inf'))
        print(f"\nLoaded {len(courses)-1} courses.")
        return courses

    def _parse_registrations(self, df: pd.DataFrame) -> List[Registration]:
        """Parses the registration DataFrame into a list of Registration objects."""
        registrations = []
        for _, row in df.iterrows():
            student_id = str(row.iloc[2])
            
            # Add requests
            try:
                num_adds = int(row.iloc[5])
            except (ValueError, TypeError):
                num_adds = 0
            add_prefs = [extract_course_code(row.iloc[c]) for c in range(6, 10)]
            add_prefs = [c for c in add_prefs if not is_no_course(c)]

            # Drop requests
            drop_requests = []
            for i in range(3): # Loop for Drop #1, Drop #2, Drop #3
                drop_col_start = 10 + (i * 4)
                drop_course = extract_course_code(row.iloc[drop_col_start])
                if not is_no_course(drop_course):
                    repl_prefs = [extract_course_code(row.iloc[c]) for c in range(drop_col_start + 1, drop_col_start + 4)]
                    repl_prefs = [c for c in repl_prefs if not is_no_course(c)]
                    drop_requests.append((drop_course, repl_prefs))

            registrations.append(Registration(
                student_id=student_id,
                add_requests=num_adds,
                add_preferences=add_prefs,
                drop_requests=drop_requests
            ))
        print(f"Parsed {len(registrations)} registration entries.")
        return registrations

    def _create_occupant(self, student_id: str, original_course: str, preferences: List[str]) -> Occupant:
        """Factory method for creating a new Occupant and incrementing the ID."""
        occ = Occupant(self._occupant_id_counter, student_id, original_course, preferences)
        self._occupant_id_counter += 1
        return occ

    def _prepare_for_ttc(self):
        """Initializes the state before running the TTC algorithm."""
        # 1. Handle unconditional drops (these happen before TTC)
        for reg in self._registrations:
            for dropped_course in reg.get_unconditional_drops():
                if dropped_course in self._courses:
                    self._courses[dropped_course].capacity += 1
                    self._unconditional_drops.append((reg.student_id, dropped_course))
                    print(f"Unconditional Drop: Student {reg.student_id} dropped {dropped_course}.")
                else:
                    print(f"Warning: Student {reg.student_id} tried to drop non-existent course '{dropped_course}'.")

        # 2. Create occupants for all other requests
        for reg in self._registrations:
            # Create occupants for 'add' requests
            for _ in range(reg.add_requests):
                prefs = reg.add_preferences.copy()
                prefs.append(DUMMY_COURSE_CODE) # Fallback is to get no course
                self._occupants.append(self._create_occupant(reg.student_id, DUMMY_COURSE_CODE, prefs))

            # Create occupants for conditional drops
            for drop_code, repl_prefs in reg.get_conditional_drops():
                prefs = repl_prefs.copy()
                prefs.append(drop_code) # Fallback is to keep the original course
                self._occupants.append(self._create_occupant(reg.student_id, drop_code, prefs))

        # 3. Set initial seats_held based on occupants' original courses
        for occ in self._occupants:
            if occ.original_course in self._courses:
                self._courses[occ.original_course].seats_held += 1
        
        print(f"\nCreated {len(self._occupants)} occupants for TTC.")

    def _get_outgoing_edge(self, occupant: Occupant, active_occupants: Dict[int, Occupant]) -> Tuple[int | None, str]:
        """Finds the top preference for an occupant, returning the target occupant and course."""
        for pref_course_code in occupant.preferences:
            if pref_course_code not in self._courses:
                continue

            course = self._courses[pref_course_code]
            if course.has_free_seat():
                return (None, course.code) # Points to a free seat

            # Course is full, find who holds it
            for other_occ in active_occupants.values():
                if other_occ.original_course == course.code:
                    return (other_occ.occupant_id, course.code)
        
        # No improvement possible, points to self
        return (occupant.occupant_id, occupant.original_course)


    def run(self) -> pd.DataFrame:
        """Executes the entire add-drop process and returns the results."""
        self._prepare_for_ttc()
        
        active_occupants = {o.occupant_id: o for o in self._occupants}
        iteration = 1

        while active_occupants:
            print(f"\n--- TTC Iteration {iteration} (Active: {len(active_occupants)}) ---")
            iteration += 1
            
            # Phase 1: Point to top choices and find cycles/sinks
            edges = {oid: self._get_outgoing_edge(occ, active_occupants) for oid, occ in active_occupants.items()}
            
            # Find all occupants pointing to a free seat (sinks)
            sinks = {oid for oid, (target_oid, _) in edges.items() if target_oid is None}
            
            # Find cycles
            cycles = self._find_cycles(edges, active_occupants.keys())

            if not sinks and not cycles:
                print("No more assignments possible. Ending TTC.")
                break

            # Phase 2: Resolve sinks and cycles
            resolved_ids = set()

            # Resolve sinks first (direct assignment to free seats)
            if sinks:
                for occ_id in sinks:
                    occupant = active_occupants[occ_id]
                    _, target_course = edges[occ_id]
                    self._assign_course(occupant, target_course, active_occupants)
                    resolved_ids.add(occ_id)
                print(f"Resolved {len(sinks)} occupants via free seats.")
            
            # Resolve cycles
            if cycles:
                for cycle in cycles:
                    for occ_id in cycle:
                        occupant = active_occupants[occ_id]
                        _, target_course = edges[occ_id]
                        self._assign_course(occupant, target_course, active_occupants)
                        resolved_ids.add(occ_id)
                    print(f"Resolved cycle of size {len(cycle)}: {cycle}")
            
            # Remove resolved occupants from the active pool
            for occ_id in resolved_ids:
                if occ_id in active_occupants:
                    del active_occupants[occ_id]

        return self._generate_result_df()

    def _assign_course(self, occupant: Occupant, new_course_code: str, active_occupants: Dict[int, Occupant]):
        """Finalizes a course assignment for an occupant and updates system state."""
        occupant.final_course = new_course_code
        
        old_course_code = occupant.original_course
        
        # Update seat counts
        if old_course_code in self._courses:
            self._courses[old_course_code].seats_held -= 1
        if new_course_code in self._courses:
            self._courses[new_course_code].seats_held += 1

        print(f"  Assignment: Student {occupant.student_id} (OccID {occupant.occupant_id}) -> {new_course_code}")

        # If a student gets a course, remove that course from the preferences of their other occupants
        if new_course_code != DUMMY_COURSE_CODE:
            for other_occ in active_occupants.values():
                if other_occ.student_id == occupant.student_id and other_occ.occupant_id != occupant.occupant_id:
                    if new_course_code in other_occ.preferences:
                        other_occ.preferences.remove(new_course_code)

    def _find_cycles(self, edges: Dict, nodes: Set[int]) -> List[List[int]]:
        """Finds all cycles in the graph defined by the edges."""
        all_cycles = []
        visited = set()
        for node in nodes:
            if node in visited:
                continue
            
            path = []
            curr = node
            while curr is not None and curr not in visited:
                visited.add(curr)
                path.append(curr)
                curr, _ = edges.get(curr, (None, None))

            if curr in path:
                cycle_start_index = path.index(curr)
                all_cycles.append(path[cycle_start_index:])
        return all_cycles

    def _generate_result_df(self) -> pd.DataFrame:
        """Compiles the final results into a DataFrame."""
        result_rows = []

        # Add unconditional drops
        for student_id, dropped_course in self._unconditional_drops:
            result_rows.append([student_id, dropped_course, ""])

        # Add results from TTC
        for occ in self._occupants:
            final_course = occ.final_course if occ.final_course is not None else occ.original_course
            
            is_add_request = (occ.original_course == DUMMY_COURSE_CODE)
            is_successful_change = (final_course != occ.original_course)

            if is_add_request and final_course != DUMMY_COURSE_CODE:
                # Successful add
                result_rows.append([occ.student_id, "", final_course])
            elif not is_add_request and is_successful_change:
                # Successful conditional drop/swap
                result_rows.append([occ.student_id, occ.original_course, final_course])
        
        return pd.DataFrame(result_rows, columns=["Student ID", "Dropped Course", "Replacement Course"])