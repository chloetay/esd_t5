CREATE DATABASE IF NOT EXISTS notes_db;
USE notes_db;

DROP TABLE IF EXISTS notes;

CREATE TABLE notes (
    notes_id VARCHAR(255) PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL
);

-- Add example rows (make sure these files exist in your /notes folder)
INSERT INTO notes (notes_id, file_name) VALUES
("N001", 'Data_Structures.pdf');
