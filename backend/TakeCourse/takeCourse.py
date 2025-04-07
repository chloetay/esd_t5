from flask import Flask, jsonify
import requests
import os
import json
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Microservice URLs for course and course logs
COURSE_SERVICE_URL = os.getenv("COURSE_SERVICE_URL", "http://course:5000")
COURSE_LOGS_URL = os.getenv("COURSE_LOGS_URL", "http://course-logs:5003")

@app.route("/takeCourse/<string:courseId>/<string:userId>", methods=["GET"])
def take_course(courseId, userId):
    try:
        # 1. Get course info
        course_resp = requests.get(f"{COURSE_SERVICE_URL}/course/{courseId}")
        if course_resp.status_code != 200:
            return jsonify({"code": 404, "message": "Course not found"}), 404
        course_info = course_resp.json().get("data", {})
        course_content = json.loads(course_info.get("courseContent", "[]"))

        # 2. Get completed items from course logs
        logs_resp = requests.get(f"{COURSE_LOGS_URL}/courseLogs/{courseId}/{userId}")
        completed_items = []
        if logs_resp.status_code == 200:
            completed_items = logs_resp.json().get("data", {}).get("completedItems", [])

        # 3. Loop through course content
        for item_id in course_content:
            if item_id in completed_items:
                continue

            prefix = item_id[0].upper()

            if prefix == "L":
                return jsonify({
                    "code": 200,
                    "data": {
                        "redirectUrl": f"lesson.html?courseId={courseId}&lessonId={item_id}"
                    }
                }), 200

            elif prefix == "Q":
                return jsonify({
                    "code": 200,
                    "data": {
                        "redirectUrl": f"quiz.html?courseId={courseId}&quizId={item_id}"
                    }
                }), 200

            elif prefix == "N":
                return jsonify({
                    "code": 200,
                    "data": {
                        "redirectUrl": f"notes.html?courseId={courseId}&notesId={item_id}"
                    }
                }), 200

        # 4. All items completed
        return jsonify({
            "code": 200,
            "message": "Course completed"
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"Internal server error: {str(e)}"
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
