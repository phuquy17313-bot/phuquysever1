import os
import sqlite3
import time
from flask import Flask, jsonify, request

DB_NAME = "keys.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS keys (
            key TEXT PRIMARY KEY,
            key_type TEXT,
            duration INTEGER,
            activated_at REAL
        )
    """)
    conn.commit()
    conn.close()


init_db()

app = Flask(__name__)


@app.route("/", methods=["GET"])
def home():
    return "PhuQuy Key Server is running 24/7!"


# === THÊM ĐOẠN NÀY ĐỂ TẠO KEY TRỰC TIẾP ===
@app.route("/add-key", methods=["GET"])
def add_key():
    new_key = request.args.get("key")  # Lấy key từ link
    k_type = request.args.get("type", "VIP")
    duration = int(request.args.get("duration", 86400))  # Mặc định 1 ngày (86400 giây)
    
    if not new_key:
        return "Lỗi: Vui lòng nhập key! Ví dụ: /add-key?key=PHUQUY-VIP123"
        
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO keys (key, key_type, duration, activated_at) VALUES (?, ?, ?, ?)",
            (new_key, k_type, duration, None)
        )
        conn.commit()
        return f"Đã tạo thành công key: {new_key} (Loại: {k_type}, Thời hạn: {duration} giây)"
    except sqlite3.IntegrityError:
        return f"Lỗi: Key '{new_key}' đã tồn tại trong database rồi!"
    finally:
        conn.close()
# ==========================================


@app.route("/verify_key", methods=["POST"])
def verify_key():
    data = request.json
    if not data:
        return jsonify({"valid": False, "message": "Thiếu dữ liệu JSON!"})
        
    user_key = data.get("key", "").strip()

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT key_type, duration, activated_at FROM keys WHERE key = ?",
        (user_key,),
    )
    row = cursor.fetchone()

    if not row:
        conn.close()
        return jsonify({"valid": False, "message": "Key không tồn tại!"})

    key_type, duration, activated_at = row
    current_time = time.time()

    if activated_at is None:
        cursor.execute(
            "UPDATE keys SET activated_at = ? WHERE key = ?",
            (current_time, user_key),
        )
        conn.commit()
        remaining = duration
    else:
        elapsed = current_time - activated_at
        remaining = int(duration - elapsed)

    conn.close()

    if remaining <= 0:
        return jsonify({"valid": False, "message": "Key đã hết hạn sử dụng!"})

    return jsonify({"valid": True, "type": key_type, "duration": remaining})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
