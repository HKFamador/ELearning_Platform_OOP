from datetime import datetime, timedelta
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
        return None

class Schedule:
    def __init__(self, course_code, start_time, end_time, day):
        self.course_code = course_code
        self.start_time = start_time
        self.end_time = end_time
        self.day = day

    def calculate_end_time(self):
        duration_in_hours = self.course.credit_units * 60
        end_time = self.start_time + timedelta(hours=duration_in_hours)
        return end_time


    @staticmethod
    def create_schedule():
        print("=== Create a New Schedule ===")
        course_code = input("Enter the course code (e.g., CS101): ")

        conn = get_connection()
        if conn is None:
            print("Failed to connect to the database. Please try again later.")
            return

        try:
            cursor = conn.cursor()

            # Check if the course exists and fetch credit units
            cursor.execute("""
                SELECT CourseID, CourseCode, CourseName, CreditUnits
                FROM Courses WHERE CourseCode = ?
            """, (course_code,))
            course_record = cursor.fetchone()
            if not course_record:
                print("Course not found.")
                return

            course_id, course_code, course_name, credit_units = course_record

            # Check if the course already has a schedule for the given day
            day = input("Enter the day of the week (e.g., 'Monday'): ")

            cursor.execute("""SELECT 1 FROM Schedules WHERE CourseCode = ? AND Day = ? """, (course_code, day))
            if cursor.fetchone():
                print("Course has already a schedule assigned.")
                return

            # Calculate duration based on credit units
            duration_minutes = credit_units * 60

            start_time_str = input("Enter the start time of the class (format: HH:MM, e.g., '09:00'): ")

            try:
                # Parse and remove seconds/microseconds from start time
                start_time = datetime.strptime(start_time_str, '%H:%M').time().replace(second=0, microsecond=0)

                # Calculate end time based on duration
                duration_timedelta = timedelta(minutes=duration_minutes)
                end_time = (datetime.combine(datetime.today(), start_time) + duration_timedelta).time().replace(
                    second=0, microsecond=0)

                # Convert time objects to strings formatted as HH:MM
                start_time_str = start_time.strftime('%H:%M')
                end_time_str = end_time.strftime('%H:%M')

                # Create the schedule instance
                schedule = Schedule(
                    course_code=course_code,
                    start_time=start_time,
                    end_time=end_time,
                    day=day
                )

                # Insert the schedule into the database using formatted strings
                cursor.execute("""
                    INSERT INTO Schedules (CourseCode, Day, StartTime, EndTime)
                    VALUES (?, ?, ?, ?)
                """, (course_code, day, start_time_str, end_time_str))

                conn.commit()
                print("\n=== Schedule Created Successfully ===")
                # Create the table data
                table = [
                    ["Course Code", "Day", "Start Time", "End Time"],
                    [schedule.course_code, schedule.day, schedule.start_time.strftime('%H:%M'), schedule.end_time.strftime('%H:%M')]
                ]

                # Print the table using tabulate with a fancy format
                print(tabulate(table, headers='firstrow', tablefmt='fancy_grid'))

            except ValueError:
                print("Invalid time format. Please enter the time in HH:MM format.")
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def display_all_schedules():
        conn = get_connection()
        if conn is None:
            print("Failed to connect to the database. Please try again later.")
            return

        try:
            cursor = conn.cursor()

            # Query to get all courses, their schedules, and the instructor details
            cursor.execute("""
                SELECT c.CourseCode, c.CourseName, 
                       s.Day, s.StartTime, s.EndTime, 
                       i.FirstName, i.LastName
                FROM Courses c
                LEFT JOIN Schedules s ON c.CourseCode = s.CourseCode
                LEFT JOIN InsAssignedCourses iac ON c.CourseCode = iac.CourseCode
                LEFT JOIN Instructors i ON iac.InstructorID = i.InstructorID
                ORDER BY c.CourseCode, s.Day, s.StartTime
            """)
            rows = cursor.fetchall()

            if not rows:
                print("No courses or schedules found.")
                return

            # Print header
            print(f"{'Course Code':<15} {'Course Name':<35} {'Instructor':<25} {'Day':<12} {'Start Time':<10} {'End Time':<10}")
            print("-" * 112)

            # Print each schedule
            for row in rows:
                course_code, course_name, day, start_time, end_time, first_name, last_name = row
                instructor_name = f"{first_name} {last_name}" if first_name and last_name else "No Instructor"
                day = day if day else "No Schedule"
                start_time = start_time if start_time else "N/A"
                end_time = end_time if end_time else "N/A"
                print(f"{course_code:<15} {course_name:<35} {instructor_name:<25} {day:<12} {start_time:<10} {end_time:<10}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            cursor.close()
            conn.close()


