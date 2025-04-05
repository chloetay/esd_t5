from flask import Flask, request, jsonify
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Service URLs
WALLET_GET_URL = "https://personal-rrfqkpux.outsystemscloud.com/Wallet/rest/Wallet/GetWallet"
ENROLL_LOG_URL = "http://enroll-log:3000/enrollments"

@app.route("/enroll-error", methods=["POST"])
def validate_enroll():
    data = request.json
    user_id = data.get("userId")
    wallet_id = data.get("walletId")
    password = data.get("walletPassword")
    course_id = data.get("courseId")
    course_price = data.get("courseCost", 20.00)  # fallback

    if not user_id or not wallet_id or not password or not course_id:
        return jsonify({"valid": False, "error": "Missing required fields"}), 400

    try:
        # 1. Check if user is already enrolled
        enroll_check = requests.get(ENROLL_LOG_URL)
        enroll_check.raise_for_status()
        existing_enrollments = enroll_check.json()

        for record in existing_enrollments:
            if record.get("user_id") == int(user_id) and record.get("course_id") == course_id:
                return jsonify({"valid": False, "error": "Already enrolled in this course"}), 409

        # 2. Check wallet balance
        wallet_resp = requests.post(WALLET_GET_URL, json={
            "WalletId": wallet_id,
            "Password": password
        })
        wallet_resp.raise_for_status()
        wallet_data = wallet_resp.json()
        current_balance = float(wallet_data.get("Balance", 0))

        if current_balance < float(course_price):
            return jsonify({
                "valid": False,
                "error": f"Insufficient balance: {current_balance} < {course_price}"
            }), 402

        # ✅ All validations passed
        return jsonify({"valid": True}), 200

    except requests.HTTPError as http_err:
        return jsonify({"valid": False, "error": f"Service error: {str(http_err)}"}), 502
    except Exception as err:
        return jsonify({"valid": False, "error": f"Internal error: {str(err)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=True)
