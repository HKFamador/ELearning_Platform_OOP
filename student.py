class Student:
    def __init__(self, student_id, first_name, last_name, middle_name, username, email, password, age, gender,
                 class_code):
        self.student_id = student_id
        self.first_name = first_name
        self.last_name = last_name
        self.middle_name = middle_name
        self.username = username
        self.email = email
        self.password = password  # Consider hashing this in a real application
        self.age = age
        self.gender = gender
        self.class_code = class_code

    def get_first_name(self):
        return self.first_name


class Admin:
    def __init__(self):
        self.students = []

