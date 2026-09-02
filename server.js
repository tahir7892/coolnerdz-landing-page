const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3003;
const DB_FILE = path.join(__dirname, 'db.sqlite3');

app.use(express.json());
app.use(express.static(__dirname));

// Initialize SQLite database
const db = new sqlite3.Database(DB_FILE, (err) => {
  if (err) {
    console.error('Error opening database', err.message);
  } else {
    db.run(`
      CREATE TABLE IF NOT EXISTS waitlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        role TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);
  }
});

app.post('/api/waitlist', (req, res) => {
  const { email, role } = req.body;

  if (!email || !role) {
    return res.status(400).json({ error: 'Email and role are required.' });
  }

  // Insert into SQLite, utilizing UNIQUE constraint on email
  const sql = `INSERT INTO waitlist (email, role) VALUES (?, ?)`;
  db.run(sql, [email, role], function (err) {
    if (err) {
      if (err.message.includes('UNIQUE constraint failed')) {
        return res.status(409).json({ error: 'This email is already on the waitlist.' });
      }
      console.error(err);
      return res.status(500).json({ error: 'An error occurred while saving your submission.' });
    }
    
    return res.status(201).json({ message: 'You\'re on the waitlist! We\'ll be in touch soon.' });
  });
});

app.get('/api/waitlist', (req, res) => {
  const sql = `SELECT id, email, role, created_at FROM waitlist ORDER BY created_at DESC`;
  db.all(sql, [], (err, rows) => {
    if (err) {
      console.error(err);
      return res.status(500).json({ error: 'Error fetching waitlist records.' });
    }
    return res.json({ success: true, count: rows.length, data: rows });
  });
});

app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
  console.log(`Waitlist entries will be saved to SQLite database: ${DB_FILE}`);
});
