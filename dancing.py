from flask import Flask, render_template, redirect, url_for, request, jsonify
import qrcode
import os
import sqlite3
import cv2
import numpy as np
from pyzbar.pyzbar import decode

app = Flask(__name__)

#static folder exists for saving QR codes
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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT,
            date TEXT,
            status TEXT
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

@app.route('/student_records')
def student_records():
    conn = sqlite3.connect('sql.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE role="student"')
    records = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('student_records.html', records=records)

@app.route('/teacher_records')
def teacher_records():
    conn = sqlite3.connect('sql.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE role="teacher"')
    records = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('teacher_records.html', records=records)

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    data = request.get_json()
    roll_no = data.get('roll_no')
    date = data.get('date')
    status = data.get('status')

    conn = sqlite3.connect('sql.db')
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO attendance (roll_no, date, status)
        VALUES (?, ?, ?)
    """, (roll_no, date, status))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Attendance marked successfully"}), 200


@app.route('/read_qr', methods=['GET', 'POST'])
def read_qr():
    if request.method == 'POST':
        cap = cv2.VideoCapture(0)
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            decoded_objects = decode(frame)
            for obj in decoded_objects:
                data = obj.data.decode('utf-8')
                details = json.loads(data)
                roll_no = details.get('Roll No.')
                if roll_no:
                    mark_attendance(roll_no, 'present')
                    cap.release()
                    cv2.destroyAllWindows()
                    return jsonify({"status": "success", "roll_no": roll_no})

            cv2.imshow('QR Code Scanner', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()
        return jsonify({"status": "failed"})

    return render_template('read_qr.html')

if __name__ == '__main__':
    app.run(debug=True)
