# Use a lightweight Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /usr/src/app

# Copy the entire backend codebase
COPY . .

# Expose the port that the Flask app will run on
EXPOSE 8000

# Command to run your Flask app
CMD ["python", "./quiz.py"]
