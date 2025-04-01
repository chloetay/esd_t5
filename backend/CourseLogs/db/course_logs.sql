-- Create the table
CREATE TABLE IF NOT EXISTS course_logs (
    courseId VARCHAR(255) NOT NULL,
    userId VARCHAR(255) NOT NULL,
    completedItems JSON NOT NULL,
    PRIMARY KEY (courseId, userId)
);

-- Insert sample data
INSERT INTO course_logs (courseId, userId, completedItems) VALUES
('C101', 'U001', JSON_ARRAY(
    JSON_OBJECT('lessonId', 'L001'),
    JSON_OBJECT('quizId', 'Q001')
)),
('C101', 'U002', JSON_ARRAY(
    JSON_OBJECT('lessonId', 'L002'),
    JSON_OBJECT('lessonId', 'L003')
)),
('C102', 'U001', JSON_ARRAY(
    JSON_OBJECT('quizId', 'Q002')
));
