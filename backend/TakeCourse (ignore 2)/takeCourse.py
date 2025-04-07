# takecourse/app.py
from flask import Flask, jsonify
import requests
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

COURSE_SERVICE_URL = os.getenv("COURSE_SERVICE_URL", "http://course:5000")
COURSE_LOGS_URL = os.getenv("COURSE_LOGS_URL", "http://course-logs:5003")
LESSON_SERVICE_URL = os.getenv("LESSON_SERVICE_URL", "http://lesson:5005/LessonService/rest/LessonAPI")
QUIZ_SERVICE_URL = os.getenv("QUIZ_SERVICE_URL", "http://quiz:8000")

@app.route("/takecourse/<string:courseId>/<string:userId>", methods=["GET"])
def take_course(courseId, userId):
    # 1. Get user progress
    logs_resp = requests.get(f"{COURSE_LOGS_URL}/courseLogs/{courseId}/{userId}")
    completed_items = []
    if logs_resp.status_code == 200:
        completed_items = logs_resp.json().get("data", {}).get("completedItems", [])
        completed_items = [list(item.keys())[0] for item in completed_items]

    # 2. Get lessons
    lessons_resp = requests.get(f"{LESSON_SERVICE_URL}/lesson/by-course/{courseId}")
    lessons = []
    if lessons_resp.status_code == 200:
        lessons = lessons_resp.json()

    # 3. Get quizzes
    quizzes_resp = requests.get(f"{QUIZ_SERVICE_URL}/quiz")
    quizzes = []
    if quizzes_resp.status_code == 200:
        quizzes = [q for q in quizzes_resp.json() if q.get("courseId") == courseId]

    # 4. Construct unified content list
    content_items = []
    for lesson in sorted(lessons, key=lambda x: x["lessonId"]):
        content_items.append((f"lesson_{lesson['lessonId']}", "lesson", lesson))
    for quiz in sorted(quizzes, key=lambda x: x.get("quizid")):
        content_items.append((f"quiz_{quiz['quizid']}", "quiz", quiz))

    # 5. Determine next incomplete item
    for item_key, item_type, item_data in content_items:
        if item_key not in completed_items:
            if item_type == "lesson":
                detail_resp = requests.get(f"{LESSON_SERVICE_URL}/lesson/{courseId}/{item_data['lessonId']}")
                if detail_resp.status_code == 200:
                    return jsonify({
                        "code": 200,
                        "data": {
                            "nextItem": {
                                "type": "lesson",
                                "title": detail_resp.json().get("title"),
                                "content": detail_resp.json().get("content")
                            }
                        }
                    }), 200
            elif item_type == "quiz":
                detail_resp = requests.get(f"{QUIZ_SERVICE_URL}/quiz/{item_data['quizid']}")
                if detail_resp.status_code == 200:
                    return jsonify({
                        "code": 200,
                        "data": {
                            "nextItem": {
                                "type": "quiz",
                                "title": item_data.get("title", "Quiz"),
                                "questions": item_data.get("questions")
                            }
                        }
                    }), 200

    return jsonify({
        "code": 200,
        "message": "Course completed"
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
