from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Database config
dbURL = os.environ.get('dbURL')
app.config['SQLALCHEMY_DATABASE_URI'] = dbURL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ✅ NEW Course Model
class Course(db.Model):
    __tablename__ = 'course'

    courseId = db.Column(db.String(255), primary_key=True)
    courseName = db.Column(db.String(255), nullable=False)
    courseDescription = db.Column(db.String(255))
    courseContent = db.Column(db.String(255), nullable=False)
    courseCost = db.Column(db.Numeric(10, 2), default=0.00)

    def json(self):
        return {
            "courseId": self.courseId,
            "courseName": self.courseName,
            "courseDescription": self.courseDescription,
            "courseContent": self.courseContent,
            "courseCost": float(self.courseCost)
        }

@app.route("/course")
def get_all_courses():
    courses = Course.query.all()
    return jsonify({
        "code": 200,
        "data": {
            "courses": [course.json() for course in courses]
        }
    }), 200

@app.route("/course/<string:course_id>")
def get_course_by_id(course_id):
    course = Course.query.filter_by(courseId=course_id).first()
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

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
