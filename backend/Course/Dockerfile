FROM python:3.10-slim

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN pip install flask flask_sqlalchemy mysql-connector-python

EXPOSE 5000

CMD ["python", "course.py"]
