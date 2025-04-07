CREATE DATABASE IF NOT EXISTS course;
USE course;

-- NOTES DB
DROP TABLE IF EXISTS notes;

CREATE TABLE notes (
    courseId VARCHAR(10),
    notesId VARCHAR(191),
    fileName VARCHAR(255) NOT NULL,
    PRIMARY KEY (courseId, notesId)
);

INSERT INTO notes (courseId, notesId, fileName) VALUES
("C001", "N001", 'Data_Structures.pdf');


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
'["L001","L002","Q001","L003","Q002","N001","L004","Q003"]',
10.00),
("C002", "Learning Mandarin", 
"你好! Learn the basics of Mandarin, including pronunciation, simple phrases, and everyday vocabulary. Perfect for travelers and language enthusiasts.",
'["L001","Q001","L002","Q002","N002"]',
15.00), 
("C003", "Web Development 101",
"Get started with web development by learning HTML, CSS, and JavaScript. Build your first interactive website from scratch.",
'["L001","Q001","L002","Q002","N001"]',
20.00),

("C004", "Financial Literacy Basics",
"Understand the essentials of personal finance, including budgeting, saving, investing, and debt management.",
'["L001","Q001","L002","Q002","N001"]',
12.00),

("C005", "Digital Marketing Essentials",
"Learn the fundamentals of digital marketing such as SEO, social media strategy, email marketing, and content creation.",
'["L001","Q001","L002","Q002","N001"]',
18.00),

("C006", "Mindfulness and Stress Management",
"Explore practical techniques to manage stress, improve focus, and live mindfully in a busy world.",
'["L001","Q001","L002","Q002","N001"]',
8.00),

("C007", "Graphic Design with Canva",
"Create eye-catching visuals using Canva. Learn basic design principles and how to design for social media, presentations, and more.",
'["L001","Q001","L002","Q002","N001"]',
10.00);



