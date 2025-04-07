# Use a lightweight Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /usr/src/app

# Copy the app files and requirements
COPY . .

# Install required Python packages from requirements.txt
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Expose the port that the Flask app will run on
EXPOSE 8000

# Command to run your Flask app
CMD ["python", "quiz.py"]
