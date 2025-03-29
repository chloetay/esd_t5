from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from os import environ

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('dbURL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

db = SQLAlchemy(app)

class Course(db.Model):
    __tablename__ = 'course'

    courseID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    courseName = db.Column(db.String(100), nullable=False)
    courseCategory = db.Column(db.String(100), nullable=False)
    numberOfLessons = db.Column(db.Integer, nullable=False)

    def __init__(self, courseName, courseCategory, numberOfLessons):
        self.courseName = courseName
        self.courseCategory = courseCategory
        self.numberOfLessons = numberOfLessons

    def json(self):
        return {
            "courseID": self.courseID,
            "courseName": self.courseName,
            "courseCategory": self.courseCategory,
            "numberOfLessons": self.numberOfLessons
        }

@app.route("/course")
def get_all():
    courselist = db.session.scalars(db.select(Course)).all()
    if courselist:
        return jsonify(
            {
                "code": 200,
                "data": {
                    "courses": [course.json() for course in courselist]
                }
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "There are no courses."
        }
    ), 404

@app.route("/course/<int:courseID>")
def find_by_id(courseID):
    course = db.session.scalar(
        db.select(Course).filter_by(courseID=courseID)
    )

    if course:
        return jsonify(
            {
                "code": 200,
                "data": course.json()
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "Course not found."
        }
    ), 404

@app.route("/course", methods=['POST'])
def create_course():
    data = request.get_json()
    course = Course(**data)

    try:
        db.session.add(course)
        db.session.commit()
    except:
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred creating the course."
            }
        ), 500

    return jsonify(
        {
            "code": 201,
            "data": course.json()
        }
    ), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
