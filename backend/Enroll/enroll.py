from flask import Flask, request, jsonify, send_from_directory
import os
import requests

app = Flask(__name__)

# These URLs work inside Docker Compose
COURSE_URL = "http://course:5000/course"
ENROLL_LOG_URL = "http://enroll-log:3000/enroll"
WALLET_GET_URL = "https://personal-rrfqkpux.outsystemscloud.com/Wallet/rest/Wallet/GetWallet"
WALLET_UPDATE_URL = "https://personal-rrfqkpux.outsystemscloud.com/Wallet/rest/Wallet/UpdateBalance"

@app.route("/")
def serve_enroll_html():
    return send_from_directory(os.path.dirname(__file__), "enroll.html")

@app.route("/enroll", methods=["POST"])
def enroll():
    data = request.json
    user_id = data.get("userId")
    course_id = data.get("courseId")
    wallet_id = data.get("walletId")
    password = data.get("walletPassword")

    if not user_id or not course_id or not wallet_id or not password:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # Get course info
        course_resp = requests.get(f"{COURSE_URL}/{course_id}")
        course_resp.raise_for_status()
        course_data = course_resp.json()["data"]
        course_name = course_data["courseName"]
        course_price = 20

        # Get wallet balance
        wallet_resp = requests.post(WALLET_GET_URL, json={
            "WalletId": wallet_id,
            "Password": password
        })
        wallet_resp.raise_for_status()
        balance = wallet_resp.json()["Balance"]

        if balance < course_price:
            return jsonify({"error": "Insufficient wallet balance"}), 400

        # Deduct balance
        deduct_resp = requests.put(WALLET_UPDATE_URL, json={
            "ChangeAmount": -course_price,
            "WalletId": wallet_id,
            "Password": password
        })
        deduct_resp.raise_for_status()
        new_balance = deduct_resp.json()["NewBalance"]

        # Log enrollment
        enroll_log_resp = requests.post(ENROLL_LOG_URL, json={
            "userId": user_id,
            "courseId": course_id
        })
        enroll_log_resp.raise_for_status()
        log_data = enroll_log_resp.json()

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
