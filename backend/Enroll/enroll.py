from flask import Flask, request, jsonify
import requests
from flask_cors import CORS

app = Flask(__name__)

# CORS configuration for frontend access
CORS(app, resources={r"/*": {
    "origins": ["http://localhost:8080", "http://0.0.0.0:8080"],
    "methods": ["GET", "POST", "OPTIONS"],
    "allow_headers": ["Content-Type"]
}}, supports_credentials=True)


# Microservice URLs
COURSE_URL = "http://course:5000/course"
ENROLL_LOG_URL = "http://enroll-log:3000/enroll"
WALLET_GET_URL = "https://personal-rrfqkpux.outsystemscloud.com/Wallet/rest/Wallet/GetWallet"
WALLET_UPDATE_URL = "https://personal-rrfqkpux.outsystemscloud.com/Wallet/rest/Wallet/UpdateBalance"
ENROLL_ERROR_URL = "http://enroll-error:5004/validate"

@app.route("/enroll", methods=["POST", "OPTIONS"])
def enroll():
    if request.method == "OPTIONS":
        # Preflight CORS request
        return '', 204
    data = request.json
    print("📨 Received enroll POST with data:", data)

    user_id = data.get("userId")
    course_id = data.get("courseId")
    wallet_id = data.get("walletId")
    password = data.get("walletPassword")

    if not user_id or not course_id or not wallet_id or not password:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # Step 1: Call enroll-error microservice to validate
        print("🔍 Calling enroll-error for validation...")
        check_resp = requests.post(ENROLL_ERROR_URL, json=data)
        print("📥 Validation response:", check_resp.status_code)
        check_data = check_resp.json()

        if check_resp.status_code != 200:
            print("❌ Validation failed:", check_data)
            return jsonify(check_data), 400

        # Step 2: Get course info
        print("📡 Fetching course info...")
        course_resp = requests.get(f"{COURSE_URL}/{course_id}")
        print("📥 Course response:", course_resp.status_code)
        course_resp.raise_for_status()
        course_data = course_resp.json().get("data", {})
        course_name = course_data.get("courseName", "Unknown Course")
        course_price = course_data.get("courseCost", 20.00)
        print("💰 Course name:", course_name)
        print("💰 Course price fetched:", course_price)

        # Step 3: Deduct balance
        wallet_payload = {
            "ChangeAmount": -course_price,
            "WalletId": wallet_id,
            "Password": password
        }
        print("💳 Deducting from wallet:", wallet_payload)
        deduct_resp = requests.put(WALLET_UPDATE_URL, json=wallet_payload)
        print("📥 Wallet update response:", deduct_resp.status_code)
        wallet_response = deduct_resp.json()
        print("📥 Wallet update response JSON:", wallet_response)

        if wallet_response.get("Status") != "Ok":
            print("❌ Wallet update failed")
            return jsonify({
                "error": "Wallet update failed",
                "details": wallet_response.get("ErrorMessage", "Unknown error")
            }), 400

        new_balance = wallet_response.get("NewBalance")
        print("🧾 New balance:", new_balance)

        # Step 4: Log enrollment
        enroll_log_payload = {
            "userId": user_id,
            "courseId": course_id
        }
        print("📝 Logging enrollment:", enroll_log_payload)
        enroll_log_resp = requests.post(ENROLL_LOG_URL, json=enroll_log_payload)
        print("📥 Enroll log response:", enroll_log_resp.status_code)
        enroll_log_resp.raise_for_status()
        log_data = enroll_log_resp.json()

        # Step 5: Final response
        response = {
            "message": "Enrollment successful!",
            "course": course_name,
            "wallet_balance": new_balance,
            "log_id": log_data.get("id")
        }
        print("✅ Final response:", response)
        return jsonify(response), 200

    except requests.HTTPError as http_err:
        print("❌ HTTP Error:", http_err)
        return jsonify({"error": "Service error", "details": str(http_err)}), 502
    except Exception as err:
        print("❌ Unexpected error:", err)
        return jsonify({"error": "Internal error", "details": str(err)}), 500
    
@app.route("/profile", methods=["POST"])
def profile():
    data = request.json
    user_id = data.get("userId")
    wallet_id = data.get("walletId")
    password = data.get("walletPassword")

    if not user_id or not wallet_id or not password:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # 1. Get wallet balance
        wallet_resp = requests.post(WALLET_GET_URL, json={
            "WalletId": wallet_id,
            "Password": password
        })
        wallet_resp.raise_for_status()
        wallet_data = wallet_resp.json()
        balance = wallet_data.get("Balance")

        # 2. Get enrolled courses from enroll-log
        enrollments_resp = requests.get("http://enroll-log:3000/enrollments")
        enrollments_resp.raise_for_status()
        all_enrollments = enrollments_resp.json()

        enrolled_course_ids = [
            e["course_id"] for e in all_enrollments if e["user_id"] == user_id
        ]

        # 3. Fetch all course info
        course_resp = requests.get("http://course:5000/course")
        course_resp.raise_for_status()
        all_courses = course_resp.json()["data"]["courses"]

        enrolled_courses = [
            c for c in all_courses if c["courseId"] in enrolled_course_ids
        ]

        return jsonify({
            "balance": balance,
            "courses": enrolled_courses
        })

    except requests.RequestException as e:
        return jsonify({"error": "Failed to load profile", "details": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
