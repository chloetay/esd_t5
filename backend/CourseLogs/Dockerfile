FROM python:3.10-slim

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN pip install flask flask_sqlalchemy mysql-connector-python

EXPOSE 5003

CMD ["python", "course_logs.py"]
