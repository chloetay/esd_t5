from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
from sqlalchemy.orm.attributes import flag_modified

app = Flask(__name__)
CORS(app)

# Database configuration
dbURL = os.environ.get('dbURL') or 'mysql+mysqlconnector://is213:password@mysql:3306/course'
app.config['SQLALCHEMY_DATABASE_URI'] = dbURL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Model definition
class CourseLog(db.Model):
    __tablename__ = 'course_logs'

    courseId = db.Column(db.String(255), primary_key=True)
    userId = db.Column(db.String(255), primary_key=True)
    completedItems = db.Column(db.JSON, nullable=False)

    def json(self):
        return {
            "courseId": self.courseId,
            "userId": self.userId,
            "completedItems": self.completedItems
        }

# Routes
@app.route("/<string:courseId>/<string:userId>", methods=['GET'])
def get_course_logs(courseId, userId):
    log = CourseLog.query.filter_by(courseId=courseId, userId=userId).first()
    if log:
        return jsonify({
            "code": 200,
            "data": log.json()
        }), 200
    return jsonify({
        "code": 404,
        "message": "Course log not found"
    }), 404

@app.route("/", methods=['POST'])
def add_or_update_course_log():
    data = request.get_json()
    courseId = data.get('courseId')
    userId = data.get('userId')
    completedItem = data.get('completedItem')

    if not all([courseId, userId, completedItem]) or not isinstance(completedItem, str):
        return jsonify({
            "code": 400,
            "message": "Missing or invalid fields: courseId, userId, completedItem"
        }), 400

    # Check if log exists
    log = CourseLog.query.filter_by(courseId=courseId, userId=userId).first()

    if log:
        # Append item if not already in list
        if completedItem not in log.completedItems:
            log.completedItems.append(completedItem)
            flag_modified(log, "completedItems")
    else:
        # Create new log entry with one item
        log = CourseLog(
            courseId=courseId,
            userId=userId,
            completedItems=[completedItem]
        )
        db.session.add(log)

    db.session.commit()

    return jsonify({
        "code": 200,
        "message": "Course log updated",
        "data": log.json()
    }), 200

@app.route("/<string:courseId>/<string:userId>", methods=['DELETE'])
def delete_course_log(courseId, userId):
    log = CourseLog.query.filter_by(courseId=courseId, userId=userId).first()
    if log:
        db.session.delete(log)
        db.session.commit()
        return jsonify({
            "code": 200,
            "message": f"Course log for user '{userId}' and course '{courseId}' deleted."
        }), 200
    return jsonify({
        "code": 404,
        "message": "Course log not found"
    }), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)
