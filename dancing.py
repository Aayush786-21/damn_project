from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Temporary storage for registered students and teachers
students = []
teachers = []

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

@app.route('/register_student', methods=['POST'])
def register_student():
    student_name = request.form['student_name']
    student_id = request.form['student_id']
    students.append({'name': student_name, 'id': student_id})
    return redirect(url_for('admin_dashboard'))

@app.route('/register_teacher', methods=['POST'])
def register_teacher():
    teacher_name = request.form['teacher_name']
    teacher_id = request.form['teacher_id']
    teachers.append({'name': teacher_name, 'id': teacher_id})
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
