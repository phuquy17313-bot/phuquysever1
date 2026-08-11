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

# Giao diện Web Trang Chủ (Tạo Key)
HTML_INTERFACE = """
<!DOCTYPE html>
<html>
<head>
    <title>PhuQuy Key Admin</title>
    <style>
        body { font-family: Arial; background: #1a1a1a; color: white; text-align: center; padding: 30px; }
        .box { background: #2d2d2d; padding: 20px; border-radius: 10px; display: inline-block; width: 380px; }
        input, select { width: 100%; padding: 10px; margin: 10px 0; border-radius: 5px; border: none; }
        button { background: #00ff00; border: none; padding: 12px; width: 100%; font-weight: bold; cursor: pointer; color: black; margin-top: 5px; }
        .btn-list { background: #ffc107; }
        #result { margin-top: 15px; color: yellow; word-break: break-all; font-weight: bold; }
    </style>
</head>
<body>
    <div class="box">
        <h2>HỆ THỐNG TẠO KEY</h2>
        <select id="type"><option value="VIP">VIP</option><option value="LITE">LITE</option></select>
        <input type="number" id="duration" placeholder="Thời hạn (giây, ví dụ 86400)">
        <button onclick="createKey()">TẠO KEY NGAY</button>
        <button class="btn-list" onclick="window.location.href='/list-keys'">XEM TẤT CẢ KEY</button>
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
    try:
        cursor.execute("INSERT INTO keys (key, key_type, duration, activated_at) VALUES (?, ?, ?, ?)", 
                       (new_key, k_type, duration, None))
        conn.commit()
        return f"Đã tạo thành công {k_type} ({duration}s)"
    except:
        return "Key đã tồn tại!"
    finally:
        conn.close()

# API Xóa Key
@app.route("/delete-key", methods=["GET"])
def delete_key():
    key = request.args.get("key")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM keys WHERE key = ?", (key,))
    conn.commit()
    conn.close()
    return "Đã xóa"

# API Reset / Tạm dừng key (Lưu lại thời gian còn lại, ngắt kích hoạt)
@app.route("/reset-key", methods=["GET"])
def reset_key():
    key = request.args.get("key")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT duration, activated_at FROM keys WHERE key = ?", (key,))
    row = cursor.fetchone()
    if row:
        duration, activated_at = row
        if activated_at is not None:
            elapsed = time.time() - activated_at
            remaining = max(0, duration - elapsed)
            cursor.execute("UPDATE keys SET duration = ?, activated_at = NULL WHERE key = ?", (int(remaining), key))
        else:
            # Nếu chưa active mà bấm reset thì đưa về trạng thái ban đầu nếu cần
            cursor.execute("UPDATE keys SET activated_at = NULL WHERE key = ?", (key,))
        conn.commit()
    conn.close()
    return "Đã reset"

# Trang danh sách quản lý Key có nút Xóa và Reset
@app.route("/list-keys", methods=["GET"])
def list_keys():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT key, key_type, duration, activated_at FROM keys")
    rows = cursor.fetchall()
    conn.close()

    current_time = time.time()

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Quản Lý Key</title>
        <meta http-equiv="refresh" content="5">
        <style>
            body { font-family: Arial; background: #1a1a1a; color: white; padding: 20px; }
            table { width: 100%; border-collapse: collapse; background: #2d2d2d; margin-top: 20px; }
            th, td { border: 1px solid #444; padding: 10px; text-align: center; }
            th { background: #333; color: #00ff00; }
            a { color: #ffc107; text-decoration: none; font-weight: bold; }
            .active { color: #00ff00; font-weight: bold; }
            .expired { color: #ff4444; font-weight: bold; }
            .unused { color: #ffc107; }
            .btn-action { padding: 5px 10px; cursor: pointer; font-weight: bold; border-radius: 4px; border: none; }
            .btn-reset { background: #ffc107; color: black; margin-right: 5px; }
            .btn-delete { background: #dc3545; color: white; }
        </style>
        <script>
            function deleteKey(key) {
                if(confirm('Chắc chắn muốn xóa key: ' + key + ' ?')) {
                    fetch('/delete-key?key=' + key).then(() => location.reload());
                }
            }
            function resetKey(key) {
                if(confirm('Reset/Tạm dừng key này về trạng thái chờ nhập lại?')) {
                    fetch('/reset-key?key=' + key).then(() => location.reload());
                }
            }
        </script>
    </head>
    <body>
        <h2>QUẢN LÝ DANH SÁCH KEY</h2>
        <a href="/">⬅ Quay lại trang chủ tạo key</a>
        <table>
            <tr>
                <th>Key</th>
                <th>Loại</th>
                <th>Thời hạn chuẩn</th>
                <th>Trạng thái / Thời gian</th>
                <th>Hành động</th>
            </tr>
    """
    for row in rows:
        k, k_type, duration, activated_at = row
        
        if activated_at is None:
            status_text = f"<span class='unused'>Chưa kích hoạt ({duration}s)</span>"
        else:
            elapsed = current_time - activated_at
            remaining = duration - elapsed
            if remaining > 0:
                mins = int(remaining // 60)
                secs = int(remaining % 60)
                hours = mins // 60
                mins = mins % 60
                status_text = f"<span class='active'>Đang chạy: {hours}h {mins}m {secs}s</span>"
            else:
                status_text = "<span class='expired'>Đã hết hạn</span>"

        html += f"""
        <tr>
            <td><b>{k}</b></td>
            <td>{k_type}</td>
            <td>{duration}s</td>
            <td>{status_text}</td>
            <td>
                <button class="btn-action btn-reset" onclick="resetKey('{k}')">Reset</button>
                <button class="btn-action btn-delete" onclick="deleteKey('{k}')">Xóa</button>
            </td>
        </tr>
        """

    html += "</table></body></html>"
    return html

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
