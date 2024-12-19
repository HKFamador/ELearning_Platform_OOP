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

class Course:
    total_courses = 0
    all_courses = []

    def __init__(self, course_id, course_name, course_code, capacity, credit_units):
        self.course_id = course_id
        self.course_name = course_name
        self.course_code = course_code
        self.capacity = capacity
        self.credit_units = credit_units
        self.enrolled_students = []
        self.instructors = []
        self.program = {}  # Map instructors to class codes
        self.gradebook = {}  # Dictionary to store grades {student: grade}
        Course.total_courses += 1
        Course.all_courses.append(self)

    def get_course_id(self):
        return self.course_id

    def get_program(self):
        return self.program

    def get_course_code(self):
        return self.course_code

    def get_credit_units(self):
        return self.credit_units

    def is_full(self):
        return len(self.enrolled_students) >= self.capacity

    def get_details(self):
        return (f"Course: {self.course_name}, Code: {self.course_code}, "
                f"Capacity: {self.capacity}, Enrolled: {len(self.enrolled_students)}, "
                f"Instructor: {', '.join(instructor.get_name() for instructor in self.instructors) if self.instructors else 'None'}")

    def get_enrolled_students(self):
        # Returns the list of students currently enrolled in the course and their count.
        student_count = len(self.enrolled_students)
        return self.enrolled_students, student_count

    @classmethod
    def enroll_stud_to_course(cls):
        print("=== Enroll Student to Course ===")
        conn = get_connection()
        if conn is None:
            print("Failed to connect to the database. Please try again later.")
            return
        try:
            cursor = conn.cursor()
            print("\n=== Pending Enrollment Requests ===")
            cursor.execute("""
                SELECT r.RequestID, s.Username, s.First_name, s.Last_name, c.CourseCode, c.CourseName, r.Program
                FROM EnrollmentRequests r
                JOIN Students s ON r.StudentID = s.StudentID
                JOIN Courses c ON r.CourseID = c.CourseID
                WHERE r.Status = 'Pending'
            """)
            requests = cursor.fetchall()

            if not requests:
                print("No pending requests.")
            else:
                for req in requests:
                    print(f"Request ID: {req.RequestID}, Student: {req.First_name} {req.Last_name} ({req.Username}), "
                          f"Course: {req.CourseCode} - {req.CourseName}, Program: {req.Program}")

            # Process a request if there are any
            if requests:
                request_id = input("Enter the Request ID to process (or press Enter to skip): ").strip()
                if request_id:
                    # Retrieve the specific request
                    cursor.execute("""
                        SELECT r.RequestID, r.StudentID, r.CourseID, c.CourseName, c.Capacity
                        FROM EnrollmentRequests r
                        JOIN Courses c ON r.CourseID = c.CourseID
                        WHERE r.RequestID = ?
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
                                INSERT INTO Enrollments (StudentID, CourseID)
                                VALUES (?, ?)
                            """, (student_id, course_id))
                            # Update the status of the enrollment request
                            cursor.execute("""
                                UPDATE EnrollmentRequests
                                SET Status = 'Approved'
                                WHERE RequestID = ?
                            """, (request_id,))

                            conn.commit()
                            print(f"Student successfully enrolled in {course_name}. Request marked as approved.")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def add_course():
        print("=== Add Course ===")
        course_name = input("Enter course name: ").strip()
        course_code = input("Enter course code: ").strip()
        try:
            capacity = int(input("Enter course capacity of students: ").strip())
            if capacity <= 0:
                print("Capacity must be a positive number.")
                return
        except ValueError:
            print("Invalid input for capacity. Please enter a number.")
            return
        try:
            credit_units = int(input("Enter course credit units: ").strip())
            if credit_units <= 0:
                print("Credit units must be a positive number.")
                return
        except ValueError:
            print("Invalid input for credit units. Please enter a number.")
            return
        # Establish database connection
        conn = get_connection()
        if conn is None:
            print("Failed to connect to the database. Please try again later.")
            return
        try:
            cursor = conn.cursor()
            # Check if the course code already exists
            cursor.execute("SELECT COUNT(*) FROM Courses WHERE CourseCode = ?", (course_code,))
            if cursor.fetchone()[0] > 0:
                print(f"A course with the code '{course_code}' already exists.")
                return
            # Insert new course into the database
            cursor.execute("""
                INSERT INTO Courses (CourseName, CourseCode, Capacity, CreditUnits)
                VALUES (?, ?, ?, ?)
            """, (course_name, course_code, capacity, credit_units))
            conn.commit()
            print("Course added successfully!")
        except Exception as e:
            print(f"Error adding course: {e}")
        finally:
            cursor.close()
            conn.close()

    def get_course_details(self):
        return (f"Course Name: {self.course_name}, Program: {self.program}, "
                f"Capacity: {self.capacity}, Credit Units: {self.credit_units}, "
                f"Enrolled Students: {len(self.enrolled_students)}")

    def is_full(self):
        return len(self.enrolled_students) >= self.capacity

    def list_students(self):
        if not self.enrolled_students:
            print(f"No students are currently enrolled in {self.course_name}.")
        else:
            print(f"Students enrolled in {self.course_name} | {self.program}:")
            for student in self.enrolled_students:
                print(f" - {student.get_name()}")

    def list_instructors(self):
        print("Lists of all Instructors Assigned to the Course")
        if not self.instructors:
            print(f"No instructors are currently assigned to {self.program} | {self.course_name}.")
        else:
            print(f"Instructors for {self.course_name}:")
            for instructor in self.instructors:
                print(f" - {instructor.get_name()}")

    @classmethod
    def total_course_count(cls):
        return f"Total Courses: {cls.total_courses}"

    @staticmethod
    def display_all_courses():
        """Displays all courses along with their schedules."""
        print("\n" + "=" * 37 + " All Courses with Schedules " + "=" * 41)
        conn = get_connection()
        if conn is None:
            print("Failed to connect to the database. Please try again later.")
            return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT CourseID, CourseName, CourseCode, Capacity, CreditUnits
                FROM Courses
            """)
            courses = cursor.fetchall()

            if not courses:
                print("No courses available.")
            else:
                print(
                    f"{'ID':<5} {'Course Name':<35} {'Code':<10} {'Capacity':<10} {'Credit Units':<15} {'Schedules':<50}")
                print("-" * 106)

                # Iterate through all courses and fetch their schedules
                for course in courses:
                    course_id, course_name, course_code, capacity, credit_units = course
                    # Fetch schedules for the current course
                    cursor.execute("""
                        SELECT Day, StartTime, EndTime
                        FROM Schedules WHERE CourseCode = ?
                    """, (course_code,))
                    schedules = cursor.fetchall()

                    # Display course details
                    schedules_str = "No schedule" if not schedules else "\n".join([f"{day}: {start_time} - {end_time}"
                                                                                   for day, start_time, end_time in
                                                                                   schedules])
                    print(
                        f"{course_id:<5} {course_name:<35} {course_code:<10} {capacity:<10} {credit_units:<10} {schedules_str}")
        # except Exception as e:
        #     print(f"Error retrieving courses and schedules: {e}")
        finally:
            cursor.close()
            conn.close()

    def remove_assigned_course(self):
        print("=== Remove Instructor from Course ===")
        course_code = input("Enter the Course Code: ").strip()
        conn = get_connection()
        if conn is None:
            print("Failed to connect to the database. Please try again later.")
            return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Courses WHERE CourseCode = ?", (course_code,))
            course_record = cursor.fetchone()
            if not course_record:
                print(f"No course found with the code {course_code}.")
                return
            # Verify if the instructor exists in the Instructors table
            instructor_id = input("Enter the instructor's ID: ").strip()
            cursor.execute("SELECT * FROM Instructors WHERE InstructorID = ?", (instructor_id,))
            instructor_record = cursor.fetchone()

            if not instructor_record:
                print(f"No instructor found with ID {instructor_id}.")
                return

            # Check if the instructor is assigned to the course
            cursor.execute("SELECT * FROM InsAssignedCourses WHERE InstructorID = ? AND CourseCode = ?",
                           (instructor_id, course_code))
            assignment_record = cursor.fetchone()

            if not assignment_record:
                print(f"Instructor {instructor_id} is not assigned to course {course_code}.")
                return

            # Remove the assignment from the InsAssignedCourses table
            cursor.execute("DELETE FROM InsAssignedCourses WHERE InstructorID = ? AND CourseCode = ?",
                           (instructor_id, course_code))
            conn.commit()
            print(f"Instructor {instructor_id} has been removed from {course_code} successfully.")

        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            cursor.close()
            conn.close()


    @staticmethod
    def get_course_level(credit_units):
        """
        Determines the course level based on credit units.
        """
        if credit_units <= 3:
            return "Beginner"
        elif credit_units <= 6:
            return "Intermediate"
        else:
            return "Advanced"

