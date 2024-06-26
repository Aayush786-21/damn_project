from flask import Flask, render_template, redirect, url_for, request
import qrcode
import os
import random
import string

app = Flask(__name__)

# Ensure the static folder exists for saving QR codes
if not os.path.exists('static'):
    os.makedirs('static')

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

        # Create unique identifier
        unique_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        details = f"Role: {role}\nFirst Name: {first_name}\nMiddle Name: {middle_name}\nLast Name: {last_name}\nRoll No.: {roll_no}\nAddress: {address}\nEmail: {email}\nUnique ID: {unique_id}"

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
        qr_code_path = os.path.join('static', f'qr_{unique_id}.png')
        img.save(qr_code_path)

        return render_template('qr_review.html', details=details, qr_code_url=qr_code_path)
    return render_template('register.html')

@app.route('/qr_review')
def qr_review():
    return render_template('qr_review.html')

if __name__ == '__main__':
    app.run(debug=True)
