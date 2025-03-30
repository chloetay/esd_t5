from flask import Flask, request, jsonify
import requests
from flask_cors import CORS

app = Flask(__name__)

CORS(app, resources={r"/*": {
    "origins": "http://localhost:8080",
    "methods": ["GET", "POST", "OPTIONS"],
    "allow_headers": ["Content-Type"]
}}, supports_credentials=True)

# Microservice URLs
COURSE_URL = "http://course:5000/course"
ENROLL_LOG_URL = "http://enroll-log:3000/enroll"
WALLET_GET_URL = "https://personal-rrfqkpux.outsystemscloud.com/Wallet/rest/Wallet/GetWallet"
WALLET_UPDATE_URL = "https://personal-rrfqkpux.outsystemscloud.com/Wallet/rest/Wallet/UpdateBalance"

@app.route("/enroll", methods=["POST"])
def enroll():
    data = request.json
    user_id = data.get("userId")
    course_id = data.get("courseId")
    wallet_id = data.get("walletId")
    password = data.get("walletPassword")  # reused from login

    if not user_id or not course_id or not wallet_id or not password:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # 1. Get course info
        course_resp = requests.get(f"{COURSE_URL}/{course_id}")
        course_resp.raise_for_status()
        course_data = course_resp.json().get("data", {})
        course_name = course_data.get("courseName", "Unknown Course")
        course_price = course_data.get("courseCost", 20.00)  # fallback price

        # 2. Deduct balance (assumes always successful)
        deduct_resp = requests.put(WALLET_UPDATE_URL, json={
            "ChangeAmount": -course_price,
            "WalletId": wallet_id,
            "Password": password
        })
        deduct_resp.raise_for_status()
        new_balance = deduct_resp.json().get("NewBalance")

        # 3. Log enrollment
        enroll_log_resp = requests.post(ENROLL_LOG_URL, json={
            "userId": user_id,
            "courseId": course_id
        })
        enroll_log_resp.raise_for_status()
        log_data = enroll_log_resp.json()

        # 4. Return unified result
        return jsonify({
            "message": "Enrollment successful!",
            "course": course_name,
            "wallet_balance": new_balance,
            "log_id": log_data.get("id")
        }), 200

    except requests.HTTPError as http_err:
        return jsonify({"error": "Service error", "details": str(http_err)}), 502
    except Exception as err:
        return jsonify({"error": "Internal error", "details": str(err)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
