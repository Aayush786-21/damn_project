**Introduction**
In today's fast-paced world, efficient and accurate attendance tracking is crucial for educational institutions and companies alike. Traditional methods of attendance management often prove to be time-consuming, error-prone, and cumbersome. To address these challenges, we have developed QR Dance, an innovative web application that leverages QR code technology to streamline the process of attendance tracking. QR Dance is designed to offer a seamless and intuitive experience for students, teachers, and administrators. By generating personalized QR codes, users can quickly and effortlessly record their attendance, ensuring precise and timely data collection. The application features a robust system that captures and timestamps QR code scans, allowing for real-time monitoring and analysis of attendance records. The application is accessible through a user-friendly interface where students and teachers can generate their unique QR codes by entering their name and roll number. These codes are then used daily to mark attendance via a system camera. Administrators have access to a comprehensive dashboard that displays attendance data in an easily interpretable format, highlighting punctuality and tardiness with distinct color codes. QR Dance also includes a premium feature, offering a dark mode for enhanced user experience, available for a one-time purchase through the eSewa payment system. Developed using Python and the Flask framework, and built in the vs code, QR Dance is a testament to modern web development capabilities and innovative problem-solving. Through QR Dance, we aim to empower institutions with a reliable, efficient, and user-friendly solution for attendance management, enhancing productivity and ensuring accurate record-keeping.

**System Architecture**
- Phase 1: Initial setup with dancing.py , student.html , admin.html , login.html , and teacher.html .
- Phase 2: Added register.html .
- Phase 3: Added qr_review.html .
- Phase 4: Integrated qr_review.html  route and added SQLite database.
- Phase 5: Set up virtual environment.
- Phase 6: Added student_records.html  and teacher_records.html .
- Phase 7: Integrated camera using cv2 .
- Phase 8: Added QR code reader functionality.
- Phase 9: Enhanced student_records.html  with new designs and features.
- Phase 10: Added Jenkinsfile  for continuous integration.
- phase 11: Added DESCRIPTION.MD for better understanding of the application.
- phase 12: Added session to get rid of vunerablities.
- phase 13: Redesigned register.html and implemented "unique roll no."
- phase 14: Added data encryption algorithm. 
- phase 15: Added a way of viewing students details in students records by clicking their names

**User Interface Design**
- Home Page (ghar.html): Landing page with navigation to student, teacher, and admin sections.
- Student Page: Interface for students to generate and scan QR codes.
- Teacher Page: Interface for teachers to manage attendance.
- Admin Page: Login and dashboard for administrators to monitor attendance data.
- Register Page: Form for new users to register and generate QR codes.
- QR Review Page: Displays generated QR code and user details.
- Student Records Page: Displays attendance records for students.
- Teacher Records Page: Displays records for teachers.
- Flowcharts: Include flowcharts to depict the user journey and interactions within the application.

**Component Design**
- dancing.py: Main application file handling routes and logic.
- HTML Templates: ghar.html , student.html , admin.html , login.html , teacher.html , register.html , qr_review.html , student_records.html , teacher_records.html .
- Database: SQLite database for storing user and attendance data.
- Camera Integration: Using cv2  for QR code scanning.
- QR Code Generation: Using qrcode  library to generate QR codes.
- Interaction Between Components: Describe how different components interact with each other to achieve the desired functionality.

**Data Design**
- User Table: Stores user information including role, name, roll number, address, email, and QR code path.
- Attendance Table: Stores attendance records with roll number, date, and status.

**Security Considerations**
- Authentication: Admin login with username and password.
- Data Validation: Ensuring unique roll numbers and valid data entries.
- Secure Storage: Storing QR codes and user data securely.

**Performance Metrics**
- Response Time: Ensuring quick generation and scanning of QR codes.
- Scalability: Ability to handle multiple users and large attendance data.

**Testing Strategy**
- Unit Testing: Testing individual components and functions.
- Integration Testing: Ensuring all components work together seamlessly.

**Third-Party Libraries and Tools**
- Flask: Web framework for building the application.
- qrcode: Library for generating QR codes.
- cv2: OpenCV library for camera integration.
- sqlite3: Database for storing user and attendance data.
- Jenkins: For continuous integration and deployment.

**Maintenance and Support**
- Version Control: Maintain a version history within the document.
- Updates: Regular updates and improvements based on user feedback.

**Future Enhancements and Scalability**
- Feature Expansion: Potential new features and improvements.
- Scalability: Plans for scaling the application to handle more users and data.


