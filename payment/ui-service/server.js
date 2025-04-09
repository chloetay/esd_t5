const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 3003;

// Simple HTTP server that serves the index.html file
const server = http.createServer((req, res) => {
  // Just serve the index.html file for all requests
  const filePath = path.join(__dirname, 'index.html');
  
  fs.readFile(filePath, (err, content) => {
    if (err) {
      res.writeHead(500);
      res.end(`Error loading index.html: ${err.message}`);
      return;
    }
    
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(content, 'utf-8');
  });
});

server.listen(PORT, () => {
  console.log(`UI service running at http://localhost:${PORT}`);
});