FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment
ENV PYTHONUNBUFFERED=1

# Expose the port
EXPOSE 5001

# Run the app
CMD ["python", "takeCourse.py"]
