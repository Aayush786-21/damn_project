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
from datetime import datetime, timedelta, date
import json
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from cryptography.fernet import Fernet, InvalidToken
import logging
import calendar

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
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS holidays (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    holiday_date TEXT
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
    try:
        year = int(request.args.get('year', datetime.now().year))
        month = int(request.args.get('month', datetime.now().month))
    except ValueError:
        year = datetime.now().year
        month = datetime.now().month

    holidays = [
        '2024-01-01', '2024-02-20', '2024-03-21', '2024-04-14',
        '2024-05-01', '2024-06-01', '2024-07-16', '2024-08-15',
        '2024-09-25', '2024-10-05', '2024-11-01', '2024-12-25'
    ]

    num_days = calendar.monthrange(year, month)[1]
    days = [f"{year}-{month:02d}-{day:02d}" for day in range(1, num_days + 1)]
    today = datetime.now().strftime("%Y-%m-%d")

    conn = sqlite3.connect('sql.db')
    cursor = conn.cursor()
    cursor.execute('SELECT first_name, last_name, roll_no, email FROM users')
    students_data = cursor.fetchall()

    students = {}
    for student in students_data:
        roll_no = student[2]
        students[roll_no] = {
            'name': f"{decrypt_data(student[0], encryption_key)} {decrypt_data(student[1], encryption_key)}",
            'email': decrypt_data(student[3], encryption_key),
            'attendance': {}
        }
        for day in days:
            if day in holidays or datetime.strptime(day, '%Y-%m-%d').weekday() == 5:  # Mark Saturdays and holidays
                students[roll_no]['attendance'][day] = 'Holiday'
            elif day > today:
                students[roll_no]['attendance'][day] = 'Upcoming'
            else:
                cursor.execute('SELECT status FROM attendance WHERE roll_no = ? AND date = ?', (roll_no, day))
                result = cursor.fetchone()
                students[roll_no]['attendance'][day] = result[0] if result else 'Absent'

    conn.close()

    month_name = datetime(year, month, 1).strftime('%B')

    return render_template('student_records.html', 
                           students=students, 
                           days=days, 
                           selected_year=year, 
                           selected_month=month,
                           month_name=month_name,
                           holidays=holidays)

@app.route('/teacher_records', methods=['GET'])
def teacher_records():
    year = request.args.get('year', datetime.now().year)
    month = request.args.get('month', datetime.now().month)
    
    # List of holidays for the year
    holidays = [
        '2024-01-01', '2024-02-20', '2024-03-21', '2024-04-14',
        '2024-05-01', '2024-06-01', '2024-07-16', '2024-08-15',
        '2024-09-25', '2024-10-05', '2024-11-01', '2024-12-25'
    ]

    num_days = calendar.monthrange(int(year), int(month))[1]
    days = [datetime(int(year), int(month), day).strftime('%Y-%m-%d') for day in range(1, num_days + 1)]

    conn = sqlite3.connect('sql.db')
    cursor = conn.cursor()
    cursor.execute('SELECT first_name, last_name, roll_no FROM users WHERE role = ?', (encrypt_data('teacher', encryption_key),))
    teachers = cursor.fetchall()

    attendance_records = []
    for teacher in teachers:
        teacher_attendance = {
            'first_name': decrypt_data(teacher[0], encryption_key),
            'last_name': decrypt_data(teacher[1], encryption_key),
            'roll_no': teacher[2],
            'attendance': {}
        }
        for day in days:
            if day in holidays or datetime.strptime(day, '%Y-%m-%d').weekday() == 5:  # Mark Saturdays and holidays
                teacher_attendance['attendance'][day] = 'Holiday'
            else:
                cursor.execute('SELECT status FROM attendance WHERE roll_no = ? AND date = ?', (teacher[2], day))
                result = cursor.fetchone()
                teacher_attendance['attendance'][day] = result[0] if result else 'Absent'
        attendance_records.append(teacher_attendance)

    conn.close()

    current_year = datetime.now().year
    current_month = datetime.now().month

    return render_template('teacher_records.html', attendance_records=attendance_records, current_year=current_year, current_month=current_month)

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    logging.info("Received request to mark attendance")
    
    if 'qr_data' not in request.form:
        logging.error("No QR data provided in the request")
        return jsonify({"error": "No QR data provided"}), 400

    qr_data = request.form['qr_data']
    logging.info(f"Received QR data: {qr_data}")

    try:
        data = json.loads(qr_data)

    except json.JSONDecodeError as e:
        logging.error(f"Error decoding QR data: {str(e)}")
        return jsonify({"error": "Invalid QR data"}), 400

    roll_no = data.get('Roll No.')
    if not roll_no:
        logging.warning("Roll No. not found in QR data")
        return jsonify({"error": "Roll No. not found in QR data"}), 400

    date = datetime.now().strftime('%Y-%m-%d')
    status = 'present'

    try:
        conn = sqlite3.connect('sql.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO attendance (roll_no, date, status) VALUES (?, ?, ?)', (roll_no, date, status))
        conn.commit()
        cursor.close()
        conn.close()
        logging.info(f"Attendance marked for roll_no: {roll_no}")
        
        student_name = f"{data.get('First Name', '')} {data.get('Last Name', '')}".strip()
        return jsonify({
            "message": "Attendance marked successfully",
            "students": [{"roll_no": roll_no, "name": student_name}]
        }), 200
    except Exception as e:
        logging.error(f"Error marking attendance: {str(e)}")
        return jsonify({"error": "Failed to mark attendance"}), 400
    
def capture_qr():
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        for barcode in decode(frame):
            qr_data = barcode.data.decode('utf-8')
            data = json.loads(qr_data)

            mark_attendance(data['Roll No.'], 'Present')

            pts = np.array([barcode.polygon], np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv2.polylines(frame, [pts], True, (0, 255, 0), 3)
            cv2.putText(frame, 'Attendance Marked', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            break

        cv2.imshow('QR Code Scanner', frame)
        if cv2.waitKey(1) == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def send_email_notification(roll_no):
    conn = sqlite3.connect('sql.db')
    cursor = conn.cursor()
    cursor.execute('SELECT email FROM users WHERE roll_no = ?', (roll_no,))
    result = cursor.fetchone()
    if result:
        email = decrypt_data(result[0], encryption_key)
        msg = Message('Attendance Alert', sender='nobusparkhere@gmail.com', recipients=[email])
        msg.body = f'Dear Student, you have been absent for three consecutive days. Please ensure to attend classes regularly.'
        try:
            mail.send(msg)
            logging.info(f"Notification sent to {email}")
        except Exception as e:
            logging.error(f"Failed to send email notification: {e}")
    cursor.close()
    conn.close()

def check_consecutive_absences():
    conn = sqlite3.connect('sql.db')
    cursor = conn.cursor()
    cursor.execute('SELECT roll_no FROM users WHERE role = ?', (encrypt_data('student', encryption_key),))
    students = cursor.fetchall()


    for student in students:
        roll_no = student[0]
        cursor.execute('''
            SELECT date, status FROM attendance
            WHERE roll_no = ? AND status = 'Absent'
            ORDER BY date DESC
            LIMIT 3
        ''', (roll_no,))
        absences = cursor.fetchall()

        if len(absences) == 3:
            last_three_dates = [datetime.strptime(record[0], '%Y-%m-%d') for record in absences]
            if (last_three_dates[0] - last_three_dates[2]).days == 2:
                cursor.execute('SELECT last_notified_date FROM notifications WHERE roll_no = ?', (roll_no,))
                notification = cursor.fetchone()
                if notification:
                    last_notified_date = datetime.strptime(notification[0], '%Y-%m-%d')
                    if (datetime.now() - last_notified_date).days >= 7:
                        send_email_notification(roll_no)
                        cursor.execute('UPDATE notifications SET last_notified_date = ? WHERE roll_no = ?', (datetime.now().strftime('%Y-%m-%d'), roll_no))
                else:
                    send_email_notification(roll_no)
                    cursor.execute('INSERT INTO notifications (roll_no, last_notified_date) VALUES (?, ?)', (roll_no, datetime.now().strftime('%Y-%m-%d')))
                conn.commit()

    cursor.close()
    conn.close()

scheduler = BackgroundScheduler()
scheduler.add_job(func=check_consecutive_absences, trigger="interval", days=1)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    app.run(debug=True, port=5001)