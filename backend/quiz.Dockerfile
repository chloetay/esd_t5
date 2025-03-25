# Use a lightweight Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /usr/src/app

# Copy requirements and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend codebase
COPY . .

# Expose the port that the Flask app will run on
EXPOSE 8000

# Command to run your Flask app
CMD ["python", "./quiz.py"]
