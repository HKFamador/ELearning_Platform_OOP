import os
import pyodbc
from tabulate import tabulate

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

class Feedback:
    total_feedbacks = 0
    feedback_list = []

    def __init__(self, student, course, rating, comments):
        self.student = student
        self.course = course
        self.rating = rating
        self.comments = comments
        Feedback.total_feedbacks += 1

    def get_feedback_details(self):
        return (f"Rating: {self.rating}/5, Comments: {self.comments}")

    @classmethod
    def class_feedback_method(cls):
        return f"Total Feedbacks: {cls.total_feedbacks}"
    @staticmethod
    def evaluate_instructor():
        conn = get_connection()
        if not conn:
            return
        cursor = conn.cursor()
        try:
            student_id = input(
                "Enter your Student ID: ").strip()

            query = """
            SELECT c.CourseCode, c.CourseName, i.FirstName, i.LastName, i.InstructorID
            FROM Enrollments e
            JOIN Courses c ON e.CourseID = c.CourseID
            LEFT JOIN InsAssignedCourses iac ON c.CourseCode = iac.CourseCode
            LEFT JOIN Instructors i ON iac.InstructorID = i.InstructorID
            WHERE e.StudentID = ?
            """
            cursor.execute(query, (student_id,))
            courses = cursor.fetchall()
            if not courses:
                print("You are not enrolled in any courses.")
                return

            # Display the courses and instructors in a table
            print(f"{'No.':<5} {'Instructor':<25} {'Course Code':<15}{'Course Name':<30}")
            print("=" * 75)
            for idx, course in enumerate(courses, start=1):
                course_code, course_name, first_name, last_name, instructor_id = course
                instructor_name = f"{first_name} {last_name}" if first_name and last_name else "No Instructor"
                print(f"{idx:<5}{instructor_name:<25}{course_code:<15}{course_name:<30}")

            # Ask the user to select a course for evaluation
            while True:
                try:
                    choice = int(input("\nEnter the number corresponding to the Instructor: "))
                    if 1 <= choice <= len(courses):
                        selected_course = courses[choice - 1]
                        break
                    else:
                        print("Invalid choice. Please select a valid number.")
                except ValueError:
                    print("Invalid input. Please enter a number.")

            selected_instructor_id = selected_course[4]
            selected_course_code = selected_course[0]
            selected_instructor_name = f"{selected_course[2]} {selected_course[3]}"

            # Proceed with the evaluation
            print("\nInstructor Evaluation:")
            print("Please rate the instructor on the following criteria (1 to 5):")
            ratings = [
                "Instructor comes punctually and regularly to our class.",
                "Instructor gives enough information about the topic of the subject.",
                "Instructor encourages us to be active participants in our class.",
                "Instructor demonstrates patience, empathy, and understanding in dealing with our concerns.",
                "Instructor makes classwork interesting.",
                "Instructor asks questions to see if we understand what has been taught.",
                "Instructor tells us how to use what we have learned to learn new things.",
                "Instructor gives me feedback about my performance.",
                "Instructor is transparent in giving grades."
            ]

            total_score = 0
            for i, question in enumerate(ratings, start=1):
                while True:
                    try:
                        rating = int(input(f"{i}. {question} (1-5): "))
                        if 1 <= rating <= 5:
                            total_score += rating
                            break
                        else:
                            print("Please enter a rating between 1 and 5.")
                    except ValueError:
                        print("Invalid input. Please enter a number between 1 and 5.")

            comments = input("\nPlease provide a comment about your instructor: ").strip()
            average_rating = total_score / len(ratings)

            # Insert evaluation into the database
            insert_query = """
            INSERT INTO Evaluations (InstructorID, LastName, FirstName, CourseCode, AverageRating, Comments)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            cursor.execute(
                insert_query,
                (
                    selected_instructor_id,
                    selected_course[3],  # Last Name
                    selected_course[2],  # First Name
                    selected_course_code,
                    average_rating,
                    comments
                )
            )
            conn.commit()
            print(f"\nThank you for your feedback!")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def view_instructor_ratings():
        """Allows an instructor to view the ratings and comments provided by students, with anonymous comments."""
        conn = get_connection()
        if not conn:
            print("Failed to connect to the database.")
            return
        cursor = conn.cursor()
        try:
            instructor_id = input("Enter your Instructor ID: ").strip()
            query = """
                SELECT AVG(AverageRating) AS AverageRating, COUNT(*) AS TotalEvaluations
                FROM Evaluations
                WHERE InstructorID = ?
            """
            cursor.execute(query, (instructor_id,))
            result = cursor.fetchone()

            if result:
                average_rating = result[0]
                total_evaluations = result[1]

                if average_rating is not None:
                    print("=" * 74)
                    print(f"Instructor ID: {instructor_id}")
                    print(f"Total Evaluations: {total_evaluations}")
                    print(f"Overall Average Rating: {average_rating:.2f}")

                    # Fetch all comments provided by students
                    cursor.execute("""
                        SELECT e.Comments
                        FROM Evaluations e
                        WHERE e.InstructorID = ?
                    """, (instructor_id,))
                    evaluations = cursor.fetchall()

                    if evaluations:
                        print("\nStudent Comments:")
                        print("-" * 74)

                        # Display only the comments anonymously
                        for evaluation in evaluations:
                            comment = evaluation[0]
                            print(f"{comment}")

                else:
                    print("No evaluations found for this instructor.")
            else:
                print("An error occurred while retrieving ratings.")

        # except Exception as e:
        #     print(f"An error occurred: {e}")
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def feedbacks_or_suggestions():
        comments = input("Please write your comments: ")
        Feedback.feedback_list.append(comments)
        Feedback.save_feedback_to_file()
        print("=== Thank you for your feedback! ===")

    @staticmethod
    def save_feedback_to_file(filename="feedback.txt"):
        with open(filename, "w") as file:
            file.write("\n".join(Feedback.feedback_list))

    @staticmethod
    def load_feedback_from_file(filename="feedback.txt"):
        if os.path.exists(filename):
            with open(filename, "r") as file:
                Feedback.feedback_list = file.read().splitlines()

    @staticmethod
    def view_feedbacks():
        Feedback.load_feedback_from_file()  # Load feedback before viewing
        if not Feedback.feedback_list:
            print("No feedbacks available.")
        else:
            for idx, feedback in enumerate(Feedback.feedback_list, start=1):
                print(f"{idx}. {feedback}")





# import pyodbc
# print(pyodbc.drivers())
