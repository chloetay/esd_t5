const express = require('express');
const { Pool } = require('pg');
const bodyParser = require('body-parser');
const amqp = require('amqplib');

const app = express();
const port = 3000;

app.use(bodyParser.json());

// PostgreSQL connection
const pool = new Pool({
    user: 'postgres',
    host: 'localhost',
    database: 'enrolllog',
    password: 'Password123!',
    port: 5432,
});

// Create table if not exists
const createTable = async () => {
    const query = `CREATE TABLE IF NOT EXISTS enrollments (
        id SERIAL PRIMARY KEY,
        user_id INT NOT NULL,
        course_id INT NOT NULL,
        enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )`;
    await pool.query(query);
};

createTable().catch(err => console.error('Error creating table:', err));

// AMQP connection setup
let channel;
const queue = 'enrollmentQueue';

const setupAMQP = async () => {
    try {
        const connection = await amqp.connect('amqp://localhost');
        channel = await connection.createChannel();
        await channel.assertQueue(queue, { durable: true });
        console.log('Connected to RabbitMQ');
    } catch (error) {
        console.error('Error connecting to RabbitMQ:', error);
    }
};

setupAMQP();

// Route to handle enrollment
app.post('/enroll', async (req, res) => {
    const { userId, courseId } = req.body;
    if (!userId || !courseId) {
        return res.status(400).json({ error: 'userId and courseId are required' });
    }

    try {
        const query = 'INSERT INTO enrollments (user_id, course_id) VALUES ($1, $2) RETURNING *';
        const values = [userId, courseId];
        const result = await pool.query(query, values);
        
        // Send message to AMQP queue
        const message = JSON.stringify(result.rows[0]);
        channel.sendToQueue(queue, Buffer.from(message), { persistent: true });
        console.log('Enrollment message sent:', message);
        
        res.status(201).json(result.rows[0]);
    } catch (err) {
        console.error('Database error:', err);
        res.status(500).json({ error: 'Internal Server Error' });
    }
});

app.listen(port, () => {
    console.log(`EnrollLog service running on port ${port}`);
});
