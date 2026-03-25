-- Create the database
CREATE DATABASE
IF NOT EXISTS dropout_prediction;
USE dropout_prediction;

-- Create the Student table
CREATE TABLE
IF NOT EXISTS Student
(
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR
(100) NOT NULL,
    gender VARCHAR
(20) DEFAULT 'Girl',
    age INT,
    class_name VARCHAR
(50),
    school_name VARCHAR
(100),
    location VARCHAR
(100),
    attendance INT,
    marks INT,
    parental_support VARCHAR
(20),
    family_income VARCHAR
(20),
    transport_safety VARCHAR
(20),
    early_marriage_pressure VARCHAR
(20),
    risk_label VARCHAR
(20),
    risk_score INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
