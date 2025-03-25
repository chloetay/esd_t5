from flask import Flask, jsonify, request, abort, make_response
from pymongo import MongoClient
from pydantic import BaseModel
from typing import Dict
from flask_cors import CORS
import os

# Load the MongoDB password from environment variables
db_password = os.getenv("db_password", "NewSecurePassword123")

# MongoDB Connection
MONGO_URI = f"mongodb+srv://jovibong2023:{db_password}@cluster0.yflll.mongodb.net/ESD?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client["ESD"]
collection = db["quiz"]

app = Flask(__name__)
CORS(app)  # Allow all origins for now

@app.route("/", methods=["GET"])
def home():
    response = make_response(jsonify({"message": "Welcome to the Flask Quiz Microservice!"}))
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

@app.route("/quiz/<string:quizid>", methods=["GET"])
def get_quiz(quizid: str):
    quiz = collection.find_one({"quizid": quizid}, {"_id": 0})
    if not quiz:
        abort(404, description="Quiz not found")
    response = make_response(jsonify(quiz))
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

@app.route("/quiz", methods=["GET"])
def get_all_quizzes():
    quizzes = list(collection.find({}, {"_id": 0}))
    if not quizzes:
        abort(404, description="No quizzes found")
    response = make_response(jsonify(quizzes))
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

@app.route("/submit_quiz", methods=["POST"])
def submit_quiz():
    response_data = request.json
    if not response_data or not response_data.get("quizid") or not response_data.get("answers"):
        abort(400, description="Invalid request data")
    
    quiz = collection.find_one({"quizid": response_data["quizid"]}, {"_id": 0})
    if not quiz:
        abort(404, description="Quiz not found")

    correct_answers = {str(i): q["correctAnswer"] for i, q in enumerate(quiz["questions"])}
    score = sum(1 for key in response_data["answers"] if response_data["answers"].get(key) == correct_answers.get(key))

    response = make_response(jsonify({"quizid": response_data["quizid"], "score": score, "total_questions": len(quiz["questions"])}))
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
