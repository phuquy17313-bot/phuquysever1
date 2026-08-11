import threading
import time
import tkinter as tk
from tkinter import messagebox
import pyautogui
import pyperclip
import requests

SERVER_URL = "https://phuquysever1.onrender.com/verify_key"

pyautogui.PAUSE = 0.001
pyautogui.FAILSAFE = False


class KeyAuthWindow:

  def __init__(self, root):
    self.root = root
    self.root.title("XÁC THỰC KEY VIP - PHUQUY")
    self.root.geometry("380x240")
    self.root.configure(bg="#040202")

    tk.Label(
        root,
        text="🔐 HỆ THỐNG XÁC THỰC KEY VIP",
        fg="#ff0055",
        bg="#040202",
        font=("Arial", 11, "bold"),
    ).pack(pady=15)

    self.entry_key = tk.Entry(
        root, width=28, font=("Arial", 11), justify="center"
    )
    self.entry_key.pack(pady=5)
    self.entry_key.focus()

    self.btn_login = tk.Button(
        root,
        text="KÍCH HOẠT NGAY",
        bg="#dc3545",
        fg="white",
        font=("Arial", 10, "bold"),
        width=15,
        command=self.check_key_online,
    )
    self.btn_login.pack(pady=10)

    self.lbl_status = tk.Label(
        root,
        text="Chưa nhập Key hoặc nhập khơi khơi sẽ không vào được!",
        fg="#ffc107",
        bg="#040202",
        font=("Arial", 8),
    )
    self.lbl_status.pack(pady=5)

  def check_key_online(self):
    user_key = self.entry_key.get().strip()
    if not user_key:
      messagebox.showerror("Lỗi", "Vui lòng nhập key!")
      return

    try:
      response = requests.post(SERVER_URL, json={"key": user_key}, timeout=5)
      res_data = response.json()

      if res_data.get("valid"):
        duration = res_data.get("duration", 60)
        key_type = res_data.get("type", "VIP")
        messagebox.showinfo(
            "Thành Công", f"Kích hoạt thành công gói {key_type}!"
        )
        self.root.destroy()
        launch_main_app(user_key, duration)  # Truyền thêm user_key để check ngầm
      else:
        messagebox.showerror(
            "Thất Bại", "Key không tồn tại trên hệ thống hoặc chưa được tạo!"
        )
        self.entry_key.delete(0, tk.END)
    except Exception:
      messagebox.showerror(
          "Lỗi Kết Nối",
          "Không kết nối được đến server trên Render!",
      )


class ZaloSpamMaxSpeed:

  def __init__(self, root, user_key, duration):
    self.root = root
    self.root.title("PHUQUY SPAM VIP - ONLINE")
    self.root.geometry("400x360")
    self.root.configure(bg="#040202")

    self.user_key = user_key
    self.is_spamming = False
    self.session_time = duration

    self.label_msg = tk.Label(
        root,
        text="SPAM ALL NỀN TẢNG VIP:",
        fg="#ffffff",
        bg="#0b0505",
        font=("Arial", 10, "bold"),
    )
    self.label_msg.pack(pady=10)

    self.entry_msg = tk.Entry(root, width=35, font=("Arial", 11))
    self.entry_msg.pack(pady=5)
    self.entry_msg.insert(0, "Tool Spam All Nền Tảng PhuQuyVip 2026")

    self.label_guide = tk.Label(
        root,
        text="Bấm Spam Rồi Click Vào Khung Chat Với Người Bạn Muốn Spam",
        fg="#f70000",
        bg="#030202",
        font=("Arial", 9),
    )
    self.label_guide.pack(pady=10)

    self.btn = tk.Button(
        root,
        text="BẮT ĐẦU VIP",
        bg="#dc3545",
        fg="white",
        font=("Arial", 12, "bold"),
        command=self.toggle_spam,
    )
    self.btn.pack(pady=10)

    self.status_label = tk.Label(
        root,
        text="Trạng thái: Đang Chờ Lệnh",
        fg="#ffc107",
        bg="#1e1e1e",
        font=("Arial", 10),
    )
    self.status_label.pack(pady=5)

    self.lbl_session = tk.Label(
        root,
        text=f"Thời hạn Key trong giao diện: {self.session_time}s",
        fg="#00ffcc",
        bg="#040202",
        font=("Arial", 9, "bold"),
    )
    self.lbl_session.pack(pady=5)

    # Chạy đồng thời 2 luồng: Đếm ngược thời gian và Kiểm tra key ngầm với server
    threading.Thread(target=self.session_countdown, daemon=True).start()
    threading.Thread(target=self.watch_dog_key, daemon=True).start()

  def session_countdown(self):
    while self.session_time > 0:
      time.sleep(1)
      self.session_time -= 1
      try:
        mins = self.session_time // 60
        secs = self.session_time % 60
        self.lbl_session.config(
            text=f"Thời hạn Key trong giao diện: {mins:02d}:{secs:02d}"
        )
      except Exception:
        break

    self.is_spamming = False
    try:
      messagebox.showwarning(
          "Hết Hạn Key",
          "Đã hết thời hạn sử dụng, hệ thống tự động kick khỏi giao diện!",
      )
      self.root.destroy()
    except Exception:
      pass

  # Luồng kiểm tra liên tục xem key có bị xóa hay không trên server
  def watch_dog_key(self):
    while True:
      time.sleep(5)  # Cứ 5 giây check lại server một lần
      try:
        response = requests.post(
            SERVER_URL, json={"key": self.user_key}, timeout=5
        )
        res_data = response.json()
        # Nếu server báo key không còn valid (do bị xóa hoặc hết hạn)
        if not res_data.get("valid"):
          self.is_spamming = False
          try:
            messagebox.showerror(
                "Bị Thu Hồi",
                "Key của bạn đã bị xóa hoặc vô hiệu hóa bởi Admin!",
            )
            self.root.destroy()
          except Exception:
            pass
          break
      except Exception:
        pass  # Nếu mất kết nối mạng tạm thời thì bỏ qua, tránh crash tool

  def toggle_spam(self):
    if not self.is_spamming:
      message = self.entry_msg.get().strip()
      if not message:
        messagebox.showerror("Lỗi", "Hãy Nhập Nội Dung Spam")
        return

      self.is_spamming = True
      self.btn.config(text="DỪNG LẠI", bg="#6c757d")
      self.status_label.config(
          text="Trạng thái: Đang Chạy Lệnh Vip", fg="#28a745"
      )

      threading.Thread(
          target=self.run_spam, args=(message,), daemon=True
      ).start()
    else:
      self.is_spamming = False
      self.btn.config(text="BẮT ĐẦU SPAM ", bg="#dc3545")
      self.status_label.config(text="Trạng thái: Đã dừng.", fg="#ffc107")

  def run_spam(self, message):
    time.sleep(2)
    pyperclip.copy(message)

    while self.is_spamming:
      try:
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.01)
        pyautogui.press("enter")
      except Exception:
        pass

      time.sleep(0.02)

    self.status_label.config(text="Trạng thái: Đã Dừng Lệnh.", fg="#ffc107")


def launch_main_app(user_key, duration):
  main_root = tk.Tk()
  ZaloSpamMaxSpeed(main_root, user_key, duration)
  main_root.mainloop()


if __name__ == "__main__":
  auth_root = tk.Tk()
  KeyAuthWindow(auth_root)
  auth_root.mainloop()
