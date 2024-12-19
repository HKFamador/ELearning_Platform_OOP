from datetime import datetime
import pyodbc
def get_connection():
    connection_string = (
        "DRIVER={SQL Server};"
        "SERVER=HANHANNAH-K\\SQLEXPRESS;"
        "DATABASE=E_Learning_Platform;"
        "Trusted_Connection=yes;"
    )
    try:
        conn = pyodbc.connect(connection_string)
        return conn
    except Exception as e:
        print(f"Connection failed: {e}")
        return None

class Assignment:
    def __init__(self, assignment_id, course_code, title, description, due_date):
        self.assignment_id = assignment_id
        self.course_code = course_code
        self.title = title
        self.description = description
        self.due_date = due_date

    def __str__(self):
        return f"Assignment ID: {self.assignment_id}, Title: {self.title}, Course Code: {self.course_code}, Due Date: {self.due_date}"

    @staticmethod
    def create_assignment():
        """Creates an assignment and assigns it to all students in the course."""
        print("\n" + "=" * 28 + " Create and Assign Assignment " + "=" * 28)

        instructor_id = input("Enter your ID:")

        # Getting course details interactively from the instructor
        course_code = input("Enter the course code for the assignment: ")
        title = input("Enter the title of the assignment: ")
        description = input("Enter the description of the assignment: ")
        due_date = input("Enter the due date for the assignment (YYYY-MM-DD): ")

        # Attempting to connect to the database
        conn = get_connection()
        if conn is None:
            print("Failed to connect to the database. Please try again later.")
            return
        try:
            cursor = conn.cursor()

            # First, check if the instructor is assigned to any course
            cursor.execute("""
                        SELECT i.InstructorID, i.FirstName, i.LastName ,e.CourseCode
                        FROM InsAssignedCourses e
                        JOIN Instructors i ON i.InstructorID = e.InstructorID
                        JOIN Courses c ON e.CourseCode = c.CourseCode
                        WHERE c.CourseCode = ? and e.InstructorID = ?
                    """, (course_code,instructor_id))

            instructor = cursor.fetchone()
            if instructor is None:
                print(f"You are not assigned to the course {course_code}.")
                return

            # Insert the new assignment into the database
            cursor.execute("""
                        INSERT INTO Assignments (CourseCode, Title, Description, DueDate)
                        VALUES (?, ?, ?, ?)
                    """, (course_code, title, description, due_date))
            conn.commit()

            print(f"Assignment '{title}' created successfully.")

            # Fetch students enrolled in the course of the assignment
            cursor.execute("""
                        SELECT e.StudentID
                        FROM Enrollments e
                        JOIN Courses c ON e.CourseID = c.CourseID
                        WHERE c.CourseCode = ?
                    """, (course_code,))

            students = cursor.fetchall()
            if not students:
                print(f"No students enrolled in the course {course_code}.")
                return
            print(f"Found {len(students)} students enrolled in the course.")
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def submit_assignment():
        """Allows a student to submit an assignment and view its status."""
        print("\n" + "=" * 28 + " Submit Assignment " + "=" * 28)

        # Get student details
        student_id = input("Enter your Student ID: ")

        # Attempting to connect to the database
        conn = get_connection()
        if conn is None:
            print("Failed to connect to the database. Please try again later.")
            return
        try:
            cursor = conn.cursor()

            # Fetch all assignments available to the student, along with their submission status and submission date
            cursor.execute("""
                SELECT a.AssignmentID, a.Title, 
                       CONVERT(varchar, a.DueDate, 23) AS DueDate,  -- Format to 'YYYY-MM-DD'
                       CASE
                           WHEN s.Status IS NULL THEN 'Not Submitted'
                           ELSE s.Status
                       END AS Status,
                       COALESCE(CONVERT(varchar, s.SubmissionDate, 120), 'N/A') AS SubmissionDate  -- Ensure SubmissionDate is properly formatted
                FROM Assignments a
                JOIN Courses c ON a.CourseCode = c.CourseCode
                JOIN Enrollments e ON e.CourseID = c.CourseID
                LEFT JOIN Submissions s ON s.AssignmentID = a.AssignmentID AND s.StudentID = e.StudentID
                WHERE e.StudentID = ?
            """, (student_id,))
            assignments = cursor.fetchall()

            if not assignments:
                print(f"No assignments found for student ID {student_id}.")
                return

            # Print header with wider columns
            print(f"{'Assignment ID':<15} {'Title':<40} {'Due Date':<15} {'Status':<20} {'Submission Date':<25}")
            print("-" * 120)

            # Display assignments in tabular format
            for assignment in assignments:
                assignment_id, title, due_date, status, submission_date = assignment
                print(f"{assignment_id:<15} {title:<40} {due_date:<15} {status:<20} {submission_date:<25}")

            # Ask the student to select an assignment to submit
            assignment_id = input("\nEnter the assignment ID you want to submit for: ")

            # Check if the assignment exists in the Assignments table
            cursor.execute("""
                SELECT COUNT(*) FROM Assignments WHERE AssignmentID = ?
            """, (assignment_id,))
            assignment_exists = cursor.fetchone()[0]

            if assignment_exists == 0:
                print(f"Assignment with ID {assignment_id} does not exist.")
                return

            # Check if the student has already submitted the assignment
            cursor.execute("""
                SELECT Status FROM Submissions 
                WHERE AssignmentID = ? AND StudentID = ?
            """, (assignment_id, student_id))
            submission = cursor.fetchone()

            if submission:
                if submission[0] == 'Checked':
                    print("You have already submitted and your assignment has been checked.")
                    return
                else:
                    print("You have already submitted this assignment, but it is still pending.")
                    return
            else:
                print("You have not submitted this assignment yet.")  # Display if no submission exists

            # If no previous submission, allow the student to submit
            answer = input("Enter your answer for the assignment: ")
            submission_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Insert the submission into the database
            cursor.execute("""
                INSERT INTO Submissions (StudentID, AssignmentID, Answer, SubmissionDate, Status)
                VALUES (?, ?, ?, ?, 'Pending')
            """, (student_id, assignment_id, answer, submission_date))
            conn.commit()

            print("Assignment submitted successfully. Status is now 'Pending'.")

        finally:
            cursor.close()
            conn.close()


class Grade:
    def __init__(self, student_id, assignment_id, grade_value, feedback):
        self.student_id = student_id
        self.assignment_id = assignment_id
        self.grade_value = grade_value
        self.feedback = feedback

    def __str__(self):
        return f"Student ID: {self.student_id}, Assignment ID: {self.assignment_id}, Grade: {self.grade_value}, Feedback: {self.feedback}"


    @staticmethod
    def grade_assignment():
        print("\n" + "=" * 28 + " Grade Assignment " + "=" * 28)

        # Get instructor details
        instructor_id = input("Enter your Instructor ID: ")

        # Attempting to connect to the database
        conn = get_connection()
        if conn is None:
            print("Failed to connect to the database. Please try again later.")
            return
        try:
            cursor = conn.cursor()

            # Get the course code for the instructor
            course_code = input("Enter the course code for which you want to grade assignments: ")

            # Check if the instructor is assigned to the course
            cursor.execute("""
                SELECT 1
                FROM InsAssignedCourses iac
                JOIN Courses c ON iac.CourseCode = c.CourseCode
                WHERE iac.InstructorID = ? AND c.CourseCode = ?
            """, (instructor_id, course_code))

            if cursor.fetchone() is None:
                print(f"You are not assigned to the course {course_code}.")
                return

            # Fetch all assignments that have been submitted but not yet graded (i.e., Status = 'Pending')
            cursor.execute("""
                SELECT s.SubmissionID, a.AssignmentID, a.Title, s.StudentID, e.FirstName, e.LastName, 
                       s.Answer, s.SubmissionDate, s.Status
                FROM Submissions s
                JOIN Assignments a ON s.AssignmentID = a.AssignmentID
                JOIN Enrollments e ON e.StudentID = s.StudentID
                WHERE s.Status = 'Pending'
            """)
            submissions = cursor.fetchall()

            if not submissions:
                print("No assignments are pending for grading.")
                return

            # Display the assignments and their submissions
            print(
                f"{'Submission ID':<15} {'Assignment ID':<15} {'Title':<35} {'Student Name':<30} {'Submission Date':<20} {'Status':<15}")
            print("-" * 135)

            for submission in submissions:
                submission_id, assignment_id, title, student_id, first_name, last_name, answer, submission_date, status = submission

                if isinstance(submission_date, str):
                    formatted_date = submission_date
                else:
                    formatted_date = submission_date.strftime("%Y-%m-%d")

                print(
                    f"{submission_id:<15} {assignment_id:<15} {title:<35} {first_name + ' ' + last_name:<30} {formatted_date:<20}  {status:<15}")

            # Ask the instructor to select an assignment to grade
            submission_id = input("\nEnter the Submission ID you want to grade: ")

            # Fetch the submission details (answer)
            cursor.execute("""
                SELECT s.Answer 
                FROM Submissions s 
                WHERE s.SubmissionID = ?
            """, (submission_id,))
            answer = cursor.fetchone()

            if not answer:
                print(f"Submission with ID {submission_id} does not exist.")
                return

            print("\nStudent's Answer:")
            print("-" * 50)
            print(answer[0])  # Display the student's answer

            # Get the instructor's grade for the submission (numeric grade)
            grade = float(input("\nEnter the grade for this submission: "))

            # Update the status to 'Checked' and assign the grade
            cursor.execute("""
                UPDATE Submissions
                SET Status = 'Checked', Grade = ?
                WHERE SubmissionID = ?
            """, (grade, submission_id))
            conn.commit()
            print("The assignment has been marked as 'Checked'.")
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def view_my_grades():
        """Allows a student to view their grades for all assignments across all their enrolled courses."""
        print("\n" + "=" * 28 + " View Grades for All Courses " + "=" * 28)

        # Get student details
        student_id = input("Enter your Student ID: ")

        # Attempting to connect to the database
        conn = get_connection()
        if conn is None:
            print("Failed to connect to the database. Please try again later.")
            return

        try:
            cursor = conn.cursor()

            # Fetch all courses the student is enrolled in
            cursor.execute("""
                SELECT DISTINCT c.CourseCode, c.CourseName
                FROM Enrollments e
                JOIN Courses c ON e.CourseID = c.CourseID
                WHERE e.StudentID = ?
            """, (student_id,))
            courses = cursor.fetchall()

            if not courses:
                print(f"No courses found for student ID {student_id}.")
                return

            for course in courses:
                course_code, course_name = course

                # Fetch all assignments for the specific course along with grades
                cursor.execute("""
                    SELECT a.AssignmentID, a.Title, s.Grade, a.DueDate
                    FROM Assignments a
                    LEFT JOIN Submissions s ON a.AssignmentID = s.AssignmentID AND s.StudentID = ?
                    WHERE a.CourseCode = ?
                    ORDER BY a.DueDate
                """, (student_id, course_code))

                assignments = cursor.fetchall()

                if not assignments:
                    print(f"No assignments found for student ID {student_id} in course {course_name}.")
                    continue

                # Display the grades for each assignment in the specified course
                print(f"\nGrades for Course {course_name} ({course_code}):")
                print(f"{'Assignment ID':<15} {'Title':<40} {'Grade':<10} {'Due Date':<15}")
                print("-" * 80)

                total_grade = 0
                num_assignments = 0

                for assignment in assignments:
                    assignment_id, title, grade, due_date = assignment

                    # Format the due date to a readable format (e.g., YYYY-MM-DD)
                    formatted_due_date = due_date.strftime("%Y-%m-%d") if due_date else 'N/A'

                    # If the grade is 'N/A', treat it as 0
                    grade = 0 if grade is None else grade

                    # Display each assignment's grade and due date
                    print(f"{assignment_id:<15} {title:<40} {grade:<10} {formatted_due_date:<15}")

                    total_grade += grade
                    num_assignments += 1

                if num_assignments > 0:
                    average_grade = total_grade / num_assignments
                    print("-" * 80)
                    print(f"Average Grade for {course_name} ({course_code}): {average_grade:.2f}")
                else:
                    print(f"No graded assignments for course {course_name}.")

        finally:
            cursor.close()
            conn.close()

    # @staticmethod
    # def view_student_grades():
    #     """Allows an instructor to view the average grade they have given to students across all assignments."""
    #     print("\n" + "=" * 28 + " View Student Grades " + "=" * 28)
    #
    #     # Get instructor details
    #     instructor_id = input("Enter your Instructor ID: ")
    #
    #     # Attempting to connect to the database
    #     conn = get_connection()
    #     if conn is None:
    #         print("Failed to connect to the database. Please try again later.")
    #         return
    #
    #     try:
    #         cursor = conn.cursor()
    #
    #         # Fetch all courses assigned to the instructor
    #         cursor.execute("""
    #                 SELECT DISTINCT c.CourseCode, s.CourseName
    #                 FROM InsAssignedCourses c
    #                 JOIN Courses s ON c.CourseCode = s.CourseCode
    #                 JOIN Instructors i ON c.InstructorID = i.InstructorID
    #                 WHERE i.InstructorID = ?
    #             """, (instructor_id,))
    #         courses = cursor.fetchall()
    #
    #         if not courses:
    #             print(f"No courses found for instructor ID {instructor_id}.")
    #             return
    #
    #         for course in courses:
    #             course_code, course_name = course
    #
    #             # Fetch all students and their assignment grades in this course
    #             cursor.execute("""
    #                     SELECT e.StudentID, e.FirstName, e.LastName, a.AssignmentID, a.Title, s.Grade
    #                     FROM Enrollments e
    #                     JOIN Submissions s ON e.StudentID = s.StudentID
    #                     JOIN Assignments a ON s.AssignmentID = a.AssignmentID
    #                     WHERE a.CourseCode = ? AND s.Status = 'Checked'
    #                     ORDER BY e.StudentID, a.AssignmentID
    #                 """, (course_code,))
    #             submissions = cursor.fetchall()
    #
    #             if not submissions:
    #                 print(f"No graded assignments for students in course {course_name}.")
    #                 continue
    #
    #             # Initialize a dictionary to calculate total grades for each student
    #             student_grades = {}
    #
    #             for submission in submissions:
    #                 student_id, first_name, last_name, assignment_id, title, grade = submission
    #
    #                 # Initialize student's total grade and assignment count if not already done
    #                 if student_id not in student_grades:
    #                     student_grades[student_id] = {
    #                         'name': f"{first_name} {last_name}",
    #                         'total_grade': 0,
    #                         'num_assignments': 0
    #                     }
    #
    #                 # Add the grade of the current assignment to the student's total grade
    #                 student_grades[student_id]['total_grade'] += grade
    #                 student_grades[student_id]['num_assignments'] += 1
    #
    #             # Display the student's average total grade for each course
    #             print(f"\nGrades for Course {course_name} ({course_code}):")
    #             print(f"{'Student ID':<15} {'Student Name':<30} {'Average Grade':<15}")
    #             print("-" * 60)
    #
    #             for student_id, data in student_grades.items():
    #                 total_grade = data['total_grade']
    #                 num_assignments = data['num_assignments']
    #                 average_grade = total_grade / num_assignments if num_assignments > 0 else 0
    #
    #                 # Display each student's average grade
    #                 print(f"{student_id:<15} {data['name']:<30} {average_grade:.2f}")
    #     finally:
    #         cursor.close()
    #         conn.close()

    @staticmethod
    def view_student_grades():
        """Allows an instructor to view the average grade they have given to students across all assignments."""
        print("\n" + "=" * 28 + " View Student Grades " + "=" * 28)

        # Get instructor details
        instructor_id = input("Enter your Instructor ID: ")

        # Attempting to connect to the database
        conn = get_connection()
        if conn is None:
            print("Failed to connect to the database. Please try again later.")
            return

        try:
            cursor = conn.cursor()

            # Fetch all courses assigned to the instructor
            cursor.execute("""
                SELECT DISTINCT c.CourseCode, c.CourseName
                FROM Courses c
                JOIN InsAssignedCourses iac ON c.CourseCode = iac.CourseCode
                WHERE iac.InstructorID = ?
            """, (instructor_id,))
            courses = cursor.fetchall()

            if not courses:
                print(f"No courses found for instructor ID {instructor_id}.")
                return

            for course in courses:
                course_code, course_name = course

                # Fetch all assignments for the course
                cursor.execute("""
                    SELECT a.AssignmentID, a.Title, a.DueDate
                    FROM Assignments a
                    WHERE a.CourseCode = ?
                    ORDER BY a.DueDate
                """, (course_code,))
                assignments = cursor.fetchall()

                if not assignments:
                    print(f"No assignments found for course {course_name}.")
                    continue

                # Fetch all students enrolled in the course
                cursor.execute("""
                    SELECT e.StudentID, e.FirstName, e.LastName
                    FROM Enrollments e
                    WHERE e.CourseCode = ?
                """, (course_code,))
                students = cursor.fetchall()

                if not students:
                    print(f"No students enrolled in course {course_name}.")
                    continue

                # Initialize a dictionary to calculate total grades for each student
                student_grades = {}

                for student in students:
                    student_id, first_name, last_name = student
                    student_grades[student_id] = {
                        'name': f"{first_name} {last_name}",
                        'total_grade': 0,
                        'num_assignments': 0
                    }
                    # Now, check each assignment to see if the student has submitted it
                    for assignment in assignments:
                        assignment_id, title, due_date = assignment

                        # Check if the student has submitted this assignment
                        cursor.execute("""
                            SELECT s.Grade
                            FROM Submissions s
                            WHERE s.StudentID = ? AND s.AssignmentID = ?
                        """, (student_id, assignment_id))
                        submission = cursor.fetchone()

                        if submission:
                            grade = submission[0]
                            # If the grade is None (i.e., N/A), treat it as 0
                            grade = 0 if grade is None else grade
                        else:
                            # If no submission, treat the grade as 0
                            grade = 0

                        # Add the grade of the current assignment to the student's total grade
                        student_grades[student_id]['total_grade'] += grade
                        student_grades[student_id]['num_assignments'] += 1

                # Display the student's average total grade for each course
                print("_" * 77)
                print(f"\nGrades for Course {course_name} ({course_code}):")
                print(f"{'Student ID':<15} {'Student Name':<30} {'Average Grade':<15}")
                print("-" * 67)

                for student_id, data in student_grades.items():
                    total_grade = data['total_grade']
                    num_assignments = data['num_assignments']
                    average_grade = total_grade / num_assignments if num_assignments > 0 else 0

                    # Display each student's average grade
                    print(f"{student_id:<15} {data['name']:<30} {average_grade:.2f}")
        finally:
            cursor.close()
            conn.close()







