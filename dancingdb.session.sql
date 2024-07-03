-- USE qr_dance;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    role VARCHAR(50),
    first_name VARCHAR(50),
    middle_name VARCHAR(50),
    last_name VARCHAR(50),
    roll_no VARCHAR(50),
    address TEXT,
    email VARCHAR(100),
    qr_code_path VARCHAR(255)
);
