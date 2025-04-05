
DROP TABLE IF EXISTS course;
DROP TABLE IF EXISTS COURSE;
 

CREATE TABLE course (
    courseId VARCHAR(255) PRIMARY KEY,
    courseName VARCHAR(255) NOT NULL,
    courseDescription VARCHAR(255),
    courseContent VARCHAR(255) NOT NULL,
    courseCost DECIMAL(10,2) DEFAULT 0.00
);

INSERT INTO course (courseId, courseName, courseDescription, courseContent, courseCost) VALUES
('course_00001', 'Introduction to Python',
 'Learn the basics of Python programming, including syntax, data types, and how to create simple applications.',
 "['lesson_00001','quiz_00001','lesson_00002','quiz_00002','notes_00001']", 19.99),

('course_00002', 'Learning Mandarin',
 '你好! Learn the basics of Mandarin, including pronunciation, simple phrases, and everyday vocabulary.',
 "['lesson_00010','quiz_00011','lesson_00012','quiz_00013','notes_00014']", 24.99);
