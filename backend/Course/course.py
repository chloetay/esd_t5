from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Get the DB URL from environment variable
dbURL = os.environ.get('dbURL')

# SQLAlchemy config
app.config['SQLALCHEMY_DATABASE_URI'] = dbURL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Course Model
class Course(db.Model):
    __tablename__ = 'course'

    courseID = db.Column(db.Integer, primary_key=True)
    courseName = db.Column(db.String(255), nullable=False)
    courseCategory = db.Column(db.String(100))
    numberOfLessons = db.Column(db.Integer)

    def json(self):
        return {
            "courseID": self.courseID,
            "courseName": self.courseName,
            "courseCategory": self.courseCategory,
            "numberOfLessons": self.numberOfLessons
        }

# GET all courses
@app.route("/course")
def get_all_courses():
    courses = Course.query.all()
    return jsonify({
        "code": 200,
        "data": {
            "courses": [course.json() for course in courses]
        }
    }), 200

# GET course by ID
@app.route("/course/<int:course_id>")
def get_course_by_id(course_id):
    course = Course.query.filter_by(courseID=course_id).first()
    if course:
        return jsonify({
            "code": 200,
            "data": course.json()
        }), 200
    else:
        return jsonify({
            "code": 404,
            "message": "Course not found"
        }), 404

# Run server
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
