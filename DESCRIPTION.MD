# QR Dance

QR Dance is a Python Flask-based application designed to manage student attendance using QR codes. This project allows administrators to register students and teachers, capture attendance via QR codes, and view attendance records. 

## Features

- Register students and teachers
- Capture attendance via QR codes
- View attendance records by month and year
- User-friendly interface with Bootstrap styling

## Prerequisites

- Python 3.x
- Flask
- OpenCV
- SQLite3
- Bootstrap

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

- `app.py`: Main application file
- `templates/`: HTML templates
  - `index.html`: Home page
  - `register.html`: Registration page for students and teachers
  - `student_records.html`: Page to view student attendance records
  - `admin.html`: Admin panel (to be customized as per requirements)
- `static/`: Static files (CSS, JavaScript)
- `setup_database.py`: Script to set up the SQLite database

## Screenshots

### Home Page
![Home Page]
![alt text](<Screenshot from 2024-07-17 13-49-10.png>)
### Register Page
![Register Page]
![alt text](<Screenshot from 2024-07-17 13-51-22.png>)
### Student Records Page
![Student Records Page]
![alt text](<Screenshot from 2024-07-17 13-52-16.png>)
## Contributing

Feel free to submit issues and pull requests. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License.
