class FAQ:
    """Stores frequently asked questions for user support."""

    def __init__(self):
        self.faqs = []

    def add_faq(self, question, answer):
        """Adds a new FAQ entry to the list."""
        self.faqs.append({'question': question, 'answer': answer})

    # def view_faqs(self):
    #     """Displays all the FAQs in a formatted way."""
    #     if not self.faqs:
    #         print("No FAQs available.")
    #         return
    #
    #     print("\n--- Frequently Asked Questions ---")
    #     for index, faq in enumerate(self.faqs, start=1):
    #         print(f"{index}. Question: {faq['question']}")
    #         print(f"   Answer: {faq['answer']}")
    #         print("-" * 50)

    def view_faqs(self, filename="faqs.txt"):
        """Reads and displays FAQs from a text file."""
        try:
            with open(filename, "r") as file:
                content = file.read()
                if content:
                    print(content)
                else:
                    print("No FAQs found in the file.")
        except FileNotFoundError:
            print("FAQ file not found. Please save FAQs first.")

    def save_to_file(self, filename="faqs.txt"):
        """Saves all the FAQs to a text file."""
        if not self.faqs:
            print("No FAQs to save.")
            return

        with open(filename, "w") as file:
            file.write("\n"+ "*-" * 30 + " Frequently Asked Questions" + "-*"* 30 + "\n\n")
            for index, faq in enumerate(self.faqs, start=1):
                file.write(f"{index}. Question: {faq['question']}\n")
                file.write(f"   Answer: {faq['answer']}\n")
                file.write("-" * 150 + "\n")

        # print(f"FAQs have been saved to {filename}")

# Example usage:
faq = FAQ()
faq.add_faq("How do I enroll to course?",
            "You can enroll to your chosen course by clicking on '2'- enroll to course on the Student menu page.")
faq.add_faq("How do I assign a course to a student?",
                "Currently, only administrators have the ability to assign courses to students. If you wish to request a course assignment, contact the admin team.")
faq.add_faq("Can I send messages to students?",
                "Yes, you can send messages to students through the 'Send Message' feature in the Instructor menu by selecting the student's ID and entering your message.")
faq.add_faq("How do I view messages sent to me?",
                "Go to the Instructor menu and select the 'View Messages' option to see all messages sent to you, listed in order of receipt.")
faq.add_faq("How do I enroll in a course?",
                "To enroll in a course, go to the Student menu and select '2' to enroll in your chosen course. Follow the on-screen instructions to complete the enrollment process.")
faq.add_faq("Can I send a message to my instructor?",
                "Yes, you can send a message to your instructor by selecting the appropriate option in the Student menu and entering their ID and message.")
faq.add_faq("What should I do if I forget my student ID?",
                "Contact the administration or use the 'Forgot Student ID' feature (if available) to recover your ID using registered details such as your email or name.")
faq.add_faq("How can I check if my enrollment was successful?",
                "After completing the enrollment process, a confirmation message will appear. You can also check the 'My Courses' section to verify your enrollment.")

# Save the FAQs to a text file
faq.save_to_file()

    # def search_faq(self, keyword):
    #     """Searches for FAQs containing the given keyword."""
    #     results = [faq for faq in self.faqs if
    #                keyword.lower() in faq['question'].lower() or keyword.lower() in faq['answer'].lower()]
    #
    #     if not results:
    #         print("No FAQs found with the given keyword.")
    #         return
    #
    #     print(f"\n--- Search Results for '{keyword}' ---")
    #     for index, faq in enumerate(results, start=1):
    #         print(f"{index}. Question: {faq['question']}")
    #         print(f"   Answer: {faq['answer']}")
    #         print("-" * 50)
