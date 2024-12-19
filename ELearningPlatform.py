from AssignmentGrade import Assignment, Grade
from courses import Course
from faq import FAQ
from enrollment import Enrollment
from feedback import Feedback
from message import Message
from schedule import Schedule
from abc import ABC, abstractmethod
from datetime import datetime
from tabulate import tabulate
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

class Person(ABC):
    total_persons = 0

    def __init__(self, first_name, last_name, middle_name, email, age, gender, password):
        self.first_name = first_name
        self.last_name = last_name
        self.middle_name = middle_name
        self._email = email
        self._age = age
        self._gender = gender
        self.__address = None
        self.__phone_number = None
        self._password = password
        Person.total_persons += 1

    @abstractmethod
    def get_details(self):
        pass

    def get_first_name(self):
        return self.first_name

    def get_last_name(self):
        return self.last_name

    def get_middle_name(self):
        return self.middle_name

    def get_email(self):
        return self._email

    def get_age(self):
        return self._age

    def get_gender(self):
        return self._gender

    def set_address(self, address):
        self.__address = address

    def get_address(self):
        return self.__address

    def set_phone_number(self, phone_number):
        self.__phone_number = phone_number

    def get_phone_number(self):
        return self.__phone_number

    def check_password(self, password):
        return self._password == password

class Student(Person):
    total_students_count = 0

    def __init__(self, student_id, first_name, last_name, middle_name, username, email, password, age, gender):
        super().__init__(first_name, last_name, middle_name, email, age, gender, password)
        self.__student_id = student_id
        self._username = username
        self._course = []
        self._completed_courses = []
        self.grades = []
        self.enrollment_requests = []
        Student.total_students_count += 1

    def get_student_id(self):
        return self.__student_id

    def get_username(self):
        return self._username

    def get_full_name(self):
        return f"{self.first_name} {self.middle_name or ''} {self.last_name}".strip()

    def enroll(self, course):
        self._course.append(course)
        return Enrollment(self, course)

    def get_details(self):
        conn = get_connection()
        if not conn:
            print("Failed to connect to the database. Please try again later.")
            return

        cursor = conn.cursor()

        try:
            # Query to fetch student details
            query = """
            SELECT StudentID, FirstName, LastName, MiddleName, Username, Email, Age, Gender, StudPass
            FROM Students
            WHERE StudentID = ?
            """
            cursor.execute(query, (self.get_student_id()))
            student_details = cursor.fetchone()

            if not student_details:
                print("Student details not found. Please check your Student ID.")
                return

            # Prepare the data for tabular display
            headers = ["Field", "Value"]
            details_keys = [
                "Student ID",
                "First Name",
                "Last Name",
                "Middle Name",
                "Username",
                "Email",
                "Age",
                "Gender",
                "Password"
            ]
            table_data = list(zip(details_keys, student_details))

            print("\nStudent Details:")
            print(tabulate(table_data, headers=headers, tablefmt="fancy_grid"))
        # except Exception as e:
        #     print(f"An error occurred while retrieving details: {e}")
        finally:
            cursor.close()
            conn.close()

    @classmethod
    def total_students(cls):
        return f"Total Students: {cls.total_students_count}"


    def my_grades(self):
        print("\nMy Grades:")
        if not self.grades:
            return f"{self.get_first_name()} has no grades recorded."
        return "\n".join(str(grade) for grade in self.grades)

    def enrolled_courses_list(self):
        print("\nEnrolled Courses:")
        conn = get_connection()
        if conn is None:
            print("Failed to connect to the database. Please try again later.")
            return
        try:
            cursor = conn.cursor()
            # Query to fetch the enrolled courses, their schedules, and instructor details for the student
            student_id = self.get_student_id()  # Replace with appropriate method to get student ID
            cursor.execute("""
                SELECT c.CourseCode, c.CourseName, s.Day, s.StartTime, s.EndTime, i.FirstName, i.LastName
                FROM Enrollments e
                JOIN Courses c ON e.CourseID = c.CourseID
                LEFT JOIN Schedules s ON c.CourseCode = s.CourseCode
                LEFT JOIN InsAssignedCourses iac ON c.CourseCode = iac.CourseCode
                LEFT JOIN Instructors i ON iac.InstructorID = i.InstructorID
                WHERE e.StudentID = ?
            """, (student_id,))

            enrolled_courses = cursor.fetchall()
            if not enrolled_courses:
                print("You are not enrolled in any courses.")
                return

            header = f"{'Course Code':<15} {'Course Name':<35} {'Instructor':<25} {'Day':<10} {'Start Time':<10} {'End Time':<10}"
            print(header)
            print("-" * len(header))

            # Print each course with schedule details
            for course in enrolled_courses:
                course_code, course_name, day, start_time, end_time, first_name, last_name = course
                instructor_name = f"{first_name} {last_name}" if first_name and last_name else "No Instructor"
                day = day if day else "No Schedule"

                # Convert `start_time` and `end_time` to formatted strings or display "N/A" if null
                start_time = start_time.strftime('%H:%M') if isinstance(start_time, datetime) else start_time or "N/A"
                end_time = end_time.strftime('%H:%M') if isinstance(end_time, datetime) else end_time or "N/A"

                # Print formatted course information
                print(
                    f"{course_code:<15} {course_name:<35} {instructor_name:<25} {day:<10} {start_time:<10} {end_time:<10}")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            cursor.close()
            conn.close()

    def enroll_to_course_req(self):
        print("=== Enrollment Request ===")
        course_code = input("Enter course code: ").strip()
        conn = get_connection()
        if conn is None:
            print("Failed to connect to the database. Please try again later.")
            return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT CourseID, CourseCode, CourseName, Capacity FROM Courses
                WHERE CourseCode = ? 
            """, (course_code))
            course_record = cursor.fetchone()
            if not course_record:
                print("Course not found.")
                return
            course_id, course_code, course_name, capacity = course_record
            cursor.execute("SELECT COUNT(*) FROM Enrollments WHERE CourseId = ?", (course_id,))
            current_enrollment = cursor.fetchone()[0]
            if current_enrollment >= capacity:
                print("Course capacity is full!")
                return

            student_id = self.get_student_id()
            cursor.execute("SELECT 1 FROM Students WHERE StudentID = ?", (student_id,))
            if not cursor.fetchone():
                print(f"Student ID {student_id} does not exist in the Students table.")
                return

            confirmation = input("Do you want to request enrollment? (yes/no): ").strip().lower()
            if confirmation != 'yes':
                print("Enrollment request canceled.")
                return
            cursor.execute("""
                INSERT INTO EnrollmentRequests (StudentID, CourseID, CourseCode, RequestDate)
                VALUES (?, ?, ?, GETDATE())
            """, (student_id, course_id, course_code))
            conn.commit()
            print("Your enrollment request has been sent.")
        # except Exception as e:
        #     print(f"Error processing enrollment request: {e}")
        finally:
            cursor.close()
            conn.close()


    def view_student_messages(self):
        conn = get_connection()
        if conn is None:
            print("Failed to connect to the database. Please try again later.")
            return

        try:
            student_id = self.get_student_id()  # Assuming this method fetches the student's ID
            cursor = conn.cursor()

            # Fetch messages from the Messaging table (Admin messages)
            cursor.execute("""
                SELECT Sender, MessageContent, DateSent
                FROM Messaging
                WHERE RecipientID = ? AND RecipientType = 'Student'
                ORDER BY DateSent DESC
            """, (student_id,))
            admin_messages = cursor.fetchall()

            # Fetch messages from the Messages table (Instructor messages)
            cursor.execute("""
                SELECT i.InstructorID, msg.MessageContent, msg.DateSent
                FROM Messages msg
                JOIN Instructors i ON msg.InstructorID = i.InstructorID
                WHERE msg.StudentID = ?
                ORDER BY msg.DateSent DESC
            """, (student_id,))
            instructor_messages = cursor.fetchall()

            # Combine admin and instructor messages
            all_messages = []

            # Process admin messages
            for message in admin_messages:
                all_messages.append({
                    'sender': f"{message[0]}",
                    'content': message[1],
                    'date_sent': message[2]
                })

            # Process instructor messages
            for message in instructor_messages:
                instructor_id = message[0]
                # Fetch instructor's name
                cursor.execute("""
                    SELECT FirstName, LastName 
                    FROM Instructors 
                    WHERE InstructorID = ?
                """, (instructor_id,))
                instructor_name_row = cursor.fetchone()
                instructor_name = (
                    f"{instructor_name_row[0]} {instructor_name_row[1]}" if instructor_name_row else "Unknown Instructor"
                )

                all_messages.append({
                    'sender': f"Instructor: {instructor_name}",
                    'content': message[1],
                    'date_sent': message[2]
                })

            # If no messages are found
            if not all_messages:
                print(f"No messages found for student with ID: {student_id}")
            else:
                print(f"\n--- Messages for Student ID {student_id} ---")
                print("-" * 85)

                # Sort and display all messages by date
                for message in sorted(all_messages, key=lambda x: x['date_sent'], reverse=True):
                    print(f"Sender: {message['sender']}")
                    print(f"Date Sent: {message['date_sent']}")
                    print(f"Message: {message['content']}")
                    print("-" * 85)

        except Exception as e:
            print(f"An error occurred while retrieving student messages: {e}")
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def student_menu():
        print("\n===== Student Log in: =====")
        input_email = input("Enter your email: ")
        input_pass = input("Enter your password: ")

        connection = get_connection()
        if connection:
            cursor = connection.cursor()
            try:
                # Query to find the student by email and password
                cursor.execute("""
                    SELECT StudentID, FirstName, LastName, MiddleName, Username, Email, Age, Gender, StudPass
                    FROM Students
                    WHERE Email = ? and StudPass = ?
                """, (input_email, input_pass))
                student_record = cursor.fetchone()

                if not student_record:
                    print("Student not found or incorrect password! Please try again.")
                    return

                # If the credentials match, create a Student object
                student = Student(*student_record)

                print(f"\n******Welcome, {student.get_first_name()}!******")

                # Main menu loop
                while True:
                    print("\n===== Student Menu =====")
                    print("1. My Profile")
                    print("2. View All Courses")
                    print("3. Enroll in a Course")
                    print("4. View Enrolled Courses")
                    print("5. Answer Assignments")
                    print("6. My Grades")
                    print("7. My Evaluation")
                    print("8. My Feedback")
                    print("9. View Messages")
                    print("10. View FAQ")
                    print("11. Log out")
                    choice = input("Enter your choice: ")

                    if choice == "1":
                        student.get_details()
                    elif choice == "2":
                        Course.display_all_courses()
                    elif choice == "3":
                        student.enroll_to_course_req()
                    elif choice == "4":
                        student.enrolled_courses_list()
                    elif choice == "5":
                        Assignment.submit_assignment()
                    elif choice == "6":
                        Grade.view_my_grades()
                    elif choice == "7":
                        Feedback.evaluate_instructor()
                    elif choice == "8":
                        Feedback.feedbacks_or_suggestions()
                    elif choice == "9":
                        student.view_student_messages()
                    elif choice == "10":
                        faq = FAQ()
                        faq.view_faqs()
                    elif choice == "11":
                        print("Logging out!....")
                        break
                    else:
                        print("Invalid choice. Please try again!")
            #except Exception as e:
             #   print(f"Error logging in: {e}")
            finally:
                cursor.close()
                connection.close()
        else:
            print("Failed to connect to the database. Please try again later.")


class Instructor(Person):
    total_instructors = 0

    def __init__(self,instructor_id, first_name, last_name, middle_name, email, age, gender, password):
        super().__init__(first_name, last_name, middle_name, email, age, gender, password)
        self.instructor_id = instructor_id
        self.assigned_courses = []
        self._years_of_experience = 0
        self._instructor_type = "Full-Time"
        self.ratings = []
        Instructor.total_instructors += 1
        self.messages = []

    def get_instructor_id(self):
        return self.instructor_id

    def assigned_course(self, course_code):
        #self.assigned_courses.append((course, program))
        return course_code in [course.course_code for course in self.assigned_courses]

    def get_full_name(self):
        return f"{self.first_name} {self.middle_name or ''} {self.last_name}".strip()

    def get_profile(self):
        """Displays the profile information of the instructor in a fancy tabular format."""
        print("\n" + "=" * 6 + " Instructor Profile " + "=" * 7)
        conn = get_connection()
        if conn is None:
            print("Failed to connect to the database. Please try again later.")
            return
        try:
            cursor = conn.cursor()
            # Fetch instructor's details from the database using InstructorID
            cursor.execute("""
                   SELECT InstructorID, FirstName, LastName, MiddleName, Email, Age, Gender, InsPass
                   FROM Instructors
                   WHERE InstructorID = ?
               """, (self.instructor_id,))
            instructor_data = cursor.fetchone()
            if not instructor_data:
                print(f"No profile found for InstructorID {self.instructor_id}.")
                return
            # Prepare data for tabulate
            headers = ["Field", "Information"]
            table = [
                ["Instructor ID", instructor_data[0]],
                ["First Name", instructor_data[1]],
                ["Last Name", instructor_data[2]],
                ["Middle Name", instructor_data[3] if instructor_data[3] else "N/A"],
                ["Email", instructor_data[4]],
                ["Age", instructor_data[5]],
                ["Gender", instructor_data[6]],
                ["Password", instructor_data[7]]  # Be cautious when displaying passwords
            ]
            print(tabulate(table, headers, tablefmt="fancy_grid"))
        except Exception as e:
            print(f"Error retrieving instructor profile: {e}")
        finally:
            cursor.close()
            conn.close()

    def view_assigned_courses(self):
        conn = get_connection()
        if conn is None:
            print("Failed to connect to the database. Please try again later.")
            return
        try:
            cursor = conn.cursor()
            # Retrieve all courses assigned to the instructor, including their schedules (if available)
            cursor.execute("""
                SELECT c.CourseCode, c.CourseName, s.Day, s.StartTime, s.EndTime, i.FirstName, i.LastName
                FROM InsAssignedCourses iac
                JOIN Courses c ON iac.CourseCode = c.CourseCode
                LEFT JOIN Schedules s ON c.CourseCode = s.CourseCode
                LEFT JOIN Instructors i ON iac.InstructorID = i.InstructorID
                WHERE iac.InstructorID = ?
            """, (self.instructor_id,))

            rows = cursor.fetchall()
            if not rows:
                print(f"Instructor {self.first_name} {self.last_name} has no courses assigned or schedules available.")
                return

            # Print header
            header = f"{'Course Code':<15} {'Course Name':<35} {'Instructor':<22} {'Day':<10} {'Start Time':<10} {'End Time':<10}"
            print(header)
            print("-" * len(header))

            # Print each schedule
            for row in rows:
                course_code, course_name, day, start_time, end_time, first_name, last_name = row
                instructor_name = f"{first_name} {last_name}" if first_name and last_name else "No Instructor"
                day = day if day else "No Schedule"

                # Convert start_time and end_time to the correct format if they are not None
                if isinstance(start_time, (datetime, str)):
                    start_time = start_time.strftime('%H:%M') if isinstance(start_time, datetime) else start_time
                else:
                    start_time = "N/A"

                if isinstance(end_time, (datetime, str)):
                    end_time = end_time.strftime('%H:%M') if isinstance(end_time, datetime) else end_time
                else:
                    end_time = "N/A"

                # Print formatted course information
                print(
                    f"{course_code:<15} {course_name:<35} {instructor_name:<22} {day:<10} {start_time:<10} {end_time:<10}")

        except Exception as e:
            print(f"Error viewing assigned courses with schedules: {e}")
        finally:
            cursor.close()
            conn.close()

    def get_details(self):
        return f"Instructor: {self.get_first_name()} {self.get_last_name}, Email: {self.get_email()}, ID: {self.instructor_id}"

    def add_years_of_experience(self, years):
        self._years_of_experience += years

    def view_ratings(self):
        if not self.ratings:
            print("No ratings available.")
        else:
            print("\nInstructor Ratings:")
            for idx, rating in enumerate(self.ratings, start=1):
                print(f"Rating {idx}: {rating['score']} - Comments: {rating['comment']}")
            average = self.calculate_average_rating()
            print(f"Overall Average Rating: {average:.2f}")

    def calculate_average_rating(self):
        if not self.ratings:
            return 0
        total_score = sum(rating['score'] for rating in self.ratings)
        average_score = total_score / len(self.ratings)
        return average_score



    def enroll_students_to_assigned_courses(self):
        print("=== Enroll Students to Assigned Courses ===")
        conn = get_connection()
        if conn is None:
            print("Failed to connect to the database. Please try again later.")
            return
        try:
            cursor = conn.cursor()
            # Fetch the courses assigned to the instructor
            cursor.execute("""
                SELECT c.CourseCode, c.CourseName, c.Capacity, c.CreditUnits
                FROM Courses c
                JOIN InsAssignedCourses ic ON c.CourseCode = ic.CourseCode
                WHERE ic.InstructorID = ?
            """, (self.instructor_id,))
            assigned_courses = cursor.fetchall()

            if not assigned_courses:
                print("You are not assigned to any courses.")
                return

            print("\n=== Your Assigned Courses ===")
            # Print header for assigned courses
            print(f"{'Course Code':<15} {'Course Name':<30} {'Capacity':<10} {'Credit Units':<15}")
            print("-" * 70)
            for course in assigned_courses:
                course_code, course_name, capacity, credit_units = course
                print(f"{course_code:<15} {course_name:<30} {capacity:<10} {credit_units:<15}")

            # Fetch pending enrollment requests for the assigned courses
            print("\n" + "="* 35 +"=== PENDING ENROLLMENT REQUESTS ===" + "="*42 )
            print("-" * 111)
            cursor.execute("""
                SELECT r.EnrollmentReq, s.Username, s.FirstName, s.LastName, c.CourseCode, c.CourseName
                FROM EnrollmentRequests r
                JOIN Students s ON r.StudentID = s.StudentID
                JOIN Courses c ON r.CourseCode = c.CourseCode
                WHERE c.CourseCode IN (SELECT CourseCode FROM InsAssignedCourses WHERE InstructorID = ?)
                  AND r.Status = 'Pending'
            """, (self.instructor_id,))
            requests = cursor.fetchall()

            if not requests:
                print("No pending enrollment requests for your courses.")
                return

            # Print header for pending requests
            print(f"{'Request ID':<12} {'Student Name':<30} {'Username':<20} {'Course Code':<15} {'Course Name':<30}")
            print("-" * 111)
            for req in requests:
                request_id, username, first_name, last_name, course_code, course_name = req
                student_name = f"{first_name} {last_name}"
                print(f"{request_id:<12} {student_name:<30} {username:<20} {course_code:<15} {course_name:<30}")

            # Process a request
            request_id = input(
                "\n\nEnter the Request ID to approve and enroll the student (or press Enter to skip): ").strip()
            if request_id:
                cursor.execute("""
                    SELECT r.EnrollmentReq, r.StudentID, r.CourseID, c.CourseName, c.Capacity
                    FROM EnrollmentRequests r
                    JOIN Courses c ON r.CourseID = c.CourseID
                    WHERE r.EnrollmentReq = ?
                """, (request_id,))
                request = cursor.fetchone()
                if not request:
                    print("Invalid Request ID.")
                else:
                    request_id, student_id, course_id, course_name, capacity = request

                    # Check current enrollment for the course
                    cursor.execute("SELECT COUNT(*) FROM Enrollments WHERE CourseID = ?", (course_id,))
                    current_enrollment = cursor.fetchone()[0]

                    if current_enrollment >= capacity:
                        print(f"Sorry, the course {course_name} is full.")
                    else:
                        # Enroll the student in the course
                        cursor.execute("""
                            INSERT INTO Enrollments (StudentID, CourseID, CourseCode, FirstName, LastName, EnrollmentDate)
                            VALUES (?, ?, ?, ?, ?, Getdate())
                        """, (student_id, course_id, course_code, first_name, last_name))
                        # Update the status of the enrollment request
                        cursor.execute("""
                            UPDATE EnrollmentRequests
                            SET Status = 'Approved'
                            WHERE EnrollmentReq = ?
                        """, (request_id,))
                        conn.commit()
                        print(f"Student successfully enrolled in {course_name}. Request marked as approved.")
        # except Exception as e:
        #     print(f"Error: {e}")
        finally:
            cursor.close()
            conn.close()

    def view_enrolled_students(self):
        print("=== View Enrolled Students in Your Assigned Courses ===")
        conn = get_connection()
        if conn is None:
            print("Failed to connect to the database. Please try again later.")
            return

        try:
            cursor = conn.cursor()

            # Fetch courses assigned to the instructor
            cursor.execute("""
                SELECT c.CourseCode, c.CourseName
                FROM Courses c
                JOIN InsAssignedCourses ic ON c.CourseCode = ic.CourseCode
                WHERE ic.InstructorID = ?
            """, (self.instructor_id,))
            assigned_courses = cursor.fetchall()

            if not assigned_courses:
                print("You have no assigned courses.")
                return

            print(f"Your assigned courses:")
            for course in assigned_courses:
                course_code, course_name = course
                print(f"\n========== Course: {course_name} (Code: {course_code}) ==========")

                # Fetch students enrolled in the course
                cursor.execute("""
                    SELECT s.FirstName, s.LastName, s.Username
                    FROM Enrollments e
                    JOIN Students s ON e.StudentID = s.StudentID
                    WHERE e.CourseCode = ?
                """, (course_code,))
                enrolled_students = cursor.fetchall()

                student_count = len(enrolled_students)
                print(f"  Total Enrolled Students: {student_count}")

                if student_count == 0:
                    print(f"No students enrolled in the course '{course_name}'.")
                else:
                    print(f"Enrolled students in '{course_name}':")
                    # Set a limit to display the first 5 students, for example
                    max_display = 5
                    for index, student in enumerate(enrolled_students[:max_display]):
                        first_name, last_name, username = student
                        print(f"  {index + 1}. {first_name} {last_name} (Username: {username})")

                    # If there are more students than max_display, show a message
                    if student_count > max_display:
                        print(f"  ...and {student_count - max_display} more students.")

                # Add boundaries to separate courses
                print("\n" + "-" * 75)

        except Exception as e:
            print(f"An error occurred while retrieving enrolled students: {e}")
        finally:
            cursor.close()
            conn.close()

    def drop_student_by_instructor(self):
        print("=== Instructor: Drop Student from Course ===")
        conn = get_connection()
        if conn is None:
            print("Failed to connect to the database. Please try again later.")
            return
        try:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT c.CourseCode, c.CourseName
                FROM Courses c
                JOIN InsAssignedCourses ic ON c.CourseCode = ic.CourseCode
                WHERE ic.InstructorID = ?
            """, (self.instructor_id,))
            assigned_courses = cursor.fetchall()
            if not assigned_courses:
                print("You have no assigned courses.")
                return

            print("Your assigned courses:")
            for course in assigned_courses:
                print(f"  - {course[1]} (Code: {course[0]})")

            course_code = input("\nEnter the course code: ").strip()
            course = next((c for c in assigned_courses if c[0] == course_code), None)

            if not course:
                print(f"Error: You are not assigned to the course with code '{course_code}'.")
                return
            # Fetch enrolled students for the course
            cursor.execute("""
                SELECT s.Username, s.FirstName, s.LastName
                FROM Enrollments e
                JOIN Students s ON e.StudentID = s.StudentID
                WHERE e.CourseCode = ?
            """, (course_code,))
            enrolled_students = cursor.fetchall()
            if not enrolled_students:
                print(f"No students are enrolled in the course '{course[1]}'.")
                return
            # Prompt the instructor for the student's username
            student_username = input("Enter the student's username to remove: ").strip()
            student = next((s for s in enrolled_students if s[0] == student_username), None)
            if not student:
                print(f"No student found with username '{student_username}' enrolled in '{course[1]}'.")
                return
            # Remove the student from the course
            cursor.execute("""
                DELETE FROM Enrollments
                WHERE CourseCode = ? AND StudentID = (SELECT StudentID FROM Students WHERE Username = ?)
            """, (course_code, student_username))
            conn.commit()
            print(
                f"Student {student[1]} {student[2]} has been removed from '{course[1]}' (Code: {course_code})."
            )
        except Exception as e:
            print(f"Error: {e}")
        finally:
            cursor.close()
            conn.close()

    def send_message_to_students(self):
        conn = get_connection()
        if conn is None:
            print("Failed to connect to the database. Please try again later.")
            return
        try:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT c.CourseCode, c.CourseName
                FROM Courses c
                JOIN InsAssignedCourses ic ON c.CourseCode = ic.CourseCode
                WHERE ic.InstructorID = ?
            """, (self.instructor_id,))
            assigned_courses = cursor.fetchall()

            if not assigned_courses:
                print("You have no assigned courses.")
                return

            # Display the list of courses
            print("Your assigned courses:")
            for i, course in enumerate(assigned_courses, start=1):
                course_code, course_name = course
                print(f"{i}. {course_name} (Code: {course_code})")

            # Get course selection from the instructor
            course_choice = input("Select a course to send the message (enter course number or '0' for all): ").strip()
            try:
                course_choice = int(course_choice)
            except ValueError:
                print("Invalid input. Please enter a valid course number.")
                return

            if course_choice == 0:
                selected_course = None
            elif 1 <= course_choice <= len(assigned_courses):
                selected_course = assigned_courses[course_choice - 1]
            else:
                print("Invalid course selection.")
                return

            # Get message content
            message_content = input("Enter the message content: ").strip()
            if not message_content:
                print("Message content cannot be empty.")
                return

            if selected_course is None:
                # Send message to all students from all courses
                cursor.execute("""
                    SELECT s.StudentID, s.FirstName, s.LastName
                    FROM Students s
                    JOIN Enrollments e ON s.StudentID = e.StudentID
                    JOIN Courses c ON e.CourseCode = c.CourseCode
                    WHERE c.InstructorID = ?
                """, (self.instructor_id,))
                students = cursor.fetchall()

                if not students:
                    print("No students are enrolled in your courses.")
                    return

                # Send message to all students
                for student in students:
                    student_id, first_name, last_name = student
                    cursor.execute("""
                        INSERT INTO Messages (InstructorID, StudentID, MessageContent, DateSent)
                        VALUES (?, ?, ?, ?)
                    """, (self.instructor_id, student_id, message_content, datetime.now()))
                    print(f"Message sent to {first_name} {last_name} (StudentID: {student_id})")

            else:
                course_code = selected_course[0]
                # Fetch students enrolled in the selected course
                cursor.execute("""
                    SELECT s.StudentID, s.FirstName, s.LastName
                    FROM Students s
                    JOIN Enrollments e ON s.StudentID = e.StudentID
                    WHERE e.CourseCode = ?
                """, (course_code,))
                students = cursor.fetchall()

                if not students:
                    print(f"No students are enrolled in the course '{selected_course[1]}'.")
                    return

                # Display list of students in the selected course
                print(f"Students enrolled in '{selected_course[1]}':")
                for i, student in enumerate(students, start=1):
                    student_id, first_name, last_name = student
                    print(f"{i}. {first_name} {last_name} (ID: {student_id})")

                # Get list of student IDs to send messages to
                selected_students = input(
                    "Enter the numbers of the students you want to send messages to (comma-separated): ")
                selected_student_ids = []
                try:
                    selected_student_ids = [students[int(i) - 1][0] for i in selected_students.split(",") if
                                            i.strip().isdigit()]
                except IndexError:
                    print("Invalid input. Please select valid student numbers.")
                    return

                if not selected_student_ids:
                    print("No valid students selected.")
                    return

                # Send message to selected students
                for student_id in selected_student_ids:
                    cursor.execute("""
                        INSERT INTO Messages (InstructorID, StudentID, MessageContent, DateSent)
                        VALUES (?, ?, ?, ?)
                    """, (self.instructor_id, student_id, message_content, datetime.now()))
                    print(f"Message sent to StudentID {student_id}")

            # Commit the transaction
            conn.commit()
            print("Message(s) successfully sent.")
        # except Exception as e:
        #     print(f"An error occurred while sending the message: {e}")
        finally:
            cursor.close()
            conn.close()

    def view_instructor_messages(self):
        conn = get_connection()
        if conn is None:
            print("Failed to connect to the database. Please try again later.")
            return
        instructor_id = self.get_instructor_id()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT Sender, MessageContent, DateSent
                FROM Messaging
                WHERE RecipientID = ? AND RecipientType = 'Instructor'
                ORDER BY DateSent DESC
            """, (instructor_id,))
            messages = cursor.fetchall()

            if not messages:
                print("No messages found for instructor with ID:", instructor_id)
            else:
                print(f"\n--- Messages for Instructor ID {instructor_id} ---")
                print("-" * 80)
                for message in messages:
                    sender, content, date_sent = message
                    print(f"Sender: {sender}")
                    print(f"Date Sent: {date_sent}")
                    print(f"Message: {content}")
                    print("-" * 80)
        # except Exception as e:
        #     print(f"An error occurred while retrieving instructor messages: {e}")
        finally:
            cursor.close()
            conn.close()

    @classmethod
    def class_instructor_method(cls):
        return f"Total Instructors: {cls.total_instructors}"

    @classmethod
    def instructor_menu(cls):
        print("\n===== Instructor Log in: =====")
        input_id = input("Enter your ID: ").strip()
        input_pass = input("Enter your password: ").strip()

        connection = get_connection()
        if connection:
            cursor = connection.cursor()
            try:
                # Query to find the instructor by ID and password
                cursor.execute("""
                    SELECT InstructorID, FirstName, LastName, MiddleName, Email,Age, Gender, InsPass
                    FROM Instructors
                    WHERE InstructorID = ? AND InsPass = ?
                """, (input_id, input_pass))
                instructor_record = cursor.fetchone()

                if not instructor_record:
                    print("Instructor not found or incorrect password! Please try again.")
                    return

                # If the credentials match, create an Instructor object
                instructor = Instructor(*instructor_record)

                print(f"\n****** Welcome, {instructor.get_first_name()} {instructor.get_last_name()}! ******")

                while True:
                    print("\n===== Instructor Menu =====")
                    print("1. View Profile")
                    print("2. View Assigned Courses w/ Schedule")
                    print("3. Add Student to Your Course")
                    print("4. View Enrolled Students")
                    print("5. Drop Student from Course")
                    print("6. View My Rating")
                    print("7. Write Feedback")
                    print("8. Send a Message")
                    print("9. View Messages")
                    print("10. Post an Assignment")
                    print("11. Assign Grade to a Students")
                    print("12. View Grades of Enrolled Students")
                    print("13. Log Out")
                    choice = input("Enter your choice: ").strip()

                    if choice == "1":
                        instructor.get_profile()
                    elif choice == "2":
                        instructor.view_assigned_courses()
                    elif choice == "3":
                        instructor.enroll_students_to_assigned_courses()
                    elif choice == "4":
                        instructor.view_enrolled_students()
                    elif choice == "5":
                        instructor.drop_student_by_instructor()
                    elif choice == "6":
                        Feedback.view_instructor_ratings()
                    elif choice == "7":
                        Feedback.feedbacks_or_suggestions()
                    elif choice == "8":
                        instructor.send_message_to_students()
                    elif choice == "9":
                        instructor.view_instructor_messages()
                    elif choice == "10":
                        Assignment.create_assignment()
                    elif choice == "11":
                        Grade.grade_assignment()
                    elif choice == "12":
                        Grade.view_student_grades()
                    elif choice == "13":
                        print("Logging out... Goodbye!")
                        break
                    else:
                        print("Invalid choice. Please try again.")
            # except Exception as e:
            #     print(f"Error logging in: {e}")
            finally:
                cursor.close()
                connection.close()
        else:
            print("Failed to connect to the database. Please try again later.")

class Admin(Person):
    school_name = "Yeoreobeun Academy"
    school_mission = "To provide accessible and quality education to all learners, supported by government initiatives."
    school_availability = "Now! Available during designated academic terms and special enrollment periods."
    school_address = "Cheongdam-dong, Gangnam-gu, Seoul 06235, South Korea"
    school_contact = "+82 2-1234-5678"
    school_email = "contact@nationalonlinepublicschool.go.kr"
    total_admins = 0

    def __init__(self, first_name, last_name, middle_name, email, age, gender, username, password):
        super().__init__(first_name, last_name, middle_name, email, age, gender, password)
        self.username = username
        self.students = []
        self.instructors = []
        self.courses = []
        self.admin = Admin
        Admin.total_admins += 1

    @classmethod
    def about_us(cls):
        """Displays information about the school in a fancy tabular format."""
        school_info = [
            ["School Name", cls.school_name],
            ["Mission", cls.school_mission],
            ["Availability", cls.school_availability],
            ["Address", cls.school_address],
            ["Contact Number", cls.school_contact],
            ["Email", cls.school_email],
        ]
        print("\n" + "=" * 50)
        print(f"Welcome to {cls.school_name}")
        print("=" * 50)
        print(tabulate(school_info, headers=["Information", "Details"], tablefmt="fancy_grid"))

    def get_details(self):
        return f"Admin: {self.get_first_name()} {self.get_middle_name()} {self.get_last_name()}, Username: {self.username}"

    def get_username(self):
        return self.username

    def add_student(self, student):
        self.students.append(student)

    def add_instructor(self, instructor):
        self.instructors.append(instructor)

    def add_course(self, course):
        self.courses.append(course)

    def get_platform_details(self):
        return f"Platform has {len(self.students)} students, {len(self.instructors)} instructors, and {len(self.courses)} courses."

    @classmethod
    def class_platform_method(cls):
        return f"Total Admins: {cls.total_admins}"

    def add_student(self):
        print("=== Registration ===")
        conn = get_connection()
        if conn is None:
            print("Failed to connect to the database. Please try again later.")
            return
        try:
            cursor = conn.cursor()

            first_name = input("Enter student first name: ")
            last_name = input("Enter student last name: ")
            middle_name = input("Enter student middle name: ")
            username = input("Enter Student Username: ")
            email = input("Enter student email: ")

            # Validate email format
            if "@" not in email or "." not in email:
                print("Invalid email format.")
                return

            try:
                age = int(input("Enter student age: "))
                if age <= 0:
                    print("Age must be a positive number.")
                    return
            except ValueError:
                print("Invalid input for age. Please enter a number.")
                return

            gender = input("Enter student gender (M/F): ")
            if gender not in ['M', 'F']:
                print("Invalid gender. Please enter 'M' or 'F'.")
                return
            password = input("Enter student password: ")

            # Insert student record into the database
            cursor.execute("""
                INSERT INTO Students ( FirstName, LastName, MiddleName, Username, Email, Age, Gender, StudPass)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (first_name, last_name, middle_name, username, email, age, gender, password))
            conn.commit()
            print(f"Student {first_name} added successfully!")
        except Exception as e:
            print(f"Error inserting data: {e}")
        finally:
            cursor.close()
            conn.close()

    def add_instructor(self):
        print("=== Add Instructor ===")
        instructor_id = input("Enter instructor ID: ").strip()

        # Establish database connection
        conn = get_connection()
        if conn is None:
            print("Failed to connect to the database. Please try again later.")
            return
        try:
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM Instructors WHERE InstructorID = ?", (instructor_id,))
            if cursor.fetchone():
                print(f"Instructor with ID {instructor_id} already exists. Cannot add duplicate.")
                return
            # Collect instructor details
            first_name = input("Enter instructor First Name: ").strip()
            last_name = input("Enter instructor Last Name: ").strip()
            middle_name = input("Enter instructor Middle Name: ").strip()
            email = input("Enter instructor email: ").strip()
            if "@" not in email or "." not in email:
                print("Invalid email format.")
                return
            try:
                age = int(input("Enter instructor age: ").strip())
                if age <= 0:
                    print("Age must be a positive number.")
                    return
            except ValueError:
                print("Invalid age. Please enter a number.")
                return
            gender = input("Enter instructor gender (M/F): ").strip().upper()
            if gender not in ['M', 'F']:
                print("Invalid gender. Please enter 'M' or 'F'.")
                return

            password = input("Enter instructor password: ").strip()

            cursor.execute("""
                INSERT INTO Instructors (InstructorID, FirstName, LastName, MiddleName, Email, Age, Gender, InsPass)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (instructor_id, first_name, last_name, middle_name, email, age, gender, password))
            conn.commit()
            print("Instructor added successfully!")
        # except Exception as e:
        #     print(f"Error adding instructor: {e}")
        finally:
            cursor.close()
            conn.close()

    def drop_student(self):
        print("=== Drop Student from Course ===")
        course_code = input("Enter the course code (e.g., CS101): ").strip()
        student_id = input("Enter the student ID: ").strip()

        conn = get_connection()
        if conn is None:
            print("Failed to connect to the database. Please try again later.")
            return

        try:
            cursor = conn.cursor()
            # Check if the course exists
            cursor.execute("""
                SELECT CourseID, CourseName FROM Courses
                WHERE CourseCode = ?
            """, (course_code,))
            course_record = cursor.fetchone()

            if not course_record:
                print(f"No course found with the code {course_code}.")
                return
            course_id, course_name = course_record
            # Check if the student exists and is enrolled in the course
            cursor.execute("""
                SELECT E.StudentID, S.FirstName, S.LastName FROM Enrollments E
                INNER JOIN Students S ON E.StudentID = S.StudentID
                WHERE E.CourseID = ? AND S.StudentID = ?
            """, (course_id, student_id))
            student_record = cursor.fetchone()

            if not student_record:
                print(f"No student found with ID {student_id} enrolled in {course_name}.")
                return
            student_id, first_name, last_name = student_record
            cursor.execute("""
                DELETE FROM Enrollments
                WHERE CourseID = ? AND StudentID = ?
            """, (course_id, student_id))
            conn.commit()
            print(f"Student {first_name} {last_name} has been removed from {course_name}.")
        # except Exception as e:
        #     print(f"Error dropping student from course: {e}")
        finally:
            cursor.close()
            conn.close()

    def assign_course_to_instructor(self):
        print("=== Assign Instructor to Courses ===")
        instructor_id = input("Enter instructor ID: ").strip()
        conn = get_connection()

        if conn is None:
            print("Failed to connect to the database. Please try again later.")
            return

        try:
            cursor = conn.cursor()

            # Verify if the instructor exists in the Instructors table
            cursor.execute("SELECT * FROM Instructors WHERE InstructorID = ?", (instructor_id,))
            instructor_record = cursor.fetchone()

            if not instructor_record:
                print("Instructor not found!")
                return

            # Ask for the number of courses to assign
            quantity = int(input("Enter the number of courses to handle: ").strip())

            if quantity <= 0:
                print("Please enter a valid number greater than zero.")
                return

            # Loop to add course codes for the instructor
            for _ in range(quantity):
                course_code = input("Enter course code: ").strip()
                cursor.execute("SELECT * FROM Courses WHERE CourseCode = ?", (course_code,))
                course_record = cursor.fetchone()

                if not course_record:
                    print(f"Course with code {course_code} not found! Skipping...")
                    continue

                # Check if the instructor is already assigned to the course
                cursor.execute("SELECT * FROM InsAssignedCourses WHERE InstructorID = ? AND CourseCode = ?",
                               (instructor_id, course_code))
                existing_assignment = cursor.fetchone()

                if existing_assignment:
                    print(f"Instructor {instructor_id} is already assigned to Course {course_code}.")
                    continue

                try:
                    cursor.execute("""
                        INSERT INTO InsAssignedCourses (InstructorID, CourseCode)
                        VALUES (?, ?)
                    """, (instructor_id, course_code))
                    conn.commit()
                    print(f"Course {course_code} assigned to instructor {instructor_id} successfully.")

                except Exception as e:
                    print(f"Error assigning course {course_code} to instructor: {e}")

        except ValueError:
            print("Invalid number. Please enter a valid integer.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        finally:
            cursor.close()
            conn.close()

    def remove_instructor(self):
        print("=== Admin: Remove Instructor ===")
        conn = get_connection()
        if conn is None:
            print("Failed to connect to the database. Please try again later.")
            return
        try:
            cursor = conn.cursor()
            instructor_id = input("Enter the ID of the instructor to remove: ").strip()
            # Check if the instructor exists in the Instructors table
            cursor.execute("SELECT * FROM Instructors WHERE InstructorID = ?", (instructor_id,))
            instructor_record = cursor.fetchone()
            if not instructor_record:
                print("Instructor not found!")
                return
            # Display instructor details for confirmation
            first_name, last_name = instructor_record[1], instructor_record[2]
            print(f"Are you sure you want to remove the instructor: {first_name} {last_name} (ID: {instructor_id})?")
            confirmation = input("Type 'YES' to confirm: ").strip().upper()

            if confirmation != 'YES':
                print("Operation cancelled.")
                return

            # Remove all course assignments for the instructor first
            cursor.execute("DELETE FROM InsAssignedCourses WHERE InstructorID = ?", (instructor_id,))
            conn.commit()
            print(f"All course assignments for instructor {instructor_id} have been removed.")

            # Delete the instructor
            cursor.execute("DELETE FROM Instructors WHERE InstructorID = ?", (instructor_id,))
            conn.commit()
            print(f"Instructor {instructor_id} has been successfully removed.")
        except Exception as e:
            print(f"Error removing instructor: {e}")
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def view_all_records():
        print("=== Display Selected Entities (Students, Instructors, or Courses) ===")
        conn = get_connection()
        if conn is None:
            print("Failed to connect to the database. Please try again later.")
            return

        try:
            cursor = conn.cursor()
            # Ask the user for their choice
            choice = input("What would you like to see? (1. students, 2. instructors, 3. courses): ").strip().lower()

            if choice == "1":
                # Display all students
                cursor.execute("SELECT StudentID, FirstName, LastName, Email FROM Students")
                students = cursor.fetchall()
                print("\n--- Students ---")
                if not students:
                    print("No students found.")
                else:
                    print(f"{'Student ID':<15} {'First Name':<20} {'Last Name':<20} {'Email':<30}")
                    print("-" * 85)
                    for student in students:
                        student_id, first_name, last_name, email = student
                        print(f"{student_id:<15} {first_name:<20} {last_name:<20} {email:<30}")

            elif choice == "2":
                # Display all instructors
                cursor.execute("SELECT InstructorID, FirstName, LastName, Email FROM Instructors")
                instructors = cursor.fetchall()
                print("\n--- Instructors ---")
                if not instructors:
                    print("No instructors found.")
                else:
                    print(f"{'Instructor ID':<15} {'First Name':<20} {'Last Name':<20} {'Email':<30}")
                    print("-" * 85)
                    for instructor in instructors:
                        instructor_id, first_name, last_name, email = instructor
                        print(f"{instructor_id:<15} {first_name:<20} {last_name:<20} {email:<30}")

            elif choice == "3":
                # Display all courses
                cursor.execute("SELECT CourseCode, CourseName, Capacity, CreditUnits FROM Courses")
                courses = cursor.fetchall()
                print("\n--- Courses ---")
                if not courses:
                    print("No courses found.")
                else:
                    print(f"{'Course Code':<15} {'Course Name':<35} {'Capacity':<15} {'Credit Units':<15}")
                    print("-" * 85)
                    for course in courses:
                        course_code, course_name, capacity, credit_units = course
                        print(f"{course_code:<15} {course_name:<35} {capacity:<15} {credit_units:<15}")
            else:
                print("Invalid choice. Please enter '1', '2', or '3'.")

        except Exception as e:
            print(f"Error displaying entities: {e}")
        finally:
            cursor.close()
            conn.close()


    def admin_login(self, admin):
        admin_username = input("Enter admin username: ")
        admin_pass = input("Enter admin password: ")

        # Compare with the stored admin credentials
        if admin_username == admin.get_username() and admin_pass == admin._password:
            print(f"\n******Welcome, Admin!******")
        else:
            print("Incorrect username or password!")
            return

        while True:
            print("\n===== Admin Menu =====")
            print("1. Add Instructor")
            print("2. Add Course")
            print("3. Display All Data")
            print("4. Assign Instructor to Course")
            print("5. Enroll student to Course")
            print("6. View Enrolled Students")
            print("7. Drop Student from Course")
            print("8. Remove Instructor from Assigned Course")
            print("9. Remove Instructor")
            print("10. Send Message to Student/Instructor")
            print("11. Create Schedule")
            print("12. View All Courses with Schedule ")
            print("13. Exit")
            choice = input("Enter your choice: ")

            if choice == "1":
                self.add_instructor()
            elif choice == "2":
                Course.add_course()
            elif choice == "3":
                self.view_all_records()
            elif choice == "4":
                self.assign_course_to_instructor()
            elif choice == "5":
                Enrollment.enroll_students_as_admin()
            elif choice == "6":
                Enrollment.view_enrolled_students()
            elif choice == "7":
                self.drop_student()
            elif choice == "8":
                Course.remove_assigned_course()
            elif choice == "9":
                self.remove_instructor()
            elif choice == "10":
                Message.send_message()
            elif choice == "11":
                Schedule.create_schedule()
            elif choice == "12":
                Schedule.display_all_schedules()
            elif choice == "13":
                print("Exiting Admin Menu.")
                break
            else:
                print("Invalid choice. Please try again!")


if __name__ == "__main__":
    admin = Admin("Yeji", "Hwang", "Yoon", "yj@gmail.com", 24, "F", "admin","adminpass")

    def main():
        while True:
            print("\n===== Main Menu =====")
            print("1. Register")
            print("2. Student Login")
            print("3. Instructor Login")
            print("4. Admin Login")
            print("5. About Us")
            print("6. View Feedbacks")
            print("7. Exit")
            choice = input("Enter your choice: ")

            if choice == "1":
                admin.add_student()
            elif choice == "2":
                Student.student_menu()
            elif choice == "3":
                Instructor.instructor_menu()
            elif choice == "4":
                admin.admin_login(admin)
            elif choice == "5":
                admin.about_us()
            elif choice == "6":
                Feedback.view_feedbacks()
            elif choice == "7":
                print("Exiting platform.")
                break
            else:
                print("Invalid choice. Please try again!")
    main()


