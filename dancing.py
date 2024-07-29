from flask import Flask, render_template, redirect, url_for, request, jsonify, session
from flask_mail import Mail, Message
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import qrcode
import os
import sqlite3
import cv2
import numpy as np
from pyzbar.pyzbar import decode
from datetime import datetime, timedelta
import json
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from cryptography.fernet import Fernet, InvalidToken
import logging


app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'nobusparkhere@gmail.com'
app.config['MAIL_PASSWORD'] = '()dev0ps?786A'

mail = Mail(app)

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
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roll_no TEXT,
    last_notified_date TEXT
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
        if student['role'] == 'student':  # Only process students
            record = {
                'first_name': student['first_name'],
                'middle_name': student['middle_name'],
                'last_name': student['last_name'],
                'roll_no': student['roll_no'],
                'address': student['address'],
                'email': student['email'],
                'attendance': []
            }
            
            for day in range(1, 32):  # Assuming a maximum of 31 days in a month
                date = f"{year}-{month}-{day:02d}"
                status = 'absent'  # Default to 'absent'
                
                for attendance in attendance_data:
                    if attendance[0] == student['roll_no'] and attendance[1] == date:
                        status = attendance[2]  # Update status if attendance record found
                
                record['attendance'].append({
                    'date': date,
                    'status': status
                })
            records.append(record)
    
    print("Attendance records: ", records)  # Debug: Check compiled attendance records
    
    return render_template('student_records.html', records=records, current_month=month, current_year=year, class_label='BCA VI Sem')

def fetch_students():
    conn = sqlite3.connect('sql.db')
    cursor = conn.cursor()
    cursor.execute('SELECT role, first_name, middle_name, last_name, roll_no, address, email FROM users')
    rows = cursor.fetchall()
    conn.close()
    
    students = []
    for row in rows:
        student = {
            'role': decrypt_data(row[0], encryption_key),
            'first_name': decrypt_data(row[1], encryption_key),
            'middle_name': decrypt_data(row[2], encryption_key),
            'last_name': decrypt_data(row[3], encryption_key),
            'roll_no': row[4],
            'address': decrypt_data(row[5], encryption_key),
            'email': decrypt_data(row[6], encryption_key)
        }
        students.append(student)
    
    return students

def fetch_attendance(month, year):
    conn = sqlite3.connect('sql.db')
    cursor = conn.cursor()
    cursor.execute('SELECT roll_no, date, status FROM attendance WHERE strftime("%m", date) = ? AND strftime("%Y", date) = ?', (month, year))
    rows = cursor.fetchall()
    conn.close()
    return rows

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    if 'image' not in request.files:
        return "No image provided", 400

    image_file = request.files['image']
    image = cv2.imdecode(np.frombuffer(image_file.read(), np.uint8), cv2.IMREAD_COLOR)

    decoded_objects = decode(image)
    if not decoded_objects:
        return "No QR code found in the image", 400

    attendance_marked = False

    for obj in decoded_objects:
        data = json.loads(obj.data.decode('utf-8'))
        roll_no = data['Roll No.']
        date = datetime.now().strftime('%Y-%m-%d')
        status = 'present'

        conn = sqlite3.connect('sql.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO attendance (roll_no, date, status) VALUES (?, ?, ?)', (roll_no, date, status))
        conn.commit()
        cursor.close()
        conn.close()

        attendance_marked = True

    if attendance_marked:
        return "Attendance marked successfully", 200
    else:
        return "Failed to mark attendance", 400

# Email notification function
def send_absence_notification(email, student_name, consecutive_days):
    msg = Message("Attendance Alert", recipients=[email])
    msg.body = f"Dear {student_name},\n\nYou have been absent for {consecutive_days} consecutive days. Please make sure to attend classes regularly.\n\nBest regards,\nSchool Administration"
    try:
        mail.send(msg)
        logging.info(f"Notification sent to {email} for {student_name}")
    except Exception as e:
        logging.error(f"Failed to send notification to {email}: {e}")

# Check for consecutive absences
def check_consecutive_absences():
    conn = sqlite3.connect('sql.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT u.roll_no, u.first_name, u.email, GROUP_CONCAT(a.date, ',') as absences
        FROM users u
        JOIN attendance a ON u.roll_no = a.roll_no
        WHERE a.status = 'absent'
        GROUP BY u.roll_no
    ''')
    rows = cursor.fetchall()
    
    for row in rows:
        roll_no, first_name, email, absences = row
        absence_dates = absences.split(',')

        # Check for 3 consecutive absent days
        consecutive_days = 0
        last_date = None
        for date in sorted(absence_dates):
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            if last_date and (date_obj - last_date).days == 1:
                consecutive_days += 1
            else:
                consecutive_days = 1
            if consecutive_days >= 3:
                # Send notification if not already sent
                cursor.execute('SELECT last_notified_date FROM notifications WHERE roll_no = ?', (roll_no,))
                notification_row = cursor.fetchone()
                if not notification_row or datetime.strptime(notification_row[0], '%Y-%m-%d') < date_obj - timedelta(days=3):
                    send_absence_notification(decrypt_data(email, encryption_key), decrypt_data(first_name, encryption_key), consecutive_days)
                    if notification_row:
                        cursor.execute('UPDATE notifications SET last_notified_date = ? WHERE roll_no = ?', (date_obj.strftime('%Y-%m-%d'), roll_no))
                    else:
                        cursor.execute('INSERT INTO notifications (roll_no, last_notified_date) VALUES (?, ?)', (roll_no, date_obj.strftime('%Y-%m-%d')))
                    conn.commit()
                break
            last_date = date_obj

    cursor.close()
    conn.close()

if __name__ == '__main__':
    # Set up APScheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=check_consecutive_absences, trigger="interval", days=1)
    scheduler.start()

    # Register the shutdown function to ensure scheduler is stopped gracefully
    atexit.register(lambda: scheduler.shutdown())

    app.run(debug=True)


