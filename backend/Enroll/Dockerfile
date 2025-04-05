FROM python:3.10

WORKDIR /app
COPY . /app

# ✅ Install requirements (this line is key)
RUN pip install -r requirements.txt

CMD ["python", "-u", "enroll.py"]
