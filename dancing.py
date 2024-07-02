from flask import Flask, render_template, redirect, url_for, request
import qrcode
import os
import sqlite3

app = Flask(__name__)

# Ensure the static folder exists for saving QR codes
if not os.path.exists('static'):
    os.makedirs('static')

# Database configuration and initialization
def init_sqlite_db():
    conn = sqlite3.connect('sql.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT,
            first_name TEXT,
            middle_name TEXT,
            last_name TEXT,
            roll_no TEXT UNIQUE,
            address TEXT,
            email TEXT,
            qr_code_path TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_sqlite_db()

@app.route('/')
def home():
    return render_template('ghar.html')

@app.route('/student')
def student():
    return render_template('student.html')

@app.route('/teacher')
def teacher():
    return render_template('teacher.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'username' and password == 'password':
            return redirect(url_for('dashboard'))
    return render_template('admin.html')

@app.route('/dashboard')
def dashboard():
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = request.form['role']
        first_name = request.form['first_name']
        middle_name = request.form['middle_name']
        last_name = request.form['last_name']
        roll_no = request.form['roll_no']
        address = request.form['address']
        email = request.form['email']

        details = {
            "Role": role,
            "First Name": first_name,
            "Middle Name": middle_name,
            "Last Name": last_name,
            "Roll No.": roll_no,
            "Address": address,
            "Email": email
        }

        # Generate QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(details)
        qr.make(fit=True)

        img = qr.make_image(fill='black', back_color='white')
        qr_code_path = os.path.join('static', f'qr_{roll_no}.png')
        img.save(qr_code_path)

        # Save to database
        try:
            conn = sqlite3.connect('sql.db')
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (role, first_name, middle_name, last_name, roll_no, address, email, qr_code_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (role, first_name, middle_name, last_name, roll_no, address, email, qr_code_path))
            conn.commit()
        except sqlite3.IntegrityError:
            return "Roll number already exists. Please use a unique roll number."
        finally:
            cursor.close()
            conn.close()

        return render_template('qr_review.html', details=details, qr_code_url=f'qr_{roll_no}.png')
    return render_template('register.html')

@app.route('/qr_review')
def qr_review():
    return render_template('qr_review.html')

@app.route('/student_records')
def student_records():
    conn = sqlite3.connect('sql.db')
    cursor = conn.cursor()
    cursor.execute("SELECT roll_no, first_name || ' ' || last_name as name, email FROM users WHERE role='student'")
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('student_records.html', students=students)

@app.route('/teacher_records')
def teacher_records():
    conn = sqlite3.connect('sql.db')
    cursor = conn.cursor()
    cursor.execute("SELECT roll_no, first_name || ' ' || last_name as name, email FROM users WHERE role='teacher'")
    teachers = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('teacher_records.html', teachers=teachers)

if __name__ == '__main__':
    app.run(debug=True)
