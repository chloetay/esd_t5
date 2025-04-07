CREATE DATABASE IF NOT EXISTS ESD_PROJECT;
USE ESD_PROJECT;

-- NOTES DB
DROP TABLE IF EXISTS NOTES;

CREATE TABLE NOTES (
    notesId VARCHAR(191) PRIMARY KEY,
    fileName VARCHAR(255) NOT NULL
);

INSERT INTO NOTES (notesId, fileName) VALUES
("notes_00001", 'Data_Structures.pdf');

-- COURSES DB
DROP TABLE IF EXISTS course;

CREATE TABLE course (
    courseId VARCHAR(191) PRIMARY KEY,
    courseName VARCHAR(255) NOT NULL,
    courseDescription TEXT,
    courseContent TEXT NOT NULL,
    courseCost DECIMAL(10,2) DEFAULT 0.00
);

INSERT INTO course (courseId, courseName, courseDescription, courseContent, courseCost) VALUES
("C001", "Introduction to Python", 
"Learn the basics of Python programming, including syntax, data types, and how to create simple applications. This course is perfect for beginners with no prior coding experience.",
'["L001","Q001","L002","Q002","N001"]',
10.00),
("C002", "Learning Mandarin", 
"你好! Learn the basics of Mandarin, including pronunciation, simple phrases, and everyday vocabulary. Perfect for travelers and language enthusiasts.",
'["L001","Q001","L002","Q002","N002"]',
15.00);
