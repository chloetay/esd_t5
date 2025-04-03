from flask import Flask, jsonify, request, abort
from pydantic import BaseModel, ValidationError
from typing import Optional
import requests
import os
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
from cachetools import TTLCache

# Initialize Flask app
app = Flask(__name__)

# Configuration
COURSE_SERVICE_URL = os.getenv("COURSE_SERVICE_URL", "http://course:5000")
COURSE_LOGS_URL = os.getenv("COURSE_LOGS_URL", "http://courselogs:5003")
QUIZ_SERVICE_URL = os.getenv("QUIZ_SERVICE_URL", "http://quiz-service:8000")

# Caching
course_cache = TTLCache(maxsize=100, ttl=3600)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic Models
class CourseRequest(BaseModel):
    courseId: str
    userId: str

# Resilient HTTP Client
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    before_sleep=lambda _: logger.warning("Retrying due to failure...")
)
def fetch_service_data(url: str, params: Optional[dict] = None):
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch {url}: {str(e)}")
        raise

# Service Integration Functions
def get_course_details(course_id: str) -> dict:
    """Fetch course metadata with caching"""
    if course_id in course_cache:
        return course_cache[course_id]
    
    url = f"{COURSE_SERVICE_URL}/course/{course_id}"
    response = fetch_service_data(url)
    if not response or response.get("code") != 200:
        raise ValueError(f"Course {course_id} not found")
    
    course_cache[course_id] = response["data"]
    return response["data"]

def get_user_progress(course_id: str, user_id: str) -> dict:
    """Fetch user progress from courselogs"""
    url = f"{COURSE_LOGS_URL}/courseLogs/{course_id}/{user_id}"
    response = fetch_service_data(url)
    if not response.get("data"):
        # Initialize progress if not found
        init_response = requests.post(
            f"{COURSE_LOGS_URL}/courseLogs",
            json={"courseId": course_id, "userId": user_id, "completedItems": []}
        )
        if init_response.status_code != 200:
            raise ValueError("Failed to initialize user progress")
        return {"completedItems": []}
    return response["data"]

def get_quiz_data(quiz_id: str) -> dict:
    """Fetch quiz from quiz service"""
    url = f"{QUIZ_SERVICE_URL}/quiz/{quiz_id}"
    return fetch_service_data(url)

def determine_next_items(course: dict, completed_items: list) -> Optional[str]:
    """
    Enhanced progression logic based on course structure
    Returns the next quiz ID or None if course completed
    """
    course_quizzes = course.get("quizIds", [])
    completed_quizzes = {item["quizId"] for item in completed_items if "quizId" in item}
    
    for quiz_id in course_quizzes:
        if quiz_id not in completed_quizzes:
            return quiz_id
    return None

# Main Endpoint
@app.route("/takecourse", methods=["GET"])
def get_course_materials():
    try:
        # Validate input
        request_data = CourseRequest(**request.args)
        
        # 1. Get course metadata
        course = get_course_details(request_data.courseId)
        
        # 2. Get user progress
        progress = get_user_progress(request_data.courseId, request_data.userId)
        
        # 3. Determine next quiz based on course structure
        quiz_id = determine_next_items(course, progress["completedItems"])
        
        if not quiz_id:
            return jsonify({
                "course": course,
                "progress": progress,
                "message": "Course completed"
            })
        
        # 4. Get quiz data
        quiz = get_quiz_data(quiz_id)
        
        return jsonify({
            "course": course,
            "quiz": quiz,
            "progress": progress,
            "nextAction": f"Take quiz {quiz_id}"
        })
    
    except ValidationError as e:
        abort(400, description=str(e))
    except requests.exceptions.RequestException as e:
        abort(502, description=f"Backend service error: {str(e)}")
    except ValueError as e:
        abort(404, description=str(e))

# Quiz Submission Endpoint
@app.route("/takecourse/submit", methods=["POST"])
def submit_quiz():
    try:
        data = request.json
        if not all(k in data for k in ["courseId", "userId", "quizId", "answers"]):
            abort(400, description="Missing required fields")
        
        # 1. Submit to quiz service
        quiz_result = requests.post(
            f"{QUIZ_SERVICE_URL}/submit_quiz",
            json={"quizid": data["quizId"], "answers": data["answers"]}
        ).json()
        
        # 2. Update progress if passed (>= 80%)
        if quiz_result["score"] / quiz_result["total_questions"] >= 0.8:
            update_data = {
                "courseId": data["courseId"],
                "userId": data["userId"],
                "completedItems": [{"quizId": data["quizId"]}]
            }
            requests.post(f"{COURSE_LOGS_URL}/courseLogs", json=update_data)
        
        return jsonify(quiz_result)
    
    except requests.exceptions.RequestException as e:
        abort(502, description=f"Quiz service error: {str(e)}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)