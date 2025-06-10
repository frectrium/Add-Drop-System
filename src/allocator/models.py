from dataclasses import dataclass, field
from typing import List, Dict

# A special constant to represent a student who is not currently holding a real course
# (i.e., they are making a pure 'add' request).
DUMMY_COURSE_CODE = "XX111"

@dataclass
class Course:
    """Represents an elective course with a seat capacity."""
    code: str
    capacity: int
    seats_held: int = 0

    def has_free_seat(self) -> bool:
        return self.seats_held < self.capacity

@dataclass
class Occupant:
    """Represents a request (an agent) in the TTC algorithm."""
    occupant_id: int
    student_id: str
    original_course: str  # The course they currently hold (or DUMMY_COURSE_CODE)
    preferences: List[str]
    final_course: str = None

@dataclass
class Registration:
    """Represents a single student's full add/drop request from one row."""
    student_id: str
    add_requests: int
    add_preferences: List[str]
    # Each tuple is (course_to_drop, [replacement_prefs])
    drop_requests: List[tuple[str, List[str]]]

    def get_unconditional_drops(self) -> List[str]:
        """Returns drops that have no replacement preferences."""
        return [drop_code for drop_code, repls in self.drop_requests if not repls]

    def get_conditional_drops(self) -> List[tuple[str, List[str]]]:
        """Returns drops that have replacement preferences."""
        return [item for item in self.drop_requests if item[1]]