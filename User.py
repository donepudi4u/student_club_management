class User:
    def __init__(self, id, name, email, role,phone_number,roll_number):
        self.id = user_id
        self.name = name
        self.email = email
        self.role = role
        self.phone_number = phone_number
        self.roll_number = roll_number

    def is_admin(self):
        return self.role == 'admin'

    def is_club_leader(self):
        return self.role == 'club_leader'

    def is_student(self):
        return self.role == 'student'
