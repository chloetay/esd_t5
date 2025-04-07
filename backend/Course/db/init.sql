
DROP TABLE IF EXISTS course;
DROP TABLE IF EXISTS COURSE;
 

CREATE TABLE course (
    courseId VARCHAR(255) PRIMARY KEY,
    courseName VARCHAR(255) NOT NULL,
    courseDescription VARCHAR(255),
    courseContent VARCHAR(255) NOT NULL,
    courseCost DECIMAL(10,2) DEFAULT 0.00
);


 INSERT INTO COURSE (courseId, courseName, courseDescription, courseContent, courseCost) VALUES
("C001", "Introduction to Python", 
"Learn the basics of Python programming, including syntax, data types, and how to create simple applications. This course is perfect for beginners with no prior coding experience.",
'["L001","Q001","L002","Q002","N001"]',
10.00),
("C002", "Learning Mandarin", 
"你好! Learn the basics of Mandarin, including pronunciation, simple phrases, and everyday vocabulary. Perfect for travelers and language enthusiasts.",
'["L001","Q001","L002","Q002","N002"]',
15.00);
