from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysql_connector import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

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
        hashed_password = generate_password_hash(password)

        # Save the user to MySQL database
        conn = mysql.connection
        cursor = conn.cursor()
        query = """
            INSERT INTO users (name, roll_number, email, `phone_number`, communication_preference, password)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (name, rollNumber, email, phone, communication_preference, hashed_password))
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
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()

        # Validate the login credentials
        if user and check_password_hash(user[6], password):
            session['id'] = user[0]
            session['user_id'] = user[1]
            session['username'] = user[2]
            session['role'] = user[7]

            flash('Login successful!')
            
            
            # Redirect based on user role
            if user[7] == 'admin':
                return redirect('/admin_dashboard')
            elif user[7] == 'club_leader':
                return redirect('/leader_dashboard')
            else:
                return redirect('/student_dashboard')
        else:
            flash('Invalid credentials. Please try again.')
            return redirect('/')

@app.route('/student_dashboard')
def student_dashboard():
    user_id = session.get('id')
    
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
    user_id = session.get('id')
    
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
    if 'user_id' in session and session['role'] == 'admin':
        return render_template('admin_dashboard.html', username=session['username'])
    else:
        flash('You are not authorized to view this page.')
        return redirect('/')

# Club Leader Dashboard: Display clubs managed by the leader
@app.route('/leader_dashboard')
def leader_dashboard():
    
    user_id = session.get('id')
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
    print(clubs)
    cursor.close()
    conn.close()
    return render_template('club_leader_dashboard.html', clubs=clubs)

# Club Details for Club Leader
@app.route('/club_details/<int:club_id>')
def club_details(club_id):
    conn = mysql.connection
    cursor = conn.cursor(dictionary=True)
    
    # Get club details and members
    cursor.execute("SELECT * FROM clubs WHERE club_id = %s", (club_id,))
    club = cursor.fetchone()
    cursor.execute("""
        SELECT u.name, u.email, u.phone_number
        FROM club_members cm
        JOIN Users u ON cm.user_id = u.id
        WHERE cm.club_id = %s
    """, (club_id,))
    members = cursor.fetchall()
    
    # Get club events
    cursor.execute("SELECT * FROM Events WHERE club_id = %s", (club_id,))
    events = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('club_details.html', club=club, members=members, events=events)

# Add event under club
@app.route('/add_event/<int:club_id>', methods=['POST'])
def add_event(club_id):
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
    conn = mysql.connection
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT c.club_id, c.club_name, c.description, 
               GROUP_CONCAT(u.name SEPARATOR ',') AS leaders
        FROM Clubs c
        LEFT JOIN club_leaders cl ON c.club_id = cl.club_id
        LEFT JOIN Users u ON cl.user_id = u.id
        GROUP BY c.club_id
    """)
    clubs = cursor.fetchall()
    cursor.execute("SELECT id, name FROM Users WHERE role IN ('club_leader', 'student')")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('manage_clubs.html', clubs=clubs, users=users)

# Add a new club
@app.route('/add_club', methods=['POST'])
def add_club():
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


    conn.commit()
    cursor.close()
    conn.close()
    flash("Club and leaders added successfully!")
    return redirect(url_for('manage_clubs'))

# Delete a club
@app.route('/delete_club/<int:club_id>')
def delete_club(club_id):
    conn = mysql.connection
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Clubs WHERE club_id = %s", (club_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Club deleted successfully!")
    return redirect(url_for('manage_clubs'))

# Edit club details (additional screen can be created for editing)
@app.route('/edit_club/<int:club_id>', methods=['GET', 'POST'])
def edit_club(club_id):
    conn = mysql.connection
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        club_name = request.form['club_name']
        description = request.form['description']
        cursor.execute("UPDATE Clubs SET club_name = %s, description = %s WHERE club_id = %s",
                       (club_name, description, club_id))
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
