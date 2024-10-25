from flask import Flask, render_template, request, redirect, session, flash
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
            session['user_id'] = user[1]
            session['username'] = user[2]
            session['role'] = user[7]

            flash('Login successful!')
            
            # Redirect based on user role
            if user[7] == 'admin':
                return redirect('/admin_dashboard')
            elif user[7] == 'club_leader':
                return redirect('/club_leader_dashboard')
            else:
                return redirect('/student_dashboard')
        else:
            flash('Invalid credentials. Please try again.')
            return redirect('/')

# Student dashboard route
@app.route('/student_dashboard')
def student_dashboard():
    if 'user_id' in session and session['role'] == 'student':
        return render_template('student_dashboard.html', username=session['username'])
    else:
        flash('You are not authorized to view this page.')
        return redirect('/')

# Admin dashboard route
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' in session and session['role'] == 'admin':
        return render_template('admin_dashboard.html', username=session['username'])
    else:
        flash('You are not authorized to view this page.')
        return redirect('/')

# Club Leader dashboard route
@app.route('/club_leader_dashboard')
def club_leader_dashboard():
    if 'user_id' in session and session['role'] == 'club_leader':
        return render_template('club_leader_dashboard.html', username=session['username'])
    else:
        flash('You are not authorized to view this page.')
        return redirect('/')

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
