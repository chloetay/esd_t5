# Use Node.js base image
FROM node:18

# Set working directory inside the container
WORKDIR /app

# Copy all files into the container
COPY . .

# Install dependencies from package.json
RUN npm install

# Expose the port the service listens on
EXPOSE 3000

# Run the app
CMD ["node", "EnrollLog.js"]
