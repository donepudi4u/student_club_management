class User:
    def __init__(self, user_id, username, email, role):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.role = role

    def is_admin(self):
        return self.role == 'admin'

    def is_club_leader(self):
        return self.role == 'club_leader'

    def is_student(self):
        return self.role == 'student'
