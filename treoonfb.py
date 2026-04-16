import os
import sys
import time
import json
import random
import hashlib
import re
import threading
from datetime import datetime
import requests
from urllib.parse import urlparse, quote
import paho.mqtt.client as mqtt
import pyfiglet
from termcolor import colored
import urllib3

# Tắt cảnh báo SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Counter:
    def __init__(self, initial_value=0):
        self.value = initial_value
        
    def increment(self):
        self.value += 1
        return self.value
        
    @property
    def counter(self):
        return self.value

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def banner():
    ascii_banner = pyfiglet.figlet_format("  CteVcl", font="slant")
    print(colored(ascii_banner, 'cyan', attrs=['bold']))
    print("=" * 60)
    print(colored("       Tool Treo Card Messenger ", 'white', attrs=['bold']))
    print("=" * 60)

def parse_cookie_string(cookie_string):
    """Parse cookie string thành dictionary"""
    cookie_dict = {}
    cookies = cookie_string.split(";")
    for cookie in cookies:
        cookie = cookie.strip()
        if "=" in cookie:
            key, value = cookie.split("=", 1)
            cookie_dict[key] = value
    return cookie_dict

def generate_offline_threading_id():
    """Generate offline threading ID"""
    return str(int(time.time() * 1000)) + str(random.randint(0, 9999))

def str_base(number, base):
    """Convert number to base string"""
    def digitToChar(digit):
        if digit < 10:
            return str(digit)
        return chr(ord('a') + digit - 10)
    
    if number < 0:
        return "-" + str_base(-number, base)
    (d, m) = divmod(number, base)
    if d > 0:
        return str_base(d, base) + digitToChar(m)
    return digitToChar(m)

def generate_session_id():
    """Generate session ID"""
    return random.randint(1000000000, 9999999999)

def generate_client_id():
    """Generate client ID"""
    import string
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choices(chars, k=8)) + '-' + \
           ''.join(random.choices(chars, k=4)) + '-' + \
           ''.join(random.choices(chars, k=4)) + '-' + \
           ''.join(random.choices(chars, k=4)) + '-' + \
           ''.join(random.choices(chars, k=12))

def json_minimal(data):
    """Convert to minimal JSON"""
    return json.dumps(data, separators=(",", ":"))

class AdvancedCookieParser:
    """Advanced cookie parser với nhiều phương pháp lấy fb_dtsg"""
    
    def __init__(self, cookie):
        self.cookie = cookie
        self.cookie_dict = parse_cookie_string(cookie)
        self.user_id = self._get_user_id()
        self.fb_dtsg = None
        self.jazoest = None
        self.rev = None
        self.lsd = None
        self._extract_all_params()
    
    def _get_user_id(self):
        """Lấy user ID từ cookie"""
        if 'c_user' in self.cookie_dict:
            return self.cookie_dict['c_user']
        
        # Tìm trong cookie string
        patterns = [r'c_user=(\d+)', r'"user_id":"(\d+)"', r"'user_id':'(\d+)'"]
        for pattern in patterns:
            match = re.search(pattern, self.cookie)
            if match:
                return match.group(1)
        
        raise Exception("Không tìm thấy user_id trong cookie")
    
    def _extract_all_params(self):
        """Lấy tất cả tham số cần thiết"""
        print(colored(f"[*] Đang lấy thông tin cho user {self.user_id}...", "cyan"))
        
        # Phương pháp 1: Dùng GraphQL API
        if self._try_graphql_method():
            return
            
        # Phương pháp 2: Dùng home page với nhiều pattern
        if self._try_homepage_method():
            return
            
        # Phương pháp 3: Dùng messages page
        if self._try_messages_method():
            return
            
        # Phương pháp 4: Dùng mbasic
        if self._try_mbasic_method():
            return
            
        # Phương pháp cuối: Tạo giá trị fake hợp lệ
        self._create_fake_params()
    
    def _try_graphql_method(self):
        """Thử lấy qua GraphQL API"""
        try:
            headers = {
                'Cookie': self.cookie,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': '*/*',
                'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://www.facebook.com',
                'Referer': 'https://www.facebook.com/',
                'X-Requested-With': 'XMLHttpRequest'
            }
            
            # Lấy lsd trước
            lsd_response = requests.get(
                'https://www.facebook.com/',
                headers=headers,
                timeout=10,
                verify=False
            )
            
            # Tìm lsd
            lsd_patterns = [
                r'"LSD",\[\],{"token":"([^"]+)"',
                r'"LSD".*?"token":"([^"]+)"',
                r'"token":"([^"]+)".*?"LSD"',
                r'\["LSD",\[\],\{"token":"([^"]+)"\}',
                r'name="lsd" value="([^"]+)"'
            ]
            
            for pattern in lsd_patterns:
                match = re.search(pattern, lsd_response.text, re.DOTALL)
                if match:
                    self.lsd = match.group(1)
                    break
            
            # Dùng doc_id mới
            params = {
                'doc_id': '6192758788609373',  # Doc_id mới cho inbox
                'variables': json.dumps({
                    'limit': 20,
                    'tags': ['INBOX'],
                    'before': None,
                    'includeDeliveryReceipts': True,
                    'includeSeqID': True
                }),
                'fb_dtsg': self.lsd or 'NA',
                '__a': '1',
                '__user': self.user_id
            }
            
            response = requests.post(
                'https://www.facebook.com/api/graphql/',
                data=params,
                headers=headers,
                cookies=parse_cookie_string(self.cookie),
                timeout=15,
                verify=False
            )
            
            if response.status_code == 200:
                text = response.text
                if text.startswith('for (;;);'):
                    text = text[9:]
                
                try:
                    data = json.loads(text)
                    
                    # Tìm fb_dtsg trong response
                    response_str = json.dumps(data)
                    
                    fb_dtsg_patterns = [
                        r'"token":"([^"]+)"',
                        r'"fb_dtsg":"([^"]+)"',
                        r'DTSG".*?"token":"([^"]+)"'
                    ]
                    
                    for pattern in fb_dtsg_patterns:
                        match = re.search(pattern, response_str, re.DOTALL)
                        if match:
                            self.fb_dtsg = match.group(1)
                            break
                    
                    # Tìm jazoest
                    jazoest_match = re.search(r'"jazoest":"(\d+)"', response_str)
                    if jazoest_match:
                        self.jazoest = jazoest_match.group(1)
                    
                    # Tìm revision
                    rev_match = re.search(r'"__rev":"(\d+)"', response_str)
                    if rev_match:
                        self.rev = rev_match.group(1)
                    
                    if self.fb_dtsg and self.fb_dtsg != "NA":
                        print(colored(f"[✓] Đã lấy fb_dtsg qua GraphQL: {self.fb_dtsg[:20]}...", "green"))
                        return True
                        
                except Exception as e:
                    pass
                    
        except Exception as e:
            pass
            
        return False
    
    def _try_homepage_method(self):
        """Thử lấy từ trang chủ Facebook"""
        try:
            headers = {
                'Cookie': self.cookie,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7'
            }
            
            urls = [
                'https://www.facebook.com/?_rdc=1&_rdr#',
                'https://www.facebook.com/home.php',
                'https://www.facebook.com/'
            ]
            
            for url in urls:
                try:
                    response = requests.get(
                        url,
                        headers=headers,
                        timeout=10,
                        verify=False,
                        allow_redirects=True
                    )
                    
                    if response.status_code == 200:
                        html = response.text
                        
                        # Tìm fb_dtsg với nhiều pattern
                        patterns = [
                            r'"token":"([^"]+)"',
                            r'name="fb_dtsg" value="([^"]+)"',
                            r'"fb_dtsg":"([^"]+)"',
                            r'DTSGInitData.*?token.*?:.*?"([^"]+)"',
                            r'\["DTSG".*?"token":"([^"]+)"',
                            r'fb_dtsg" value="([^"]+)"',
                            r'"ttstamp":"([^"]+)"'
                        ]
                        
                        for pattern in patterns:
                            matches = re.findall(pattern, html, re.DOTALL)
                            for match in matches:
                                if match and len(match) > 10 and ':' not in match:
                                    self.fb_dtsg = match
                                    break
                            if self.fb_dtsg:
                                break
                        
                        # Tìm jazoest
                        jazoest_match = re.search(r'name="jazoest" value="(\d+)"', html)
                        if jazoest_match:
                            self.jazoest = jazoest_match.group(1)
                        else:
                            jazoest_match = re.search(r'"jazoest":"(\d+)"', html)
                            if jazoest_match:
                                self.jazoest = jazoest_match.group(1)
                        
                        # Tìm revision
                        rev_match = re.search(r'"__rev":"(\d+)"', html)
                        if rev_match:
                            self.rev = rev_match.group(1)
                        
                        # Tìm lsd
                        lsd_match = re.search(r'name="lsd" value="([^"]+)"', html)
                        if lsd_match:
                            self.lsd = lsd_match.group(1)
                        
                        if self.fb_dtsg:
                            print(colored(f"[✓] Đã lấy fb_dtsg từ {url}: {self.fb_dtsg[:20]}...", "green"))
                            return True
                            
                except Exception as e:
                    continue
                    
        except Exception as e:
            pass
            
        return False
    
    def _try_messages_method(self):
        """Thử lấy từ trang messages"""
        try:
            headers = {
                'Cookie': self.cookie,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            response = requests.get(
                'https://web.facebook.com/messages/t/{thread_id}',
                headers=headers,
                timeout=10,
                verify=False
            )
            
            if response.status_code == 200:
                html = response.text
                
                # Tìm trong JavaScript data
                script_pattern = r'requireLazy\(\["ServerJS"\]\).*?(handle.*?)\);'
                script_match = re.search(script_pattern, html, re.DOTALL)
                
                if script_match:
                    script_content = script_match.group(0)
                    
                    # Tìm fb_dtsg
                    dtsg_patterns = [
                        r'"DTSG".*?"token":"([^"]+)"',
                        r'"token":"([^"]+)".*?DTSG',
                        r'fb_dtsg["\']?\s*[:=]\s*["\']([^"\']+)'
                    ]
                    
                    for pattern in dtsg_patterns:
                        match = re.search(pattern, script_content, re.DOTALL)
                        if match:
                            self.fb_dtsg = match.group(1)
                            break
                
                if not self.fb_dtsg:
                    # Tìm với pattern khác
                    other_patterns = [
                        r'"ttstamp":"([^"]+)"',
                        r'"fb_dtsg":"([^"]+)"'
                    ]
                    
                    for pattern in other_patterns:
                        match = re.search(pattern, html)
                        if match:
                            self.fb_dtsg = match.group(1)
                            break
                
                if self.fb_dtsg:
                    print(colored(f"[✓] Đã lấy fb_dtsg từ messages: {self.fb_dtsg[:20]}...", "green"))
                    return True
                    
        except Exception as e:
            pass
            
        return False
    
    def _try_mbasic_method(self):
        """Thử lấy từ mbasic.facebook.com"""
        try:
            headers = {
                'Cookie': self.cookie,
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
            }
            
            response = requests.get(
                'https://mbasic.facebook.com/',
                headers=headers,
                timeout=10,
                verify=False
            )
            
            if response.status_code == 200:
                html = response.text
                
                # Tìm fb_dtsg trong form
                dtsg_match = re.search(r'name="fb_dtsg" value="([^"]+)"', html)
                if dtsg_match:
                    self.fb_dtsg = dtsg_match.group(1)
                
                # Tìm jazoest
                jazoest_match = re.search(r'name="jazoest" value="(\d+)"', html)
                if jazoest_match:
                    self.jazoest = jazoest_match.group(1)
                
                if self.fb_dtsg:
                    print(colored(f"[✓] Đã lấy fb_dtsg từ mbasic: {self.fb_dtsg[:20]}...", "green"))
                    return True
                    
        except Exception as e:
            pass
            
        return False
    
    def _create_fake_params(self):
        """Tạo tham số fake hợp lệ khi không lấy được thật"""
        print(colored("[!] Không lấy được tham số thật, tạo giá trị hợp lệ...", "yellow"))
        
        # Tạo fb_dtsg hợp lệ (format thường thấy)
        fake_hash = hashlib.md5(f"{self.user_id}{int(time.time())}".encode()).hexdigest()
        self.fb_dtsg = f"NA{fake_hash[:20]}"
        
        # Jazoest mặc định
        self.jazoest = "22036"
        
        # Revision mặc định
        self.rev = "1015919737"
        
        # LSD
        self.lsd = hashlib.md5(f"lsd_{self.user_id}".encode()).hexdigest()[:10]
        
        print(colored(f"[✓] Đã tạo tham số fake: fb_dtsg={self.fb_dtsg[:20]}...", "green"))

class MessengerOnlineKeeper:
    """Class chính để giữ online trên Messenger"""
    
    def __init__(self, cookie, user_info, thread_num):
        self.cookie = cookie
        self.user_info = user_info
        self.thread_num = thread_num
        self.parser = None
        self.dataFB = None
        self.mqtt = None
        self.is_running = True
        self.is_connected = False
        self.last_activity = time.time()
        self.keepalive_count = 0
        self.reconnect_attempts = 0
        self.max_reconnect = 3
    
    def initialize(self):
        """Khởi tạo kết nối"""
        try:
            print(colored(f"[*] Thread {self.thread_num}: Đang parse cookie...", "cyan"))
            
            # Parse cookie
            self.parser = AdvancedCookieParser(self.cookie)
            
            self.dataFB = {
                "FacebookID": self.parser.user_id,
                "fb_dtsg": self.parser.fb_dtsg,
                "clientRevision": self.parser.rev or "1015919737",
                "jazoest": self.parser.jazoest or "22036",
                "cookieFacebook": self.cookie,
                "lsd": self.parser.lsd or "NA"
            }
            
            print(colored(f"[✓] Thread {self.thread_num}: Parse thành công!", "green"))
            print(colored(f"    User: {self.user_info['name']} ({self.user_info['id']})", "white"))
            print(colored(f"    fb_dtsg: {self.parser.fb_dtsg[:30]}...", "white"))
            
            # Kết nối MQTT
            return self._connect_mqtt_direct()
            
        except Exception as e:
            print(colored(f"[!] Thread {self.thread_num}: Lỗi khởi tạo: {str(e)}", "red"))
            return False
    
    def _connect_mqtt_direct(self):
        """Kết nối MQTT trực tiếp không cần last_seq_id"""
        try:
            import ssl
            
            print(colored(f"[*] Thread {self.thread_num}: Đang kết nối MQTT...", "cyan"))
            
            # Tạo session ID và client ID
            session_id = generate_session_id()
            client_id = generate_client_id()
            
            # Tạo user data cho MQTT
            user_data = {
                "u": self.dataFB["FacebookID"],
                "s": session_id,
                "chat_on": True,
                "fg": False,
                "d": client_id,
                "ct": "websocket",
                "aid": 219994525426954,
                "cp": 3,
                "ecp": 10,
                "st": ["/t_ms", "/messenger_sync_get_diffs", "/messenger_sync_create_queue"],
                "pm": [],
                "dc": "",
                "no_auto_fg": True,
                "gas": None,
                "pack": []
            }
            
            # Tạo MQTT client
            self.mqtt = mqtt.Client(
                client_id="mqttwsclient",
                clean_session=True,
                protocol=mqtt.MQTTv31,
                transport="websockets"
            )
            
            # Cấu hình SSL
            self.mqtt.tls_set(certfile=None, keyfile=None, cert_reqs=ssl.CERT_NONE)
            
            # Thiết lập username
            self.mqtt.username_pw_set(username=json_minimal(user_data))
            
            # Cấu hình WebSocket
            self.mqtt.ws_set_options(
                path="/chat?region=lla&sid=" + str(session_id),
                headers={
                    "Cookie": self.cookie,
                    "Origin": "https://www.messenger.com",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Host": "edge-chat.messenger.com"
                }
            )
            
            # Callback khi kết nối
            def on_connect(client, userdata, flags, rc):
                if rc == 0:
                    print(colored(f"[✓] Thread {self.thread_num}: Đã kết nối MQTT thành công!", "green"))
                    self.is_connected = True
                    self.reconnect_attempts = 0
                    
                    # Subscribe các topic cần thiết
                    client.subscribe("/t_ms", qos=0)
                    
                    # Gửi packet tạo queue với seq_id mặc định
                    queue_data = {
                        "sync_api_version": 10,
                        "max_deltas_able_to_process": 1000,
                        "delta_batch_size": 500,
                        "encoding": "JSON",
                        "entity_fbid": self.dataFB["FacebookID"],
                        "initial_titan_sequence_id": int(time.time() * 1000),  # Fake seq_id
                        "device_params": None
                    }
                    
                    client.publish(
                        "/messenger_sync_create_queue",
                        json_minimal(queue_data),
                        qos=1
                    )
                    
                else:
                    print(colored(f"[!] Thread {self.thread_num}: MQTT connect failed with code {rc}", "red"))
            
            # Callback khi disconnect
            def on_disconnect(client, userdata, rc):
                print(colored(f"[!] Thread {self.thread_num}: MQTT disconnected", "yellow"))
                self.is_connected = False
                if self.is_running:
                    self._reconnect()
            
            # Gán callbacks
            self.mqtt.on_connect = on_connect
            self.mqtt.on_disconnect = on_disconnect
            
            # Kết nối
            self.mqtt.connect(
                host="edge-chat.messenger.com",
                port=443,
                keepalive=60
            )
            
            # Bắt đầu loop
            self.mqtt.loop_start()
            
            # Chờ kết nối
            for _ in range(30):  # Chờ tối đa 30 giây
                if self.is_connected:
                    return True
                time.sleep(1)
            
            return False
            
        except Exception as e:
            print(colored(f"[!] Thread {self.thread_num}: Lỗi kết nối MQTT: {str(e)}", "red"))
            return False
    
    def _reconnect(self):
        """Tự động reconnect"""
        if self.reconnect_attempts >= self.max_reconnect:
            print(colored(f"[!] Thread {self.thread_num}: Đã vượt quá số lần reconnect tối đa", "red"))
            return False
        
        self.reconnect_attempts += 1
        print(colored(f"[*] Thread {self.thread_num}: Đang reconnect lần {self.reconnect_attempts}...", "yellow"))
        
        time.sleep(5)
        return self._connect_mqtt_direct()
    
    def send_keepalive(self):
        """Gửi tín hiệu keepalive"""
        if not self.is_connected or not self.mqtt:
            return False
        
        try:
            # Gửi foreground state
            self.mqtt.publish(
                "/foreground_state",
                json_minimal({"foreground": True}),
                qos=0
            )
            
            # Thỉnh thoảng gửi active
            if self.keepalive_count % 5 == 0:
                self.mqtt.publish(
                    "/active",
                    json_minimal({"active": True}),
                    qos=0
                )
            
            # Thỉnh thoảng gửi typing indicator ẩn
            if self.keepalive_count % 10 == 0:
                typing_payload = {
                    "app_id": "2220391788200892",
                    "payload": json_minimal({
                        "label": "3",
                        "payload": json_minimal({
                            "thread_key": "0",
                            "is_group_thread": False,
                            "is_typing": False,
                            "attribution": 0
                        }),
                        "version": "25393437286970779"
                    }),
                    "request_id": self.keepalive_count,
                    "type": 4
                }
                
                self.mqtt.publish(
                    "/ls_req",
                    json_minimal(typing_payload),
                    qos=1
                )
            
            self.keepalive_count += 1
            self.last_activity = time.time()
            return True
            
        except Exception as e:
            print(colored(f"[!] Thread {self.thread_num}: Lỗi send keepalive: {str(e)}", "red"))
            self.is_connected = False
            return False
    
    def run(self, delay=5):
        """Chạy main loop"""
        print(colored(f"[*] Thread {self.thread_num}: Bắt đầu giữ online...", "cyan"))
        
        last_status_time = time.time()
        status_interval = 30  # Hiển thị status mỗi 30 giây
        
        while self.is_running:
            try:
                # Kiểm tra và gửi keepalive
                current_time = time.time()
                
                # Gửi keepalive mỗi 3-8 giây
                if current_time - self.last_activity > random.uniform(3, 8):
                    if self.send_keepalive():
                        # Hiển thị status định kỳ
                        if current_time - last_status_time >= status_interval:
                            timestamp = datetime.now().strftime('%H:%M:%S')
                            status = "✓ ONLINE" if self.is_connected else "✗ OFFLINE"
                            print(colored(
                                f"[{timestamp}] Thread {self.thread_num}: {self.user_info['name']} - {status} " +
                                f"(Keepalive: {self.keepalive_count})",
                                "green" if self.is_connected else "yellow"
                            ))
                            last_status_time = current_time
                
                # Kiểm tra kết nối
                if not self.is_connected and self.is_running:
                    print(colored(f"[!] Thread {self.thread_num}: Mất kết nối, đang thử reconnect...", "yellow"))
                    time.sleep(5)
                    self._reconnect()
                
                time.sleep(delay)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(colored(f"[!] Thread {self.thread_num}: Lỗi trong main loop: {str(e)}", "red"))
                time.sleep(5)
    
    def stop(self):
        """Dừng thread"""
        print(colored(f"[*] Thread {self.thread_num}: Đang dừng...", "yellow"))
        self.is_running = False
        
        if self.mqtt:
            try:
                self.mqtt.disconnect()
                self.mqtt.loop_stop()
            except:
                pass
        
        print(colored(f"[✓] Thread {self.thread_num}: Đã dừng", "green"))

class User:
    @staticmethod
    def get_user_info(cookie):
        """Lấy thông tin user từ cookie"""
        try:
            # Lấy user_id
            uid_match = re.search(r'c_user=(\d+)', cookie)
            if not uid_match:
                return {'id': 'unknown', 'name': 'Unknown'}

            uid = uid_match.group(1)

            # Thử lấy tên từ Graph API
            try:
                xs_match = re.search(r'xs=([^;]+)', cookie)
                if xs_match:
                    xs_token = xs_match.group(1)

                    # Giải mã URL encoded nếu cần
                    if '%' in xs_token:
                        xs_token = quote(xs_token, safe='')

                    headers = {
                        'User-Agent': (
                            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                            'AppleWebKit/537.36 (KHTML, like Gecko) '
                            'Chrome/120.0.0.0 Safari/537.36'
                        )
                    }

                    response = requests.get(
                        f'https://graph.facebook.com/{uid}?fields=name&access_token={xs_token}',
                        headers=headers,
                        timeout=10,
                        verify=False
                    )

                    if response.status_code == 200:
                        data = response.json()
                        if 'name' in data:
                            return {'id': uid, 'name': data['name']}

            except Exception:
                pass

            # Nếu không được, thử lấy từ trang profile
            try:
                headers = {
                    'Cookie': cookie,
                    'User-Agent': (
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                        'AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/120.0.0.0 Safari/537.36'
                    )
                }

                response = requests.get(
                    f'https://mbasic.facebook.com/profile.php?id={uid}',
                    headers=headers,
                    timeout=10,
                    verify=False
                )

                if response.status_code == 200:
                    title_match = re.search(
                        r'<title>(.*?)</title>',
                        response.text
                    )
                    if title_match:
                        name = title_match.group(1).split('|')[0].strip()
                        if name and name != 'Facebook':
                            return {'id': uid, 'name': name}

            except Exception:
                pass

            return {'id': uid, 'name': f'User_{uid[:6]}'}

        except Exception:
            return {'id': 'unknown', 'name': 'Unknown'}

def main():
    """Hàm main"""
    clear()
    banner()
    
    # Nhập Cookie
    cookies = []
    print(colored("\n📝 NHẬP COOKIE FACEBOOK:", "green", attrs=['bold']))
    
    i = 1
    while True:
        cookie = input(colored(f"\n>> Cookie {i} (Enter để dừng): ", "yellow")).strip()
        
        if not cookie:
            break
        
        if 'c_user=' not in cookie:
            print(colored("❌ Cookie phải có 'c_user'", "red"))
            continue
        
        cookies.append(cookie)
        
        # Kiểm tra cookie ngay
        try:
            parser = AdvancedCookieParser(cookie)
            print(colored(f"✅ Cookie {i} hợp lệ - User: {parser.user_id}", "green"))
        except Exception as e:
            print(colored(f"⚠️  Cookie có vấn đề: {str(e)}", "yellow"))
        
        i += 1
    
    if not cookies:
        print(colored("\n❌ Không có cookie nào!", "red"))
        return

    delay = 5

    print(colored("\n[*] Đang lấy thông tin người dùng...", "cyan"))
    user_infos = []
    
    for cookie in cookies:
        info = User.get_user_info(cookie) 
        user_infos.append(info)
        time.sleep(1)

    print(colored("\n" + "=" * 60, "cyan"))
    print(colored("🚀 BẮT ĐẦU TREO CARD", "cyan", attrs=['bold']))
    print(colored("=" * 60, "cyan"))
    
    keepers = []
    threads = []
    
    for i, (cookie, user_info) in enumerate(zip(cookies, user_infos), 1):
        keeper = MessengerOnlineKeeper(cookie, user_info, i)
        keepers.append(keeper)
        
        thread = threading.Thread(
            target=lambda k=keeper, d=delay: (k.initialize() and k.run(d)),
            daemon=True
        )
        threads.append(thread)
        thread.start()
        
        print(colored(f"[✓] Đã khởi động thread {i} cho {user_info['name']}", "green"))
        time.sleep(2)
    
    print(colored(f"\n✅ Đã khởi động {len(threads)} tài khoản", "green"))
    print(colored("⏳ Đang giữ online... (Nhấn Ctrl+C để dừng)", "cyan"))
    
    try:
        # Giữ chương trình chạy
        while True:
            time.sleep(1)
            
            # Kiểm tra tất cả keepers còn chạy không
            running = any(k.is_running for k in keepers)
            if not running:
                break
                
    except KeyboardInterrupt:
        print(colored("\n\n🛑 ĐANG DỪNG TẤT CẢ THREAD...", "red", attrs=['bold']))
    
    finally:
        # Dừng tất cả keepers
        for keeper in keepers:
            keeper.stop()
        
        print(colored("\n" + "=" * 60, "green"))
        print(colored("✅ ĐÃ DỪNG TẤT CẢ TÀI KHOẢN", "green", attrs=['bold']))
        print(colored("=" * 60, "green"))

if __name__ == "__main__":
    main()
