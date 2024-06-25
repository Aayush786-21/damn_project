from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('ghar.html')

@app.route('/student')
def student():
    return render_template('student.html')

@app.route('/teacher')
def teacher():
    return render_template('teacher.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)
