CREATE DATABASE IF NOT EXISTS ESD_PROJECT;
USE ESD_PROJECT;

-- NOTES DB
DROP TABLE IF EXISTS NOTES;

CREATE TABLE NOTES (
    notesId VARCHAR(255) PRIMARY KEY,
    fileName VARCHAR(255) NOT NULL
);

INSERT INTO NOTES (notesId, fileName) VALUES
("notes_00001", 'Data_Structures.pdf')

-- COURSES DB
DROP TABLE IF EXISTS COURSES;

CREATE TABLE COURSE (
    courseId VARCHAR(255) PRIMARY KEY,
    courseName VARCHAR(255) NOT NULL,
    courseDescription VARCHAR(255),
    courseContent VARCHAR(255) NOT NULL,
    courseCost DECIMAL(10,2) DEFAULT 0.00
);

INSERT INTO COURSES (courseId, courseName, courseDescription) VALUES
("course_00001", "Introduction to Python", 
"Learn the basics of Python programming, including syntax, data types, and how to create simple applications. This course is perfect for beginners with no prior coding experience.",
"['lesson_00001','quiz_00001','lesson_00002','quiz_00002','notes_00001']"),
("course_00002", "Learning Mandarin", 
" 你好! Learn the basics of Mandarin, including pronunciation, simple phrases, and everyday vocabulary. Perfect for travelers and language enthusiasts.",
"['lesson_00010','quiz_00011','lesson_00012','quiz_00013','notes_00014']")


