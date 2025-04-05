const express = require('express');
const { Pool } = require('pg');
const bodyParser = require('body-parser');
const amqp = require('amqplib');

const app = express();
const port = 3000;
app.use(bodyParser.json());

const pool = new Pool({
    user: 'postgres',
    host: 'pgdb',  // ✅ Must match service name in Docker Compose
    database: 'enrolllog',
    password: 'Password123!',
    port: 5432,
});

const queue = 'enrollmentQueue';
let channel;

// ✅ Create table if it doesn't exist
const createTable = async () => {
    const query = `CREATE TABLE IF NOT EXISTS enrollments (
        id SERIAL PRIMARY KEY,
      user_id TEXT NOT NULL,
      course_id TEXT NOT NULL,
      enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )`;
    await pool.query(query);
};

// ✅ Retry PostgreSQL until it's ready
const connectPostgresWithRetry = async () => {
    for (let attempt = 1; attempt <= 10; attempt++) {
        try {
            await pool.query('SELECT 1');
            console.log('✅ Connected to PostgreSQL');
            await createTable();
            return;
        } catch (err) {
            console.error(`❌ PostgreSQL not ready (attempt ${attempt})... retrying in 3s`);
            await new Promise(res => setTimeout(res, 3000));
        }
    }
};

// ✅ Retry RabbitMQ until it's ready
const setupAMQP = async () => {
    for (let attempt = 1; attempt <= 10; attempt++) {
        try {
            const connection = await amqp.connect('amqp://rabbitmq');
            channel = await connection.createChannel();
            await channel.assertQueue(queue, { durable: true });
            console.log('✅ Connected to RabbitMQ');
            return;
        } catch (error) {
            console.error(`❌ RabbitMQ not ready (attempt ${attempt})... retrying in 3s`);
            await new Promise(res => setTimeout(res, 3000));
        }
    }
};

// ✅ API endpoint for /enroll
app.post('/enroll', async (req, res) => {
    const { userId, courseId } = req.body;

    if (!userId || !courseId) {
        return res.status(400).json({ error: 'Missing userId or courseId' });
    }

    try {
        const insertQuery = `
            INSERT INTO enrollments (user_id, course_id)
            VALUES ($1, $2)
            RETURNING id
        `;
        const result = await pool.query(insertQuery, [userId, courseId]);
        const logId = result.rows[0].id;

        // ✅ Optionally send to RabbitMQ
        if (channel) {
            const msg = JSON.stringify({ userId, courseId, logId });
            channel.sendToQueue(queue, Buffer.from(msg), { persistent: true });
        }

        res.status(201).json({ id: logId });
    } catch (err) {
        console.error('❌ Failed to log enrollment:', err);
        res.status(500).json({ error: 'Failed to log enrollment' });
    }
});

// ✅ Start the server
app.listen(port, () => {
    console.log(`✅ EnrollLog service listening on port ${port}`);
});

// 🔁 Start setup
connectPostgresWithRetry();
setupAMQP();
