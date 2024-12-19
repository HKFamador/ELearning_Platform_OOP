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
class Enrollment:
    total_enrollments = 0

    def __init__(self, student):
        self.student_id = student.get_student_id()
        self.student = student
        Enrollment.total_enrollments += 1
        self.enrollment_requests= []
        self.assigned_courses = []

    def get_enrollment_details(self):
        return f"Enrollment: {self.student.get_name()} in {self.assigned_courses}"

    @staticmethod
    def enroll_students_as_admin():
        """Admin enrolls students into any course."""
        print("=== Admin Enrollment ===")
        conn = get_connection()
        if conn is None:
            print("Failed to connect to the database. Please try again later.")
            return
        try:
            cursor = conn.cursor()
            print("\n=== Pending Enrollment Requests ===")
            cursor.execute("""
                SELECT r.EnrollmentReq, s.Username, s.FirstName, s.LastName, c.CourseCode, c.CourseName
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
                    print(f"Request ID: {req[0]}, Student: {req[2]} {req[3]} ({req[1]}), "
                          f"Course: {req[4]} - {req[5]}")

                # Process a request
                request_id = input("Enter the Enrollment Request No. to process (or press Enter to skip): ").strip()
                if request_id:
                    cursor.execute("""
                        SELECT r.EnrollmentReq, r.StudentID, r.CourseID, c.CourseCode, c.CourseName, c.Capacity
                        FROM EnrollmentRequests r
                        JOIN Courses c ON r.CourseID = c.CourseID
                        WHERE r.EnrollmentReq = ?
                    """, (request_id,))
                    request = cursor.fetchone()

                    if not request:
                        print("Invalid Request ID.")
                    else:
                        request_id, student_id, course_id, course_code, course_name, capacity = request

                        # Check if the course is full
                        cursor.execute("SELECT COUNT(*) FROM Enrollments WHERE CourseID = ?", (course_id,))
                        current_enrollment = cursor.fetchone()[0]

                        if current_enrollment >= capacity:
                            print(f"Sorry, the course {course_name} is full.")
                        else:
                            # Enroll the student
                            cursor.execute("""
                                SELECT s.FirstName, s.LastName
                                FROM Students s
                                WHERE s.StudentID = ?
                            """, (student_id,))
                            student = cursor.fetchone()
                            if student:
                                first_name, last_name = student

                                # Insert enrollment
                                cursor.execute("""
                                    INSERT INTO Enrollments (StudentID, CourseID, CourseCode, FirstName, LastName, EnrollmentDate)
                                    VALUES (?, ?, ?, ?, ?, GETDATE())
                                """, (student_id, course_id, course_code, first_name, last_name))

                                # Mark the request as approved
                                cursor.execute("""
                                    UPDATE EnrollmentRequests
                                    SET Status = 'Approved'
                                    WHERE EnrollmentReq = ?
                                """, (request_id,))

                                conn.commit()
                                print(f"Student successfully enrolled in {course_name}. Request marked as approved.")
                            else:
                                print("Student not found in the database.")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def view_enrolled_students():
        print("=== View Enrolled Students ===")
        conn = get_connection()
        if conn is None:
            print("Failed to connect to the database. Please try again later.")
            return
        try:
            cursor = conn.cursor()
            # Display all courses
            print("Available courses:")
            cursor.execute("""
                SELECT CourseCode, CourseName FROM Courses
            """)
            courses = cursor.fetchall()
            if not courses:
                print("No courses found.")
                return

            for course in courses:
                print(f"{course[0]} - {course[1]}")

            # Prompt for course selection
            course_code = input(
                "\nEnter the course code to view enrolled students (or press Enter to view all): ").strip()

            # Query to fetch enrolled students
            if course_code:
                cursor.execute("""
                    SELECT s.StudentID, s.FirstName, s.LastName, s.Email, c.CourseCode, c.CourseName
                    FROM Enrollments e
                    JOIN Students s ON e.StudentID = s.StudentID
                    JOIN Courses c ON e.CourseID = c.CourseID
                    WHERE c.CourseCode = ?
                """, (course_code,))
            else:
                cursor.execute("""
                    SELECT s.StudentID, s.FirstName, s.LastName, s.Email, c.CourseCode, c.CourseName
                    FROM Enrollments e
                    JOIN Students s ON e.StudentID = s.StudentID
                    JOIN Courses c ON e.CourseID = c.CourseID
                """)

            rows = cursor.fetchall()

            if not rows:
                print(f"No students enrolled{f' in {course_code}' if course_code else ''}.")
            else:
                # Display enrolled students
                print("\nEnrolled Students:")
                print(
                    f"{'Student ID':<12} {'First Name':<15} {'Last Name':<15} {'Email':<30} {'Course Code':<12} {'Course Name':<30}")
                print("-" * 120)
                for row in rows:
                    student_id, first_name, last_name, email, course_code, course_name = row
                    print(
                        f"{student_id:<12} {first_name:<15} {last_name:<15} {email:<30} {course_code:<12} {course_name:<30}")

        except Exception as e:
            print(f"Error fetching enrolled students: {e}")
        finally:
            cursor.close()
            conn.close()

    @classmethod
    def class_enrollment_method(cls):
        return f"Total Enrollments: {cls.total_enrollments}"