# QR Dance

QR Dance is a Python Flask-based application designed to manage student attendance using QR codes. This project allows administrators to register students, capture attendance via QR codes, and view attendance records. 

## Features

- Register students
- Capture attendance via QR codes
- View attendance records by month and year
- Handle holidays and weekends in attendance records
- Send automated email notifications for consecutive absences
- Encrypt sensitive user data
- User-friendly interface with Bootstrap styling

## Prerequisites

- Python 3.x
- Flask
- Flask-Mail
- OpenCV
- SQLite3
- Pyzbar
- Cryptography
- Bootstrap
- APScheduler

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/your-username/qr_dance.git
    cd qr_dance
    ```

2. Create and activate a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

4. Set up the database:
    ```bash
    python setup_database.py
    ```

## Usage

1. Run the Flask application:
    ```bash
    flask run
    ```

2. Open your web browser and go to `http://127.0.0.1:5000`.

3. Use the application to register users, capture attendance, and view records.

## Project Structure

- `dancing.py`: Main application file with Flask routes, email notifications, and encryption
- `templates/`: HTML templates
  - `ghar.html`: Home page
  - `register.html`: Registration page for students
  - `student_records.html`: Page to view student attendance records
  - `login.html`: Dashboard for admin
  - `signup.html`: Admin signup page
  - `qr_review.html`: Page to display QR code and user details
- `static/`: Static files (CSS, JavaScript, QR code images)
- `setup_database.py`: Script to set up the SQLite database
- `secret.key`: File storing the encryption key (automatically generated if not found)

## Screenshots

### Home Page
![Home Page]
![alt text](<Screenshot from 2024-09-12 12-43-19.png>)

### Register Page
![Register Page]
![alt text](<Screenshot from 2024-09-12 12-38-56.png>)

### Student Records Page
![Student Records Page]
![alt text](<Screenshot from 2024-08-11 14-25-04.png>)

## Contributing

Feel free to submit issues and pull requests. For major changes, please open an issue first to discuss what you would like to change.
