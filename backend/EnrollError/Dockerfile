FROM python:3.9-slim
WORKDIR /app
COPY . /app
RUN pip install flask flask-cors requests
CMD ["python", "enroll_error.py"]
