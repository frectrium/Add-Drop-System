# Add-Drop System Documentation

A comprehensive guide to the scripts managing the student course add-drop process.

---

## Table of Contents

- [1. `randomizer.py`: Shuffling Registration Data](#1-randomizerpy-shuffling-registration-data)
- [2. `add_and_drop.py`: The Core Add-Drop Algorithm](#2-add_and_droppy-the-core-add-drop-algorithm)
- [3. `verifier.py`: Validating Add-Drop Results](#3-verifierpy-validating-add-drop-results)
- [Summary of the Entire Add-Drop System](#summary-of-the-entire-add-drop-system)
- [Overall Workflow](#overall-workflow)

---

## 1. `randomizer.py`: Shuffling Registration Data

### Purpose
The `randomizer.py` script is designed to shuffle the rows of an Excel file containing student registration data.

### Functionality Overview
- **Load Original Data**: Reads the original registration data from `RegistrationData_Original.xlsx`.
- **Shuffle Rows**: Randomly rearranges the order of the rows to eliminate any inherent ordering biases.
- **Save Shuffled Data**: Writes the shuffled data to `RegistrationData.xlsx`, which will be used as input for the add-drop algorithm.

---

## 2. `add_and_drop.py`: The Core Add-Drop Algorithm

### Purpose
The `add_and_drop.py` script manages student requests to add or drop courses, ensuring that seat allocations are handled efficiently. The algorithm accommodates both **unconditional drops** (dropping a course without a replacement) and **conditional drops** (dropping a course with one or more replacement preferences). Additionally, it handles multiple add requests per student, ensuring that seat assignments do not conflict.

### Functionality Overview
- **Load Data**: Reads elective seat availability from `ElectiveSeats.xlsx` and student registrations from `RegistrationData.xlsx`.
- **Initialize Data Structures**:
    - **Course Capacities**: Tracks available seats per course.
    - **Occupant List**: Represents students’ course assignments and preferences.
- **Process Registrations**:
    - Handle unconditional drops (students dropping courses without replacements).
    - Handle add requests (students requesting to add new courses).
    - Handle conditional drops (students dropping courses with replacement preferences).
- **Seat Allocation Using TTC (Top Trading Cycles)**:
    - Implements the TTC algorithm to assign courses based on student preferences and seat availability.
    - Ensures that allocations are stable and respect students' priorities.
- **Generate Results**: Outputs the final seat assignments and any course drops or additions to `Result.xlsx`.

### Detailed Breakdown

#### 1. Loading Data
- **Elective Seats (`ElectiveSeats.xlsx`)**:
    - **Structure**: Contains a list of courses along with the number of seats available in each.
    - **Process**:
        - Read the Excel file to create a dictionary mapping each course code to its available seats.
        - Initialize a dummy course (`XX111`) with infinite capacity to handle add requests where no real seats are available.

- **Registration Data (`RegistrationData.xlsx`)**:
    - **Structure**: Contains student information, including:
        - Student ID
        - Number of Courses to Add
        - Add Preferences: Columns 6-9 specify desired courses to add.
        - Drop Courses: Columns 10 and 14 specify courses to drop.
        - Replacement Preferences: Columns 11-13 and 15-17 specify replacement courses for each drop.
    - **Process**:
        - Iterate through each student’s registration entry.
        - Extract and standardize course codes using the `extract_course_code` function.
        - Determine the nature of each drop (unconditional or conditional) based on the presence of replacement preferences.
        - For add requests, create occupant records with the specified preferences.

#### 2. Initializing Data Structures
- **Course Capacities**:
    - A dictionary mapping each course code to the number of available seats.
    - The dummy course (`XX111`) is added with infinite capacity to serve as a fallback for add requests when no real seats are available.
- **Occupant List**:
    - A list of dictionaries, each representing an occupant (either a student wanting to add a course or a student dropping a course).
    - Each occupant record contains:
        - **Occupant ID**: A unique identifier.
        - **Student ID**: Identifier linking the occupant to the student.
        - **Original Course**: The course the occupant is currently assigned to (or a dummy course if adding).
        - **Preferences**: An ordered list of desired courses.
        - **Final Course**: The course the occupant is finally assigned to after the algorithm runs.

#### 3. Processing Registrations
- **Unconditional Drops**:
    - **Definition**: A student wishes to drop a course without specifying any replacement.
    - **Handling**:
        - Increase the seat count for the dropped course, making a seat available.
        - Record the drop in a list for result generation.
- **Add Requests**:
    - **Definition**: A student wishes to add one or more courses.
    - **Handling**:
        - For each add request, create an occupant with the specified add preferences.
        - Preferences include desired courses and the dummy course as a fallback.
        - The algorithm ensures that once a course is assigned to a student, it is removed from the preferences of other add occupants for the same student to prevent duplicate assignments.
- **Conditional Drops**:
    - **Definition**: A student wishes to drop a course and specifies one or more replacement courses.
    - **Handling**:
        - Create an occupant with preferences set to the replacement courses.
        - The fallback preference is the original course, meaning if no replacements are available, the student remains enrolled in the original course.
        - These occupants are later processed by the TTC algorithm to potentially swap course assignments based on preferences and seat availability.

#### 4. Seat Allocation Using TTC (Top Trading Cycles) Algorithm
The TTC algorithm is employed to allocate courses to students in a way that respects their preferences and ensures a fair distribution of seats.

- **Core Concepts**:
    - **Occupants**: Represent individual seat requests (either adding or dropping courses).
    - **Preferences**: Each occupant has an ordered list of desired courses.
    - **Cycles**: Groups of occupants and courses that form a closed loop, allowing for mutual exchanges.

- **Algorithm Steps**:
    1. **Initialization**:
        - **Seats Held**: A dictionary tracking how many seats are currently held in each course.
        - **Active Occupants**: A set containing all occupants that have not yet been assigned a final course.
    2. **Iterative Processing**:
        - **Assigning Free Seats**:
            - For each active occupant, check if any of their preferred courses have available seats.
            - If a seat is available, assign the occupant to that course, update seat counts, and remove the occupant from the active set.
            - Additionally, remove the assigned course from the preferences of other occupants from the same student to prevent duplicate assignments.
        - **Finding and Processing Cycles**:
            - If no free seats can be assigned, search for cycles among the occupants' preferences.
            - **Cycle Detection**: Each occupant points to their highest-preference course. A cycle is detected when a group of occupants and courses form a closed loop, allowing for mutual swaps.
            - **Processing a Cycle**: Assign each occupant in the cycle to the next course in the cycle. Update seat counts, remove these occupants from the active set, and remove the assigned courses from the preferences of other occupants from the same student.
        - **Termination**: The algorithm continues iterating until no active occupants remain or no further assignments can be made.

- **Handling Add Requests**:
    - Each add request is treated as an occupant with a preference list that includes desired courses and the dummy course.
    - When an add occupant is assigned a real course, the dummy course is removed from their preferences, ensuring that only one course is added per occupant.
- **Handling Conditional Drops**:
    - Occupants created from conditional drops have preferences set to replacement courses, followed by the original course.
    - If a replacement course is assigned, the occupant is moved to that course; otherwise, they remain in their original course.

#### 5. Generating Results
- **Output File**: `Result.xlsx`
- **Content**:
    - **Unconditional Drops**: Records indicating a student has dropped a course without any replacement.
    - **Add Requests**: Records showing that a student has successfully added a course.
    - **Conditional Drops**: Records showing a student has dropped a course and been assigned a replacement.
- **Process**:
    - Compile all recorded drops and additions into a structured format.
    - Write the compiled data to an Excel file for review.

---

## 3. `verifier.py`: Validating Add-Drop Results

### Purpose
The `verifier.py` script serves as a validation tool to ensure that the results produced by the add-drop algorithm (`add_and_drop.py`) are consistent and accurate.

### Functionality Overview
- **Load Data**: Reads both the original `RegistrationData.xlsx` and the `Result.xlsx` files.
- **Parse Registration Data**: Organizes the registration data into a structured format for easy lookup and comparison.
- **Verify Result Entries**:
    - Ensures that drops and additions in the result file align with the original registration requests.
    - Checks for consistency in course assignments and preference fulfillment.
- **Generate Output**: Reports the verification status of each entry, indicating whether it is correct or contains discrepancies.

---

## Summary of the Entire Add-Drop System

- **Data Preparation with `randomizer.py`**:
    - **Function**: Shuffles the original registration data to eliminate ordering biases.
    - **Purpose**: Ensures the add-drop algorithm is tested against randomized input, simulating real-world unpredictability.
- **Core Processing with `add_and_drop.py`**:
    - **Function**: Processes student add/drop requests and allocates seats based on preferences and availability using the TTC algorithm.
    - **Purpose**: Manages the entire lifecycle of course registrations, ensuring fair and efficient seat assignments.
- **Validation with `verifier.py`**:
    - **Function**: Cross-verifies the results against the original registration data to ensure accuracy.
    - **Purpose**: Acts as a quality control measure to maintain data integrity and trustworthiness of the system.

---

## Overall Workflow

1.  **Initial Data Shuffle**:
    - Run `randomizer.py` to create a randomized version of the registration data (`RegistrationData.xlsx`).
2.  **Execute Add-Drop Algorithm**:
    - Run `add_and_drop.py` using the shuffled `RegistrationData.xlsx` and `ElectiveSeats.xlsx` to generate `Result.xlsx`.
3.  **Verify Results**:
    - Run `verifier.py` to ensure that `Result.xlsx` accurately reflects the original student requests and that all operations were performed correctly.