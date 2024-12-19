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

class Message:
    def __init__(self):
        self.messages = []

    @staticmethod
    def send_message():
        # Ask the user for the type of recipient (student or instructor)
        recipient_type = input("Enter the type of recipient \n(1. student 2. instructor): ").strip().lower()
        conn = get_connection()
        if conn is None:
            print("Failed to connect to the database. Please try again later.")
            return
        try:
            cursor = conn.cursor()
            if recipient_type == '1':
                # Get student ID and message
                student_id = input("Enter student ID: ").strip()
                cursor.execute("SELECT * FROM Students WHERE StudentID = ?", (student_id,))
                student = cursor.fetchone()

                if not student:
                    print("Student not found!")
                    return

                sender = 'HK Academy'
                message = input("Enter the message to send: ").strip()

                # Correct the SQL query to use a parameter for the sender
                cursor.execute("""
                    INSERT INTO Messaging (RecipientID, RecipientType, Sender, MessageContent, DateSent)
                    VALUES (?, 'Student', ?, ?, GETDATE())
                """, (student_id, sender, message))

                conn.commit()
                print(f"Message was sent to student with ID {student_id}!")

            elif recipient_type == '2':
                # Get instructor ID and message
                instructor_id = input("Enter instructor ID: ").strip()
                cursor.execute("SELECT * FROM Instructors WHERE InstructorID = ?", (instructor_id,))
                instructor = cursor.fetchone()

                if not instructor:
                    print("Instructor not found!")
                    return

                sender = 'Yeoreobeun Academy'
                message = input("Enter the message to send: ").strip()

                # Correct the SQL query to use a parameter for the sender
                cursor.execute("""
                    INSERT INTO Messaging (RecipientID, RecipientType, Sender, MessageContent, DateSent)
                    VALUES (?, 'Instructor', ?, ?, GETDATE())
                """, (instructor_id, sender, message))

                conn.commit()
                print(f"Notification was sent to instructor with ID {instructor_id}!")

            else:
                print("Invalid recipient type. Please enter '1' or '2'.")

        except Exception as e:
            print(f"An error occurred while sending the message: {e}")
        finally:
            cursor.close()
            conn.close()





