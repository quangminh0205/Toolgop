import multiprocessing
import requests
import os
import re
import json
import time
import random
import pyfiglet
import threading
import ssl
import paho.mqtt.client as mqtt
from urllib.parse import urlparse
import warnings
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

# Bỏ qua cảnh báo phiên bản
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Khởi tạo Rich Console
console = Console()

# Màu sắc gradient từ Viniciusv2.py
RESET = "\033[0m"

def rgb(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"

def gradient_text(text, colors):
    lines = text.splitlines()
    result = ""
    total_chars = sum(len(line) for line in lines if line.strip())
    idx = 0
    for line in lines:
        for ch in line:
            t = idx / max(total_chars-1, 1)
            seg = int(t * (len(colors)-1))
            c1, c2 = colors[seg], colors[min(seg+1, len(colors)-1)]
            ratio = (t * (len(colors)-1)) - seg
            r = int(c1[0] + (c2[0]-c1[0]) * ratio)
            g = int(c1[1] + (c2[1]-c1[1]) * ratio)
            b = int(c1[2] + (c2[2]-c1[2]) * ratio)
            result += rgb(r,g,b) + ch
            idx += 1
        result += RESET
        if line != lines[-1]:
            result += "\n"
    return result + RESET

def print_color(text, color_type="info"):
    """In văn bản với màu sắc"""
    colors = {
        "success": "\033[92m",  # Xanh lá
        "error": "\033[91m",    # Đỏ
        "warning": "\033[93m",  # Vàng
        "info": "\033[94m",     # Xanh dương
        "cyan": "\033[96m",     # Cyan
        "magenta": "\033[95m",  # Magenta
        "reset": RESET
    }
    print(f"{colors.get(color_type, colors['info'])}{text}{colors['reset']}")

def print_gradient(text):
    """In văn bản với gradient"""
    colors = [(0,255,0), (0,0,255), (255,255,255)]
    print(gradient_text(text, colors))

def print_banner():
    """Hiển thị banner"""
    banner = r"""
⠀⠀⠀⠀⠀⠀⣄⠀⠀⠀⣦⣤⣾⣿⠿⠛⣋⣥⣤⣀⠀⠀⠀⠀
⠀⠀⠀⠀⡤⡀⢈⢻⣬⣿⠟⢁⣤⣶⣿⣿⡿⠿⠿⠛⠛⢀⣄⠀
⠀⠀⢢⣘⣿⣿⣶⣿⣯⣤⣾⣿⣿⣿⠟⠁⠄⠀⣾⡇⣼⢻⣿⣾
⣰⠞⠛⢉⣩⣿⣿⣿⣿⣿⣿⣿⣿⠋⣼⣧⣤⣴⠟⣠⣿⢰⣿⣿
⣶⡾⠿⠿⠿⢿⣿⣿⣿⣿⣿⣿⣿⣈⣩⣤⡶⠟⢛⣩⣴⣿⣿⡟
⣠⣄⠈⠀⣰⡦⠙⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣟⡛⠛⠛⠁
⣉⠛⠛⠛⣁⡔⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠥⠀⠀
⣭⣏⣭⣭⣥⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⢠

     TOOL NHÂY TAG MESS                      
"""
    print_gradient(banner)

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def check_live(cookie):
    try:
        if 'c_user=' not in cookie:
            return {"status": "failed", "msg": "Cookie không chứa user_id"}
        
        user_id = cookie.split('c_user=')[1].split(';')[0]
        headers = {
            'authority': 'm.facebook.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-language': 'vi-VN,vi;q=0.9',
            'cache-control': 'max-age=0',
            'cookie': cookie,
            'sec-ch-ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-ch-ua-platform-version': '"0.1.0"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
        }
        profile_response = requests.get(f'https://m.facebook.com/profile.php?id={user_id}', headers=headers, timeout=30)
        name = profile_response.text.split('<title>')[1].split('<')[0].strip()
        return {
            "status": "success",
            "name": name,
            "user_id": user_id,
            "msg": "successful"
        }
    except Exception as e:
        return {"status": "failed", "msg": f"Lỗi xảy ra: {str(e)}"}

def load_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        if not lines:
            raise Exception(f"File {file_path} trống!")
        return lines
    except Exception as e:
        raise Exception(f"Lỗi đọc file {file_path}: {str(e)}")

def parse_selection(input_str, max_index):
    try:
        numbers = [int(i.strip()) for i in input_str.split(',')]
        return [n for n in numbers if 1 <= n <= max_index]
    except:
        print_color("❌ Định dạng không hợp lệ!", "error")
        return []

def generate_offline_threading_id():
    ret = int(time.time() * 1000)
    value = random.randint(0, 4294967295)
    binary_str = format(value, "022b")[-22:]
    msgs = bin(ret)[2:] + binary_str
    return str(int(msgs, 2))

def json_minimal(data):
    return json.dumps(data, separators=(",", ":"))

def generate_session_id():
    return random.randint(1, 2 ** 53)

def generate_client_id():
    import string
    def gen(length):
        return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return gen(8) + '-' + gen(4) + '-' + gen(4) + '-' + gen(4) + '-' + gen(12)

class MQTTManager:
    def __init__(self, cookie, user_id):
        self.cookie = cookie
        self.user_id = user_id
        self.mqtt = None
        self.ws_req_number = 0
        self.ws_task_number = 0
        self.connected = False
        
    def connect(self):
        try:
            chat_on = json_minimal(True)
            session_id = generate_session_id()
            user = {
                "u": self.user_id,
                "s": session_id,
                "chat_on": chat_on,
                "fg": False,
                "d": generate_client_id(),
                "ct": "websocket",
                "aid": 219994525426954,
                "mqtt_sid": "",
                "cp": 3,
                "ecp": 10,
                "st": ["/t_ms", "/messenger_sync_get_diffs", "/messenger_sync_create_queue"],
                "pm": [],
                "dc": "",
                "no_auto_fg": True,
                "gas": None,
                "pack": [],
            }
            
            host = f"wss://edge-chat.facebook.com/chat?region=eag&sid={session_id}"
            options = {
                "client_id": "mqttwsclient",
                "username": json_minimal(user),
                "clean": True,
                "ws_options": {
                    "headers": {
                        "Cookie": self.cookie,
                        "Origin": "https://www.facebook.com",
                        "User-Agent": "Mozilla/5.0 (Linux; Android 9; SM-G973U Build/PPR1.180610.011) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Mobile Safari/537.36",
                        "Referer": "https://www.facebook.com/",
                        "Host": "edge-chat.facebook.com",
                    },
                },
                "keepalive": 10,
            }
            
            # Tạo MQTT client với phiên bản callback mới
            try:
                self.mqtt = mqtt.Client(
                    client_id="mqttwsclient",
                    clean_session=True,
                    protocol=mqtt.MQTTv31,
                    transport="websockets",
                    callback_api_version=mqtt.CallbackAPIVersion.VERSION2
                )
            except:
                # Fallback cho phiên bản cũ
                self.mqtt = mqtt.Client(
                    client_id="mqttwsclient",
                    clean_session=True,
                    protocol=mqtt.MQTTv31,
                    transport="websockets"
                )
            
            self.mqtt.tls_set(certfile=None, keyfile=None, cert_reqs=ssl.CERT_NONE, tls_version=ssl.PROTOCOL_TLSv1_2)
            
            self.mqtt.on_connect = self._on_connect
            self.mqtt.on_disconnect = self._on_disconnect
            
            self.mqtt.username_pw_set(username=options["username"])
            parsed_host = urlparse(host)
            
            self.mqtt.ws_set_options(
                path=f"{parsed_host.path}?{parsed_host.query}",
                headers=options["ws_options"]["headers"],
            )
            
            print_color("🔄 Đang Loading...", "info")
            self.mqtt.connect(
                host=options["ws_options"]["headers"]["Host"],
                port=443,
                keepalive=options["keepalive"],
            )
            
            self.mqtt.loop_start()
            time.sleep(3)
            return self.connected
            
        except Exception as e:
            print_color(f"❌ Lỗi kết nối MQTT: {e}", "error")
            return False
    
    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            self.connected = True
        else:
            print_color(f"❌ Kết nối MQTT thất bại với mã: {rc}", "error")
            self.connected = False
    
    def _on_disconnect(self, client, userdata, rc, properties=None):
        print_color(f"🔌 Ngắt kết nối MQTT với mã: {rc}", "warning")
        self.connected = False
    
    def send_typing(self, thread_id, is_typing=True):
        if not self.connected or not self.mqtt:
            return False
            
        self.        
        try:
            response = requests.post(
                'https://www.facebook.com/api/graphqlbatch/',
                data=form_data,
                headers=headers,
                timeout=15
            )
            
            if response.status_code != 200:
                return {"error": f"HTTP Error: {response.status_code}"}
            
            response_text = response.text.split('{"successful_results"')[0]
            data = json.loads(response_text)
            
            if "o0" not in data:
                return {"error": "Không tìm thấy dữ liệu thread list"}
            
            if "errors" in data["o0"]:
                return {"error": f"Facebook API Error: {data['o0']['errors'][0]['summary']}"}
            
            threads = data["o0"]["data"]["viewer"]["message_threads"]["nodes"]
            thread_list = []
            
            for thread in threads:
                if not thread.get("thread_key") or not thread["thread_key"].get("thread_fbid"):
                    continue
                thread_list.append({
                    "thread_id": thread["thread_key"]["thread_fbid"],
                    "thread_name": thread.get("name", "Không có tên")
                })
            
            return {
                "success": True,
                "thread_count": len(thread_list),
                "threads": thread_list
            }
            
        except json.JSONDecodeError as e:
            return {"error": f"Lỗi parse JSON: {str(e)}"}
        except Exception as e:
            return {"error": f"Lỗi không xác định: {str(e)}"}

    def get_group_members(self, thread_id):
        headers = {
            'Cookie': self.cookie,
            'User-Agent': 'python-http/0.27.0',
            'Accept': '*/*',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://www.facebook.com',
            'Host': 'www.facebook.com',
            'Referer': 'https://www.facebook.com/'
        }
        
        payload = {
            'queries': json.dumps({
                'o0': {
                    'doc_id': '3449967031715030',
                    'query_params': {
                        'id': thread_id,
                        'message_limit': 0,
                        'load_messages': False,
                        'load_read_receipts': False,
                        'before': (0,0,255)])).strip()
            
            if raw.lower() == 'all':
                selected = list(range(1, len(threads_list) + 1))
            else:
                selected = parse_selection(raw, len(threads_list))
            
            if not selected:
                print_color("❌ Không chọn box nào! Bỏ qua tài khoản này.", "error")
                continue
            
            selected_ids = [threads_list[i - 1]['thread_id'] for i in selected]
            selected_names = [threads_list[i - 1]['thread_name'] or 'Không có tên' for i in selected]
            
            print_color(f"\n🔄 Đang lấy danh sách thành viên cho box...", "info")
            members = []
            for thread_id in selected_ids:
                result = messenger.get_group_members(thread_id)
                if result.get("success"):
                    members.extend(result["members"])
                else:
                    print_color(f"⚠️ Lỗi lấy thành viên cho box {thread_id}: {result['error']}", "warning")
            
            if not members:
                print_color("❌ Không tìm thấy thành viên nào trong các box đã chọn. Bỏ qua tài khoản này.", "error")
                continue
            
            # Hiển thị danh sách thành viên trong bảng với rich - KHÔNG BỊ LỆCH
            member_table = Table(title=f"👥 DANH SÁCH THÀNH VIÊN - {len(members)} NGƯỜI", show_header=True, header_style="bold blue", box=box.ROUNDED)
            member_table.add_column("STT", style="cyan", width=5, justify="center")
            member_table.add_column("Tên", style="green")
            member_table.add_column("ID", style="yellow")
            
            for idx, member in enumerate(members, 1):
                member_name = f"{member['name'][:40]}{'...' if len(member['name']) > 40 else ''}"
                member_table.add_row(str(idx), member_name, member['id'])
            
            console.print(member_table)
            print_line()
            
            raw_tags = input(gradient_text("🏷️ Nhập số thứ tự người muốn réo (VD: 1,2,3 hoặc all) hoặc 'khong' để bỏ qua: ", [(0,255,0), (0,0,255)])).strip()
            tag_ids = []
            tag_names = []
            if raw_tags.lower() != 'khong':
                if raw_tags.lower() == 'all':
                    selected_tags = list(range(1, len(members) + 1))
                else:
                    selected_tags = parse_selection(raw_tags, len(members))
                if not selected_tags:
                    print_color("❌ Không chọn thành viên nào để tag! Bỏ qua tài khoản này.", "error")
                    continue
                tag_ids = [members[i - 1]['id'] for i in selected_tags]
                tag_names = [members[i - 1]['name'] for i in selected_tags]
                print_color(f"✅ Đã chọn {len(tag_ids)} người để tag thật", "success")
            
            file_txt = input(gradient_text("📂 Nhập tên file .txt chứa nội dung chửi: ", [(0,255,0), (0,0,255)])).strip()
            try:
                message_lines = load_file(file_txt)
                print_color(f"✅ Đã tải {len(message_lines)} dòng nội dung từ {file_txt}", "success")
            except Exception as e:
                print_color(f"❌ Lỗi: {str(e)}. Bỏ qua tài khoản này.", "error")
                continue
            
            replace_text = input(gradient_text("✏️ Nhập nội dung thay thế cho tên (nhấn Enter nếu không thay thế): ", [(0,255,0), (0,0,255)])).strip()
            
            try:
                delay = int(input(gradient_text("⏳ Nhập delay giữa các lần gửi (giây): ", [(0,255,0), (0,0,255)])))
                if delay < 1:
                    print_color("❌ Delay phải là số nguyên dương. Bỏ qua tài khoản này.", "error")
                    continue
            except ValueError:
                print_color("❌ Delay phải là số nguyên. Bỏ qua tài khoản này.", "error")
                continue
            
            print_header(f"🚀 KHỞI ĐỘNG TÀI KHOẢN {cl['name']}")
            if tag_ids:
                print_color(f"🎯 Sẽ tag thật {len(tag_ids)} người: {', '.join(tag_names[:3])}{'...' if len(tag_names) > 3 else ''}", "cyan")
            
            if messenger.mqtt_manager and messenger.mqtt_manager.connected:
                print_color("⚡ Bắt Đầu Giết Mấy Con Chó", "success")
            else:
                print_color("⚠️ Sử dụng phương thức gửi thông thường", "warning")
            
            p = multiprocessing.Process(
                target=start_spam,
                args=(cookie, cl['name'], cl['user_id'], selected_ids, selected_names, delay, message_lines, replace_text, tag_ids, tag_names)
            )
            processes.append(p)
            p.start()
            
            time.sleep(2)  # Delay giữa các account để tránh conflict
            
        except Exception as e:
            print_color(f"❌ Lỗi tài khoản {cl['name']}: {str(e)}. Bỏ qua tài khoản này.", "error")
            continue
    
    if not processes:
        print_color("❌ Không có tài khoản nào được khởi động. Thoát chương trình.", "error")
        return
    
    print_header("🎉 KHỞI ĐỘNG THÀNH CÔNG")
    print_color(f"✅ Đã khởi động {len(processes)} tài khoản", "success")
    print_color("⚡ Tính Năng: Nhây Tag + Fake Typing Cực Múp", "cyan")
    print_color("⏹️ Nhấn Ctrl+C để dừng tất cả tiến trình", "warning")
    print_line()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print_color("\n\n🛑 Đang dừng tất cả tiến trình...", "error")
        for p in processes:
            p.terminate()
        time.sleep(2)
        print_color("✅ Đã dừng tất cả tiến trình!", "success")
        print_color("👋 Chào tạm biệt!", "info")

if __name__ == "__main__":
    start_multiple_accounts()


