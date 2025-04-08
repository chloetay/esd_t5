FROM node:16-alpine

WORKDIR /app

# Copy application files
COPY index.html .
COPY server.js .

# Expose port
EXPOSE 3000

# Start the application
CMD ["node", "server.js"]