# Use a lightweight Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy the enroll script
COPY enroll.py .

# Install dependencies
RUN pip install flask requests

# Expose the port the app runs on
EXPOSE 5002

# Start the app
CMD ["python", "enroll.py"]
