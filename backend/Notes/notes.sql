CREATE DATABASE IF NOT EXISTS notes_db;
USE notes_db;

DROP TABLE IF EXISTS notes;

CREATE TABLE notes (
    notes_id VARCHAR(255) PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL
);

-- Add example rows (make sure these files exist in your /notes folder)
INSERT INTO notes (notes_id, file_name) VALUES
("notes_00001", 'Data_Structures.pdf'),
("notes_00002", 'notes2.pdf'),
("notes_00003", 'notes3.pdf');
