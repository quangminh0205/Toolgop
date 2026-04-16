import requests
import json
import time
import random
import re
import glob
import os
from pystyle import Colors, Colorate
import sys
from time import sleep
import httpx
import ssl
import certifi
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
import requests
from time import sleep
from urllib.parse import urlparse
import os
import re
import sys
import time
import json
import requests
from time import sleep
from urllib.parse import urlparse

class Treoanhmess:
    def __init__(self, cookie):
        self.cookie = cookie
        self.user_id = self.id_user()
        self.fb_dtsg = None
        self.jazoest = None
        self.init_params()

    # ================= LẤY USER ID =================
    def id_user(self):
        try:
            return re.search(r"c_user=(\d+)", self.cookie).group(1)
        except:
            raise Exception("Cookie không hợp lệ")

    # ================= INIT FB PARAM =================
    def init_params(self):
        headers = {
            "Cookie": self.cookie,
            "User-Agent": "Mozilla/5.0"
        }

        r = requests.get("https://www.facebook.com", headers=headers)
        fb = re.search(r'"token":"(.*?)"', r.text)
        jz = re.search(r'name="jazoest" value="(\d+)"', r.text)

        if not fb:
            r = requests.get("https://mbasic.facebook.com", headers=headers)
            fb = re.search(r'name="fb_dtsg" value="(.*?)"', r.text)
            jz = re.search(r'name="jazoest" value="(\d+)"', r.text)

        if not fb:
            raise Exception("Không lấy được fb_dtsg")

        self.fb_dtsg = fb.group(1)
        self.jazoest = jz.group(1) if jz else "22036"

    # ================= UPLOAD ẢNH / VIDEO =================
    def upload_media(self, media_url):
        # bỏ query ?ex=... để không lỗi tên file
        filename = os.path.basename(urlparse(media_url).path.split("?")[0])
        if not filename:
            return None, None

        try:
            r = requests.get(media_url, timeout=30)
            if r.status_code != 200:
                return None, None
            with open(filename, "wb") as f:
                f.write(r.content)
        except:
            return None, None

        is_video = filename.lower().endswith(".mp4")

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Origin": "https://www.facebook.com",
            "Referer": "https://www.facebook.com/"
        }

        params = {
            "__user": self.user_id,
            "fb_dtsg": self.fb_dtsg,
            "__a": "1",
            "__req": "1",
            "__comet_req": "15"
        }

        cookies = {
            k.strip(): v for k, v in
            (x.split("=") for x in self.cookie.split(";") if "=" in x)
        }

        try:
            print("[📤] Upload VIDEO MP4..." if is_video else "[📤] Upload ẢNH...")

            # 🔑 FIX CHÍNH: dùng with open để đóng file
            with open(filename, "rb") as f:
                if is_video:
                    files = {
                        "upload_video": (filename, f, "video/mp4")
                    }
                else:
                    files = {
                        "upload_1024": (filename, f, "image/jpeg")
                    }

                res = requests.post(
                    "https://www.facebook.com/ajax/mercury/upload.php",
                    headers=headers,
                    params=params,
                    cookies=cookies,
                    files=files
                )

            if res.status_code != 200:
                return None, None

            data = json.loads(res.text.replace("for (;;);", ""))
            meta = data.get("payload", {}).get("metadata", {})

            for k in meta:
                if is_video and meta[k].get("video_id"):
                    print("✅ Upload video thành công")
                    return "video", meta[k]["video_id"]
                if not is_video and meta[k].get("image_id"):
                    print("✅ Upload ảnh thành công")
                    return "image", meta[k]["image_id"]

        except Exception as e:
            print("Lỗi upload:", e)

        finally:
            try:
                os.remove(filename)
            except:
                pass

        return None, None

    # ================= GỬI TIN NHẮN =================
    def gui_tn(self, recipient_id, message, media_type=None, media_id=None):
        self.init_params()
        ts = int(time.time() * 1000)

        data = {
            "thread_fbid": recipient_id,
            "action_type": "ma-type:user-generated-message",
            "body": message,
            "client": "mercury",
            "author": f"fbid:{self.user_id}",
            "timestamp": ts,
            "source": "source:chat:web",
            "offline_threading_id": ts,
            "message_id": ts,
            "ephemeral_ttl_mode": "",
            "__user": self.user_id,
            "__a": "1",
            "__req": "1b",
            "fb_dtsg": self.fb_dtsg,
            "jazoest": self.jazoest
        }

        if media_type == "image":
            data["has_attachment"] = "true"
            data["image_ids"] = [media_id]

        if media_type == "video":
            data["has_attachment"] = "true"
            data["video_ids"] = [media_id]

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://www.facebook.com",
            "Referer": f"https://www.facebook.com/messages/t/{recipient_id}"
        }

        cookies = {
            k.strip(): v for k, v in
            (x.split("=") for x in self.cookie.split(";") if "=" in x)
        }

        try:
            r = requests.post(
                "https://www.facebook.com/messaging/send/",
                data=data,
                headers=headers,
                cookies=cookies
            )

            if r.status_code != 200:
                print("❌ Gửi thất bại:", r.status_code)
                return {"success": False}

            if "for (;;);" in r.text:
                js = json.loads(r.text.replace("for (;;);", ""))
                if js.get("error"):
                    print("❌ FB lỗi:", js.get("errorDescription"))
                    return {"success": False}

            print("✅ Gửi tin nhắn thành công")
            return {"success": True}

        except Exception as e:
            print("❌ Lỗi gửi:", e)
            return {"success": False}
        
if __name__ == "__main__":
    try:
        cookie = input(">> Nhập cookie: ").strip()
        messenger = Treoanhmess(cookie)
        print(f"[✓] Đã xác thực cookie: ID-> {messenger.user_id}")

        recipient_id = input(">> Nhập ID box: ").strip()
        media_link = input(">> Nhập LINK ảnh / video (jpg/mp4): ").strip()
        file_txt = input(">> Nhập đường dẫn file .txt chứa nội dung: ").strip()
        delay = float(input(">> Nhập delay: ").strip())

        if not os.path.isfile(file_txt):
            print(f"[!] File không tồn tại: {file_txt}")
            exit()

        print("\n===BẮT ĐẦU GỬI===\n")

        while True:
            try:
                with open(file_txt, 'r', encoding='utf-8') as f:
                    message = f.read().strip()

                if not message:
                    print("[!] Nội dung rỗng.")
                    break

                # ⬇⬇⬇ CHỖ QUAN TRỌNG ⬇⬇⬇
                media_type, media_id = messenger.upload_media(media_link)

                if not media_id:
                    print("[!] Upload media thất bại.")
                    continue

                result = messenger.gui_tn(
                    recipient_id,
                    message,
                    media_type,
                    media_id
                )

                if result.get("success"):
                    print(f"[✓] Gửi thành công nội dung từ {file_txt}")
                else:
                    print(f"[×] Gửi thất bại từ {file_txt}")

            except Exception as e:
                print(f"[!] Lỗi xử lý file: {e}")

            sys.stdout.write("--> Đang chờ... ")
            for _ in range(int(delay)):
                sys.stdout.write("⌛")
                sys.stdout.flush()
                sleep(1)
            sys.stdout.write("\n")

    except Exception as e:
        print(f"[!] Lỗi tổng: {e}")
