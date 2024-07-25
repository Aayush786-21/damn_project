from flask import Flask, render_template, redirect, url_for, request, jsonify, session
import qrcode
import os
import sqlite3
import cv2
import numpy as np
from pyzbar.pyzbar import decode
from datetime import datetime
import json
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from cryptography.fernet import Fernet, InvalidToken
import logging

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Encryption key setup
KEY_FILE = 'secret.key'

def generate_key():
    return Fernet.generate_key()

def save_key(key, filename=KEY_FILE):
    with open(filename, 'wb') as key_file:
        key_file.write(key)

def load_key(filename=KEY_FILE):
    try:
        with open(filename, 'rb') as key_file:
            return key_file.read()
    except FileNotFoundError:
        logging.error(f"Key file {filename} not found.")
        return None

# Load encryption key
if not os.path.exists(KEY_FILE):
    encryption_key = generate_key()
    save_key(encryption_key)
else:
    encryption_key = load_key()

def encrypt_data(data, key):
    fernet = Fernet(key)
    encrypted_data = fernet.encrypt(data.encode())
    logging.debug(f"Encrypted data: {encrypted_data}")
    return encrypted_data

def decrypt_data(encrypted_data, key):
    fernet = Fernet(key)
    try:
        decrypted_data = fernet.decrypt(encrypted_data).decode()
        logging.debug(f"Decrypted data: {decrypted_data}")
        return decrypted_data
    except InvalidToken as e:
        logging.error(f"Decryption error (InvalidToken): {e}")
        logging.error(f"Problematic encrypted data: {encrypted_data}")
        return None
    except Exception as e:
        logging.error(f"Unexpected decryption error: {e}")
        logging.error(f"Problematic encrypted data: {encrypted_data}")
        return None

def init_sqlite_db():
    conn = sqlite3.connect('sql.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role BLOB,
    first_name BLOB,
    middle_name BLOB,
    last_name BLOB,
    roll_no TEXT UNIQUE,
    address BLOB,
    email BLOB,
    qr_code_path TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roll_no TEXT,
    date TEXT,
    status TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
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

        conn = sqlite3.connect('sql.db')
        cursor = conn.cursor()
        cursor.execute('SELECT password FROM admin WHERE username = ?', (username,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if row and check_password_hash(row[0], password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return "Incorrect username or password", 401

    return render_template('admin.html')

@app.route('/admin_signup', methods=['GET', 'POST'])
def admin_signup():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        conn = sqlite3.connect('sql.db')
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO admin (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            return redirect(url_for('admin'))
        except sqlite3.IntegrityError:
            return "Username already taken", 400
        finally:
            cursor.close()
            conn.close()

    return render_template('signup.html')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('admin'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = encrypt_data(request.form['role'], encryption_key)
        first_name = encrypt_data(request.form['first_name'], encryption_key)
        middle_name = encrypt_data(request.form['middle_name'], encryption_key)
        last_name = encrypt_data(request.form['last_name'], encryption_key)
        roll_no = request.form['roll_no']  # Roll number is used as a unique identifier, so it should not be encrypted
        address = encrypt_data(request.form['address'], encryption_key)
        email = encrypt_data(request.form['email'], encryption_key)

        details = {
            "Role": request.form['role'],
            "First Name": request.form['first_name'],
            "Middle Name": request.form['middle_name'],
            "Last Name": request.form['last_name'],
            "Roll No.": roll_no,
            "Address": request.form['address'],
            "Email": request.form['email']
        }

        details_json = json.dumps(details)

        # Generate QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(details_json)
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
            logging.info(f"User registered successfully: {roll_no}")
        except sqlite3.IntegrityError:
            logging.error(f"Registration failed: Roll number {roll_no} already exists.")
            return "Roll number already exists. Please use a unique roll number."
        finally:
            cursor.close()
            conn.close()

        # Save QR review page as a static HTML file
        qr_review_html = render_template('qr_review.html', details=details, qr_code_url=f'qr_{roll_no}.png')
        qr_review_path = os.path.join('static', f'qr_review_{roll_no}.html')
        with open(qr_review_path, 'w') as f:
            f.write(qr_review_html)

        return render_template('qr_review.html', details=details, qr_code_url=f'qr_{roll_no}.png')
    return render_template('register.html')

@app.route('/student_records', methods=['GET'])
def student_records():
    month = request.args.get('month', '07')  # Default to current month if not provided
    year = request.args.get('year', str(datetime.now().year))  # Default to current year if not provided
    
    students = fetch_students()
    attendance_data = fetch_attendance(month, year)
    
    print("Fetched students: ", students)  # Debug: Check fetched students
    print("Fetched attendance: ", attendance_data)  # Debug: Check fetched attendance data
    
    records = []
    for student in students:
        record = {
            'roll_no': student['roll_no'],
            'first_name': student['first_name'],
            'middle_name': student['middle_name'],
            'last_name': student['last_name'],
            'email': student['email'],
            'attendance': ['N/A'] * 31
        }
        for attendance in attendance_data:
            roll_no, date, status = attendance
            day = int(date.split('-')[2])
            if roll_no == student['roll_no']:
                record['attendance'][day-1] = 'P' if status == 'present' else 'A'
        records.append(record)
    
    print("Records: ", records)  # Debug: Check processed records
    
    return render_template('student_records.html', records=records, current_year=year)

@app.route('/teacher_records')
@login_required
def teacher_records():
    conn = sqlite3.connect('sql.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE role=?', (encrypt_data("teacher", encryption_key),))
    records = cursor.fetchall()
    cursor.close()
    conn.close()

    decrypted_records = []
    for record in records:
        decrypted_record = list(record)
        decrypted_record[1] = decrypt_data(record[1], encryption_key)  # role
        decrypted_record[2] = decrypt_data(record[2], encryption_key)  # first_name
        decrypted_record[3] = decrypt_data(record[3], encryption_key)  # middle_name
        decrypted_record[4] = decrypt_data(record[4], encryption_key)  # last_name
        decrypted_record[6] = decrypt_data(record[6], encryption_key)  # address
        decrypted_record[7] = decrypt_data(record[7], encryption_key)  # email
        decrypted_records.append(decrypted_record)

    logging.debug(f"Teacher records: {decrypted_records}")
    
    return render_template('teacher_records.html', records=decrypted_records)

def fetch_students():
    conn = sqlite3.connect('sql.db')
    cursor = conn.cursor()
    cursor.execute("SELECT roll_no, first_name, middle_name, last_name, email FROM users")
    students = cursor.fetchall()
    conn.close()
    return [
        {
            'roll_no': student[0],
            'first_name': decrypt_data(student[1], encryption_key),
            'middle_name': decrypt_data(student[2], encryption_key),
            'last_name': decrypt_data(student[3], encryption_key),
            'email': decrypt_data(student[4], encryption_key)
        }
        for student in students
    ]

def fetch_attendance(month, year):
    conn = sqlite3.connect('sql.db')
    cursor = conn.cursor()
    cursor.execute("SELECT roll_no, date, status FROM attendance WHERE strftime('%m', date) = ? AND strftime('%Y', date) = ?", (month, year))
    attendance = cursor.fetchall()
    conn.close()
    return attendance
@app.route('/mark_attendance', methods=['POST'])
@login_required
def mark_attendance():
    data = request.get_json()
    roll_no = data.get('roll_no')
    date = data.get('date')
    status = data.get('status')

    conn = sqlite3.connect('sql.db')
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO attendance (roll_no, date, status)
            VALUES (?, ?, ?)
        """, (roll_no, date, status))
        conn.commit()
        logging.info(f"Attendance marked successfully for {roll_no} on {date}")
        return jsonify({"message": "Attendance marked successfully"}), 200
    except sqlite3.IntegrityError as e:
        logging.error(f"Error marking attendance: {e}")
        return jsonify({"message": "Error marking attendance"}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/view_attendance', methods=['GET'])
def view_attendance():
    roll_no = request.args.get('roll_no')
    month = request.args.get('month', datetime.now().strftime('%m'))
    year = request.args.get('year', datetime.now().strftime('%Y'))

    conn = sqlite3.connect('sql.db')
    cursor = conn.cursor()
    cursor.execute('SELECT date, status FROM attendance WHERE roll_no = ? AND strftime("%m", date) = ? AND strftime("%Y", date) = ?', (roll_no, month, year))
    attendance_records = cursor.fetchall()
    cursor.close()
    conn.close()

    dates = []
    statuses = []
    for record in attendance_records:
        dates.append(record[0])
        statuses.append(record[1])

    return render_template('view_attendance.html', roll_no=roll_no, dates=dates, statuses=statuses, month=month, year=year)

@app.route('/logout')
@login_required
def logout():
    session.pop('username', None)
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)
