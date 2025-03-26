from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysql_connector import MySQL

# from User import User


app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL Configuration
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_DATABASE'] = 'student_club_management'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# Route for the homepage (Login page)
@app.route('/')
def index():
    return render_template('login.html')

# User registration route
@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        rollNumber = request.form['rollNumber']
        email = request.form['email']
        phone = request.form['phone']
        communication_preference = request.form['communicationPreference']
        password = request.form['password']
        # role = request.form['role']  # Role from registration form
        # hashed_password = generate_password_hash(password)

        # Save the user to MySQL database
        conn = mysql.connection
        cursor = conn.cursor()
        query = """
            INSERT INTO users (name, roll_number, email, `phone_number`, communication_preference, password)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (name, rollNumber, email, phone, communication_preference, password))
        conn.commit()
        cursor.close()

        flash('User registered successfully!')
        return redirect('/')

# User login route
@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        
        email = request.form['loginEmail']
        password = request.form['loginPassword']

        # Fetch the user from the database
        conn = mysql.connection
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE email = %s AND password = %s", (email, password))
        user_data = cursor.fetchone()
        cursor.close()


        # Validate the login credentials
        if user_data :
            session['user'] = {
                'id': user_data[0],
                'name': user_data[1],
                'email': user_data[3],
                'role': user_data[7],
                'roll_number': user_data[2],
                'phone_number': user_data[4]
            }
            flash('Login successful!')
            # Redirect to the respective dashboard based on role
            if user_data[7] == 'admin':
                return redirect('/admin_dashboard')
            elif user_data[7] == 'club_leader':
                return redirect('/leader_dashboard')
            elif user_data[7] == 'student':
                return redirect('/student_dashboard')
        else:
            flash('Invalid credentials. Please try again.')
            return redirect('/')

@app.route('/dashboard')
def dashboard():
    user_role = session['user']['role']
    if user_role == 'student':
        return redirect('/student_dashboard')
    elif user_role == 'admin':
        return redirect('/admin_dashboard')
    elif user_role == 'club_leader':
        return redirect('/leader_dashboard')
    else:
        return redirect(url_for('login'))

@app.route('/student_dashboard')
def student_dashboard():
    user_id = session['user']['id']
   
    conn = mysql.connection
    cursor = conn.cursor(dictionary=True)
    
    # Fetch clubs the student has already joined
    cursor.execute("""
        SELECT c.club_id, c.club_name, c.description
        FROM Clubs c
        JOIN club_members cm ON c.club_id = cm.club_id
        WHERE cm.user_id = %s
    """, (user_id,))
    joined_clubs = cursor.fetchall()
    
    # Fetch all clubs the student has not joined yet
    cursor.execute("""
        SELECT c.club_id, c.club_name, c.description
        FROM Clubs c
        WHERE c.club_id NOT IN (
            SELECT cm.club_id FROM club_members cm WHERE cm.user_id = %s
        )
    """, (user_id,))
    available_clubs = cursor.fetchall()

    cursor.close()
    conn.close()
    
    return render_template('student_dashboard.html', joined_clubs=joined_clubs, available_clubs=available_clubs)

@app.route('/join_club/<int:club_id>')
def join_club(club_id):
    user_id = session['user']['id']
    
    conn = mysql.connection
    cursor = conn.cursor()
    
    # Check if the user is already a member of the club
    cursor.execute("SELECT * FROM club_members WHERE club_id = %s AND user_id = %s", (club_id, user_id))
    member = cursor.fetchone()
    
    if member:
        flash('You have already joined this club.')
    else:
        cursor.execute("INSERT INTO club_members (club_id, user_id) VALUES (%s, %s)", (club_id, user_id))
        conn.commit()
        flash('You have successfully joined the club!')
    
    cursor.close()
    conn.close()
    
    return redirect(url_for('student_dashboard'))


# Admin dashboard route
@app.route('/admin_dashboard')
def admin_dashboard():
    if session['user']['role'] == 'admin':
        return render_template('admin_dashboard.html', username=session['user']['name'])
    else:
        flash('You are not authorized to view this page.')
        return redirect('/')

# Club Leader Dashboard: Display clubs managed by the leader
@app.route('/leader_dashboard')
def leader_dashboard():
    if 'user' in session and session['user']['role'] != 'club_leader':
        return "Access Denied", 403

    user_id = session['user']['id']
    print(user_id)
    conn =  mysql.connection
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT c.club_id, c.club_name, c.description
        FROM clubs c
        JOIN club_leaders cl ON c.club_id = cl.club_id
        WHERE cl.user_id = %s
    """, (user_id,))
    clubs = cursor.fetchall()
    
    
    # Fetch clubs the student has already joined
    cursor.execute("""
        SELECT c.club_id, c.club_name, c.description
        FROM Clubs c
        JOIN club_members cm ON c.club_id = cm.club_id
        WHERE cm.user_id = %s
    """, (user_id,))
    member_clubs = cursor.fetchall()
    
    # Fetch all clubs the student has not joined yet
    cursor.execute("""
        SELECT c.club_id, c.club_name, c.description
        FROM Clubs c
        WHERE c.club_id NOT IN (
            SELECT cm.club_id FROM club_members cm WHERE cm.user_id = %s
        )
    """, (user_id,))
    other_clubs = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('club_leader_dashboard.html', clubs=clubs, member_clubs = member_clubs, other_clubs=other_clubs)

# Club Details for Club Leader
@app.route('/club_details/<int:club_id>')
def club_details(club_id):
    conn = mysql.connection
    cursor = conn.cursor(dictionary=True)
    
    user = session['user'] 

    # Get club details and members
    cursor.execute("SELECT * FROM clubs WHERE club_id = %s", (club_id,))
    club = cursor.fetchone()
    cursor.execute("""
        SELECT u.id, u.name, u.email, u.phone_number
        FROM club_members cm
        JOIN Users u ON cm.user_id = u.id
        WHERE cm.club_id = %s
    """, (club_id,))
    members = cursor.fetchall()
    
    # Get club events
    cursor.execute("SELECT * FROM Events WHERE club_id = %s", (club_id,))
    events = cursor.fetchall()
    
    cursor.execute("SELECT * FROM club_leaders WHERE club_id = %s", (club_id,))
    clubLeader = cursor.fetchone()
        
    cursor.close()
    conn.close()
    return render_template('club_details.html', club=club, members=members, events=events, user=user, clubLeader=clubLeader)

# Add event under club
@app.route('/add_event/<int:club_id>', methods=['POST'])
def add_event(club_id):
    print(session['user']['role'])
    if 'user' in session and (session['user']['role'] != 'club_leader' and session['user']['role'] != 'admin') :
        return "Access Denied", 403
    event_name = request.form['event_name']
    description = request.form['description']
    event_date = request.form['event_date']

    conn = mysql.connection
    cursor = conn.cursor()
    cursor.execute("INSERT INTO events (club_id, event_name, description, event_date) VALUES (%s, %s, %s, %s)",
                   (club_id, event_name, description, event_date))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Event added successfully!")
    return redirect(url_for('club_details', club_id=club_id))


# Display all clubs
@app.route('/manage_clubs')
def manage_clubs():

    if 'user' in session and session['user']['role'] != 'admin':
        return "Access Denied", 403

    conn = mysql.connection
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT c.club_id, c.club_name, c.description, u.id, u.name  AS leaders
        FROM Clubs c
        LEFT JOIN club_leaders cl ON c.club_id = cl.club_id
        LEFT JOIN Users u ON cl.user_id = u.id        
    """)
    clubs = cursor.fetchall()
    cursor.execute("SELECT id, name FROM Users WHERE role IN ('student','club_leader')")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('manage_clubs.html', clubs=clubs, users=users)

# Add a new club
@app.route('/add_club', methods=['POST'])
def add_club():
    if 'user' in session and session['user']['role'] != 'admin':
        return "Access Denied", 403

    club_name = request.form['club_name']
    description = request.form['description']
    leaders = request.form.getlist('club_leaders')

    conn = mysql.connection
    cursor = conn.cursor()
    cursor.execute("INSERT INTO clubs (club_name, description) VALUES (%s, %s)", (club_name, description))
    club_id = cursor.lastrowid
    print(club_id)
    print(leaders)
    # Assign leaders to the club
    for id  in leaders:
        cursor.execute("INSERT INTO club_leaders (club_id, user_id) VALUES (%s, %s)", (club_id, id))
        cursor.execute("UPDATE users  set role = %s WHERE id = %s", ('club_leader',id))


    conn.commit()
    cursor.close()
    conn.close()
    flash("Club and leaders added successfully!")
    return redirect(url_for('manage_clubs'))

# Delete a club
@app.route('/delete_club/<int:club_id>')
def delete_club(club_id):
    if 'user' in session and session['user']['role'] != 'admin':
        return "Access Denied", 403

    conn = mysql.connection
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Clubs WHERE club_id = %s", (club_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Club deleted successfully!")
    return redirect(url_for('manage_clubs'))

# Edit club details (additional screen can be created for editing)
@app.route('/edit_club', methods=['GET', 'POST'])
def edit_club():
    if 'user' in session and session['user']['role'] != 'admin':
        return "Access Denied", 403
    conn = mysql.connection
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        club_id = request.form['club_id']
        club_name = request.form['name']
        description = request.form['description']
        club_leader_id = request.form['leader_id']
        cursor.execute("UPDATE Clubs SET club_name = %s, description = %s WHERE club_id = %s",
                       (club_name, description, club_id))
        cursor.execute("UPDATE club_leaders SET user_id = %s  WHERE club_id = %s",
                       (club_leader_id, club_id))
        cursor.execute("UPDATE users SET role = %s  WHERE id = %s",
                       ('club_leader', club_leader_id))                                             
        conn.commit()
        flash("Club updated successfully!")
        return redirect(url_for('manage_clubs'))
    else:
        cursor.execute("SELECT * FROM Clubs WHERE club_id = %s", (club_id,))
        club = cursor.fetchone()
        cursor.close()
        conn.close()
        return render_template('edit_club.html', club=club)

# Assign or remove a club leader
@app.route('/assign_leader', methods=['POST'])
def assign_leader():
    if 'user' in session and session['user']['role'] != 'admin':
        return "Access Denied", 403

    club_id = request.form['club_id']
    user_id = request.form['user_id']
    action = request.form['action']  # 'add' or 'remove'

    conn = mysql.connection
    cursor = conn.cursor()
    if action == 'add':
        cursor.execute("INSERT INTO club_leaders (club_id, user_id) VALUES (%s, %s)", (club_id, user_id))
    elif action == 'remove':
        cursor.execute("DELETE FROM club_leaders WHERE club_id = %s AND user_id = %s", (club_id, user_id))
    conn.commit()
    cursor.close()
    conn.close()
    flash(f"Club leader {'added' if action == 'add' else 'removed'} successfully!")
    return redirect(url_for('manage_clubs'))

@app.route('/manage_users')
def manage_users():
    if 'user' in session and session['user']['role'] == 'admin':  # Only admins can view this page
        conn = mysql.connection
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name,roll_number,email, phone_number,communication_preference,role FROM users")
        users = cursor.fetchall()
        cursor.close()
        return render_template('manage_users.html', users=users)
    return redirect(url_for('login'))

@app.route('/add_user', methods=['POST'])
def add_user():
    if 'user' in session and session['user']['role'] == 'admin':  # Only admins can add users
        name = request.form['name']
        roll_number = request.form['roll_number']
        email = request.form['email']
        phone = request.form['phone']
        communicationPreference = request.form['communicationPreference']
        password = request.form['password']
        role = request.form['role']
        
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO users (name, roll_number, email, phone_number,communication_preference, password, role) VALUES (%s, %s, %s, %s,%s,%s, %s)", (name, roll_number, email, phone, communicationPreference, password, role))
        mysql.connection.commit()
        cursor.close()
        
        flash('User added successfully!')
        return redirect(url_for('manage_users'))
# Update user
@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if 'user' in session and session['user']['role'] == 'admin':  # Only admins can edit users
        cursor = mysql.connection.cursor(dictionary=True)
        
        if request.method == 'POST':
            name = request.form['name']
            email = request.form['email']
            phone = request.form['phone']
            role = request.form['role']
            
            cursor.execute("UPDATE users SET name=%s, email=%s, phone_number=%s, role=%s WHERE id=%s", (name, email, phone, role, user_id))
            mysql.connection.commit()
            flash('User updated successfully!')
            return redirect(url_for('manage_users'))
        
        # Pre-fill the form with user details
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        
        return render_template('edit_user.html', user=user)
    
    return redirect(url_for('login'))

# Delete user
@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    if 'user' in session and session['user']['role'] == 'admin':  # Only admins can delete users
        cursor = mysql.connection.cursor()
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        mysql.connection.commit()
        cursor.close()
        flash('User deleted successfully!')
        return redirect(url_for('manage_users'))
    
    return redirect(url_for('login'))        

# Delete user
@app.route('/delete_member/<int:club_id>/<int:user_id>')
def delete_user_from_club(club_id,user_id):
    if 'user' in session and (session['user']['role'] != 'club_leader' and session['user']['role'] != 'admin') :
        return "Access Denied", 403
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM club_members WHERE club_id = %s and user_id = %s", (club_id,user_id,))
    mysql.connection.commit()
    cursor.close()
    flash('User deleted from club successfully!')
    return redirect(url_for('club_details', club_id=club_id))


@app.route('/leave_club', methods=['POST'])
def leave_club():
    if 'user' in session:
        user_id = session['user']['id']
        club_id = request.form['club_id']
        print(user_id)
        print(club_id)

        cursor = mysql.connection.cursor()
        cursor.execute("""
            DELETE FROM club_members 
            WHERE user_id=%s AND club_id=%s
        """, (user_id, club_id))
        mysql.connection.commit()
        cursor.close()

        flash('You have successfully left the club.', 'success')
        return redirect('/dashboard')
    return redirect('/login')

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user' in session:
        user_id = session['user']['id']
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']

        cursor = mysql.connection.cursor()
        cursor.execute("""
            UPDATE users 
            SET name=%s, email=%s, phone_number=%s 
            WHERE id=%s
        """, (name, email, phone, user_id))
        mysql.connection.commit()
        cursor.close()

        # Update session data
        session['user']['name'] = name
        session['user']['email'] = email
        session['user']['phone_number'] = phone

        flash('Profile updated successfully', 'success')
        return redirect('/dashboard')
    return redirect('/login')

# Route for logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('role', None)
    flash('You have been logged out.')
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
