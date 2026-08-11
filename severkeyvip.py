import os
import sqlite3
import time
import random
import string
from flask import Flask, jsonify, request, render_template_string

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

# Giao diện Web đẹp (HTML/CSS)
HTML_INTERFACE = """
<!DOCTYPE html>
<html>
<head>
    <title>PhuQuy Key Admin</title>
    <style>
        body { font-family: Arial; background: #1a1a1a; color: white; text-align: center; padding: 50px; }
        .box { background: #2d2d2d; padding: 20px; border-radius: 10px; display: inline-block; width: 350px; }
        input, select { width: 100%; padding: 10px; margin: 10px 0; border-radius: 5px; }
        button { background: #00ff00; border: none; padding: 15px; width: 100%; font-weight: bold; cursor: pointer; }
        #result { margin-top: 20px; color: yellow; word-break: break-all; }
    </style>
</head>
<body>
    <div class="box">
        <h2>HỆ THỐNG TẠO KEY</h2>
        <select id="type"><option value="VIP">VIP</option><option value="LITE">LITE</option></select>
        <input type="number" id="duration" placeholder="Thời hạn (giây, ví dụ 86400)">
        <button onclick="createKey()">TẠO KEY NGAY</button>
        <div id="result"></div>
    </div>
    <script>
        function createKey() {
            let key = 'PHUQUY-' + Math.random().toString(36).substr(2, 9).toUpperCase();
            let type = document.getElementById('type').value;
            let duration = document.getElementById('duration').value || 86400;
            fetch(`/add-key?key=${key}&type=${type}&duration=${duration}`)
                .then(res => res.text()).then(data => {
                    document.getElementById('result').innerText = "Key: " + key + "\\n" + data;
                });
        }
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def home():
    return render_template_string(HTML_INTERFACE)

@app.route("/add-key", methods=["GET"])
def add_key():
    new_key = request.args.get("key")
    k_type = request.args.get("type", "VIP")
    duration = int(request.args.get("duration", 86400))
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO keys (key, key_type, duration, activated_at) VALUES (?, ?, ?, ?)", 
                   (new_key, k_type, duration, None))
    conn.commit()
    conn.close()
    return f"Đã tạo thành công {k_type} ( {duration}s )"

@app.route("/verify_key", methods=["POST"])
def verify_key():
    data = request.json
    user_key = data.get("key", "").strip()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT key_type, duration, activated_at FROM keys WHERE key = ?", (user_key,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({"valid": False})
    
    key_type, duration, activated_at = row
    current_time = time.time()
    
    if activated_at is None:
        cursor.execute("UPDATE keys SET activated_at = ? WHERE key = ?", (current_time, user_key))
        conn.commit()
        remaining = duration
    else:
        remaining = int(duration - (current_time - activated_at))
    
    conn.close()
    return jsonify({"valid": remaining > 0, "type": key_type, "duration": max(0, remaining)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
