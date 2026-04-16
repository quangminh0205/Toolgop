import os
import time
import json
import threading
from datetime import datetime
from zlapi import ZaloAPI, ThreadType
import random


UI_WIDTH = 70


class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def draw_box(title, content_lines, color=Colors.CYAN):
    print(color + "╔" + "═" * (UI_WIDTH - 2) + "╗" + Colors.RESET)
    print(color + "║" + Colors.RESET + title.center(UI_WIDTH - 2) + color + "║" + Colors.RESET)
    print(color + "╠" + "═" * (UI_WIDTH - 2) + "╣" + Colors.RESET)
    for line in content_lines:
        print(color + "║ " + Colors.RESET + line.ljust(UI_WIDTH - 4) + color + " ║" + Colors.RESET)
    print(color + "╚" + "═" * (UI_WIDTH - 2) + "╝" + Colors.RESET)


class InfiniteGroupBot(ZaloAPI):
    def __init__(self, imei, session_cookies, account_name="Account"):
        super().__init__("dummy_api_key", "dummy_secret_key", imei, session_cookies)
        self.account_name = account_name
        self.created_groups = []
        self.create_sessions = {}
        self.session_counter = 0
        self.friends_cache = []
        self.is_running = False
        
    def fetch_friends(self):
        """Lấy danh sách bạn bè"""
        friends_data = []
        try:
            print(f"{Colors.CYAN}🔍 Đang gọi API fetchAllFriends()...{Colors.RESET}")
            friends = self.fetchAllFriends()
            
            print(f"{Colors.YELLOW}📋 Kiểm tra cấu trúc dữ liệu trả về...{Colors.RESET}")
            print(f"{Colors.YELLOW}   Type: {type(friends)}{Colors.RESET}")
            
            # Thử nhiều cách khác nhau để lấy danh sách bạn bè
            
            # Cách 1: Nếu trả về trực tiếp là list
            if isinstance(friends, list):
                print(f"{Colors.GREEN}✅ Dữ liệu trả về là list với {len(friends)} phần tử{Colors.RESET}")
                
                if len(friends) > 0:
                    print(f"{Colors.YELLOW}📋 Kiểm tra phần tử đầu tiên: {type(friends[0])}{Colors.RESET}")
                
                for idx, friend in enumerate(friends):
                    try:
                        # Nếu là dict
                        if isinstance(friend, dict):
                            user_id = friend.get('userId') or friend.get('uid') or friend.get('id') or friend.get('zaloId')
                            display_name = friend.get('displayName') or friend.get('name') or friend.get('dName') or user_id
                        # Nếu là object
                        elif hasattr(friend, 'userId') or hasattr(friend, 'uid'):
                            user_id = getattr(friend, 'userId', None) or getattr(friend, 'uid', None) or getattr(friend, 'id', None)
                            display_name = getattr(friend, 'displayName', None) or getattr(friend, 'name', None) or user_id
                        # Nếu là string (chỉ có ID)
                        elif isinstance(friend, str):
                            user_id = friend
                            display_name = f"User {friend}"
                        else:
                            # Debug phần tử đầu tiên
                            if idx == 0:
                                print(f"{Colors.YELLOW}📋 Cấu trúc phần tử:{Colors.RESET}")
                                if hasattr(friend, '__dict__'):
                                    print(f"{Colors.YELLOW}   Attributes: {list(vars(friend).keys())}{Colors.RESET}")
                                else:
                                    print(f"{Colors.YELLOW}   Content: {friend}{Colors.RESET}")
                            continue
                        
                        if user_id:
                            friends_data.append({
                                "id": str(user_id),
                                "name": str(display_name)
                            })
                    except Exception as e:
                        if idx == 0:
                            print(f"{Colors.RED}❌ Lỗi xử lý phần tử đầu: {e}{Colors.RESET}")
                        continue
            
            # Cách 2: Kiểm tra thuộc tính 'friends'
            elif friends and hasattr(friends, 'friends'):
                print(f"{Colors.GREEN}✅ Tìm thấy thuộc tính 'friends'{Colors.RESET}")
                friend_list = friends.friends
                for friend in friend_list:
                    try:
                        user_id = friend.userId if hasattr(friend, 'userId') else str(friend)
                        display_name = friend.displayName if hasattr(friend, 'displayName') else user_id
                        friends_data.append({
                            "id": user_id,
                            "name": display_name
                        })
                    except:
                        continue
            
            # Cách 3: Kiểm tra nếu là dict
            elif isinstance(friends, dict):
                print(f"{Colors.YELLOW}⚠️ Dữ liệu trả về là dict{Colors.RESET}")
                print(f"{Colors.YELLOW}   Keys: {list(friends.keys())}{Colors.RESET}")
                
                # Thử các key có thể có
                possible_keys = ['friends', 'data', 'friendList', 'friend_list', 'users']
                for key in possible_keys:
                    if key in friends:
                        print(f"{Colors.GREEN}✅ Tìm thấy key '{key}'{Colors.RESET}")
                        friend_list = friends[key]
                        if isinstance(friend_list, list):
                            for friend in friend_list:
                                try:
                                    if isinstance(friend, dict):
                                        user_id = friend.get('userId') or friend.get('uid') or friend.get('id')
                                        display_name = friend.get('displayName') or friend.get('name') or user_id
                                    else:
                                        user_id = friend.userId if hasattr(friend, 'userId') else str(friend)
                                        display_name = friend.displayName if hasattr(friend, 'displayName') else user_id
                                    
                                    if user_id:
                                        friends_data.append({
                                            "id": user_id,
                                            "name": display_name
                                        })
                                except:
                                    continue
                        break
            
            # Cách 4: Kiểm tra tất cả attributes
            elif friends and hasattr(friends, '__dict__'):
                print(f"{Colors.YELLOW}⚠️ Kiểm tra tất cả attributes...{Colors.RESET}")
                attrs = vars(friends)
                print(f"{Colors.YELLOW}   Attributes: {list(attrs.keys())}{Colors.RESET}")
                
                for attr_name, attr_value in attrs.items():
                    if isinstance(attr_value, list) and len(attr_value) > 0:
                        print(f"{Colors.CYAN}🔍 Thử attribute '{attr_name}'{Colors.RESET}")
                        for item in attr_value:
                            try:
                                if hasattr(item, 'userId'):
                                    user_id = item.userId
                                    display_name = item.displayName if hasattr(item, 'displayName') else user_id
                                    friends_data.append({
                                        "id": user_id,
                                        "name": display_name
                                    })
                            except:
                                continue
                        if friends_data:
                            break
            
            if friends_data:
                self.friends_cache = friends_data
                print(f"{Colors.GREEN}✅ Tìm thấy {len(friends_data)} bạn bè{Colors.RESET}")
            else:
                print(f"{Colors.RED}❌ Không tìm thấy bạn bè nào trong dữ liệu trả về{Colors.RESET}")
                print(f"{Colors.YELLOW}💡 Gợi ý: Có thể tài khoản chưa có bạn bè hoặc API trả về định dạng khác{Colors.RESET}")
                
        except Exception as e:
            print(f"{Colors.RED}❌ Lỗi lấy danh sách bạn bè: {e}{Colors.RESET}")
            import traceback
            print(f"{Colors.RED}📋 Chi tiết lỗi:{Colors.RESET}")
            traceback.print_exc()
        
        return friends_data
    
    def create_group_with_name(self, group_name, member_ids=[]):
        """Tạo nhóm với tên cụ thể và danh sách thành viên"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        try:
            # Gọi API tạo nhóm
            print(f"{Colors.CYAN}🔄 [{timestamp}] Đang tạo: {group_name}...{Colors.RESET}")
            
            result = self.createGroup(
                name=group_name,
                description="",
                members=member_ids if member_ids else []
            )
            
            # Debug: Kiểm tra kết quả trả về
            print(f"{Colors.YELLOW}📋 Type của result: {type(result)}{Colors.RESET}")
            
            # Thử nhiều cách lấy group ID
            group_id = None
            
            # Cách 1: Kiểm tra thuộc tính groupId
            if result and hasattr(result, 'groupId'):
                group_id = result.groupId
                print(f"{Colors.GREEN}✅ Lấy ID qua thuộc tính 'groupId'{Colors.RESET}")
            
            # Cách 2: Kiểm tra thuộc tính gid
            elif result and hasattr(result, 'gid'):
                group_id = result.gid
                print(f"{Colors.GREEN}✅ Lấy ID qua thuộc tính 'gid'{Colors.RESET}")
            
            # Cách 3: Nếu là dict
            elif isinstance(result, dict):
                possible_keys = ['groupId', 'gid', 'group_id', 'id', 'grid', 'gridId']
                for key in possible_keys:
                    if key in result:
                        group_id = result[key]
                        print(f"{Colors.GREEN}✅ Lấy ID qua key '{key}'{Colors.RESET}")
                        break
            
            # Cách 4: Kiểm tra tất cả attributes
            elif result and hasattr(result, '__dict__'):
                attrs = vars(result)
                print(f"{Colors.YELLOW}📋 Attributes: {list(attrs.keys())}{Colors.RESET}")
                for attr_name in ['groupId', 'gid', 'group_id', 'id', 'grid', 'gridId']:
                    if attr_name in attrs and attrs[attr_name]:
                        group_id = attrs[attr_name]
                        print(f"{Colors.GREEN}✅ Lấy ID qua attr '{attr_name}'{Colors.RESET}")
                        break
            
            # Cách 5: Thử lấy từ danh sách nhóm
            if not group_id:
                print(f"{Colors.CYAN}🔄 Thử lấy ID từ danh sách nhóm...{Colors.RESET}")
                try:
                    time.sleep(1)  # Đợi API cập nhật
                    all_groups = self.fetchAllGroups()
                    
                    if all_groups and hasattr(all_groups, 'gridVerMap'):
                        for gid, _ in all_groups.gridVerMap.items():
                            try:
                                ginfo = self.fetchGroupInfo(gid)
                                if ginfo.gridInfoMap[gid]["name"] == group_name:
                                    group_id = gid
                                    print(f"{Colors.GREEN}✅ Tìm thấy ID qua danh sách nhóm{Colors.RESET}")
                                    break
                            except:
                                continue
                except Exception as e:
                    print(f"{Colors.YELLOW}⚠️ Không lấy được từ danh sách: {e}{Colors.RESET}")
            
            if group_id:
                self.created_groups.append({
                    'id': group_id,
                    'name': group_name,
                    'time': timestamp,
                    'members': len(member_ids) if member_ids else 0
                })
                members_info = f" | {len(member_ids)} thành viên" if member_ids else " | Nhóm rỗng"
                print(f"{Colors.GREEN}[{timestamp}] [{self.account_name}] ✅ Tạo nhóm: {group_name}{members_info} | ID: {group_id}{Colors.RESET}")
                return True, group_id
            else:
                print(f"{Colors.RED}[{timestamp}] [{self.account_name}] ❌ Không tìm thấy group ID{Colors.RESET}")
                print(f"{Colors.RED}📋 Response: {result}{Colors.RESET}")
                return False, None
                
        except Exception as e:
            print(f"{Colors.RED}[{timestamp}] [{self.account_name}] ❌ Lỗi: {group_name} - {str(e)}{Colors.RESET}")
            import traceback
            print(f"{Colors.RED}📋 Chi tiết:{Colors.RESET}")
            traceback.print_exc()
            return False, None
    
    def create_groups_infinite(self, base_name, delay, session_id, member_ids=[], max_count=None):
        """Vòng lặp tạo nhóm vô hạn hoặc giới hạn số lượng"""
        if session_id not in self.create_sessions:
            return
            
        session = self.create_sessions[session_id]
        counter = 1
        
        while session['running']:
            try:
                # Kiểm tra giới hạn số lượng
                if max_count and counter > max_count:
                    print(f"\n{Colors.CYAN}[{self.account_name}] 🎯 Đã đạt giới hạn {max_count} nhóm{Colors.RESET}")
                    break
                
                # Tạo tên nhóm với số thứ tự
                group_name = f"{base_name} {counter}"
                
                success, group_id = self.create_group_with_name(group_name, member_ids)
                
                if success:
                    session['success_count'] += 1
                else:
                    session['fail_count'] += 1
                
                session['current_index'] = counter
                counter += 1
                
                # Đợi delay trước khi tạo nhóm tiếp theo
                if session['running']:
                    time.sleep(delay)
                    
            except Exception as e:
                print(f"{Colors.RED}❌ [{self.account_name}] Lỗi: {e}{Colors.RESET}")
                session['fail_count'] += 1
                time.sleep(delay)
        
        # Đánh dấu session hoàn thành
        session['running'] = False
        session['completed'] = True
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        total = session['current_index']
        print(f"\n{Colors.CYAN}[{timestamp}] [{self.account_name}] 🎉 HOÀN THÀNH!{Colors.RESET}")
        print(f"{Colors.GREEN}✅ Thành công: {session['success_count']}/{total}{Colors.RESET}")
        print(f"{Colors.RED}❌ Thất bại: {session['fail_count']}/{total}{Colors.RESET}\n")
    
    def start_infinite_session(self, base_name, delay, member_ids=[], max_count=None):
        """Bắt đầu session tạo nhóm vô hạn hoặc có giới hạn"""
        self.session_counter += 1
        session_id = f"session_{self.session_counter}"
        
        self.create_sessions[session_id] = {
            'running': True,
            'completed': False,
            'current_index': 0,
            'total': max_count if max_count else "∞",
            'success_count': 0,
            'fail_count': 0,
            'delay': delay,
            'members': len(member_ids),
            'base_name': base_name,
            'start_time': datetime.now().strftime("%H:%M:%S"),
            'thread': None
        }
        
        thread = threading.Thread(
            target=self.create_groups_infinite,
            args=(base_name, delay, session_id, member_ids, max_count)
        )
        thread.daemon = True
        thread.start()
        
        self.create_sessions[session_id]['thread'] = thread
        self.is_running = True
        return session_id
    
    def stop_session(self, session_id):
        """Dừng session tạo nhóm"""
        if session_id in self.create_sessions:
            self.create_sessions[session_id]['running'] = False
            return True
        return False
    
    def stop_all_sessions(self):
        """Dừng tất cả session"""
        for session_id in list(self.create_sessions.keys()):
            self.create_sessions[session_id]['running'] = False
        self.is_running = False
    
    def get_status(self):
        """Lấy trạng thái session"""
        status = []
        for session_id, session in self.create_sessions.items():
            status.append({
                'session_id': session_id,
                'account_name': self.account_name,
                'current': session['current_index'],
                'total': session['total'],
                'success': session['success_count'],
                'fail': session['fail_count'],
                'running': session['running'],
                'completed': session['completed'],
                'delay': session['delay'],
                'members': session.get('members', 0),
                'base_name': session.get('base_name', ''),
                'start_time': session['start_time']
            })
        return status
    
    def get_created_groups(self):
        """Lấy danh sách nhóm đã tạo"""
        return self.created_groups
    
    def export_groups_to_file(self, filepath):
        """Xuất danh sách nhóm ra file"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# DANH SÁCH NHÓM ĐÃ TẠO - {self.account_name}\n")
                f.write(f"# Tạo lúc: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Tổng số: {len(self.created_groups)} nhóm\n\n")
                
                for idx, group in enumerate(self.created_groups, 1):
                    f.write(f"{idx}. {group['name']}\n")
                    f.write(f"   ID: {group['id']}\n")
                    f.write(f"   Thành viên: {group['members']} người\n")
                    f.write(f"   Thời gian: {group['time']}\n\n")
            
            print(f"{Colors.GREEN}✅ Đã xuất danh sách ra: {filepath}{Colors.RESET}")
            return True
        except Exception as e:
            print(f"{Colors.RED}❌ Lỗi xuất file: {e}{Colors.RESET}")
            return False


class MultiAccountManager:
    """Quản lý nhiều tài khoản bot"""
    def __init__(self):
        self.bots = {}
        self.account_counter = 0
    
    def add_account(self, imei, cookies, account_name=None):
        """Thêm tài khoản mới"""
        self.account_counter += 1
        if not account_name:
            account_name = f"Acc{self.account_counter}"
        
        account_id = f"acc_{self.account_counter}"
        
        try:
            bot = InfiniteGroupBot(imei, cookies, account_name)
            self.bots[account_id] = bot
            return account_id, bot
        except Exception as e:
            print(f"{Colors.RED}❌ Lỗi tạo bot: {e}{Colors.RESET}")
            return None, None
    
    def get_all_status(self):
        """Lấy status từ tất cả tài khoản"""
        all_status = []
        for account_id, bot in self.bots.items():
            all_status.extend(bot.get_status())
        return all_status
    
    def stop_all(self):
        """Dừng tất cả bot"""
        for bot in self.bots.values():
            bot.stop_all_sessions()
    
    def get_all_created_groups(self):
        """Lấy tất cả nhóm đã tạo từ tất cả tài khoản"""
        all_groups = {}
        for account_id, bot in self.bots.items():
            all_groups[bot.account_name] = bot.get_created_groups()
        return all_groups


def select_friends(bot):
    """Chọn bạn bè để thêm vào nhóm"""
    print(f"\n{Colors.CYAN}🔍 Đang tải danh sách bạn bè...{Colors.RESET}\n")
    
    friends = bot.friends_cache
    if not friends:
        friends = bot.fetch_friends()
    
    if not friends:
        print(f"{Colors.YELLOW}⚠️ Không tìm thấy bạn bè nào!{Colors.RESET}")
        print(f"{Colors.CYAN}💡 Bạn có thể:{Colors.RESET}")
        print(f"   1. Tạo nhóm rỗng (không có thành viên)")
        print(f"   2. Nhập ID thành viên thủ công")
        
        choice = input(f"\n👉 Chọn (1/2, Enter = tạo nhóm rỗng): ").strip()
        
        if choice == '2':
            print(f"\n{Colors.CYAN}📝 NHẬP ID THÀNH VIÊN:{Colors.RESET}")
            print(f"   • Nhập các ID cách nhau bởi dấu phẩy")
            print(f"   • VD: 1234567890,9876543210")
            
            ids_input = input(f"\n👉 Nhập ID: ").strip()
            
            if ids_input:
                member_ids = [id.strip() for id in ids_input.split(',') if id.strip()]
                print(f"{Colors.GREEN}✅ Đã thêm {len(member_ids)} ID thành viên{Colors.RESET}")
                return member_ids
        
        print(f"{Colors.YELLOW}⚠️ Sẽ tạo nhóm rỗng (không có thành viên){Colors.RESET}\n")
        return []
    
    # Hiển thị danh sách bạn bè
    print(f"\n{Colors.CYAN}📋 DANH SÁCH BẠN BÈ: (Tổng: {len(friends)}){Colors.RESET}\n")
    
    display_count = min(30, len(friends))
    for i, friend in enumerate(friends[:display_count]):
        print(f"  {i+1}. {friend['name']}")
    
    if len(friends) > display_count:
        print(f"  ... và {len(friends) - display_count} người khác")
    
    print(f"\n{Colors.YELLOW}💡 HƯỚNG DẪN CHỌN:{Colors.RESET}")
    print("  • Nhập số thứ tự cách nhau bởi dấu phẩy (VD: 1,3,5)")
    print("  • Nhập khoảng số (VD: 1-5)")
    print("  • Kết hợp cả hai (VD: 1,3,5-10)")
    print("  • Nhập 'all' để chọn tất cả")
    print("  • Enter để tạo nhóm rỗng")
    
    choice = input(f"\n👉 Chọn thành viên: ").strip()
    
    member_ids = []
    
    if choice.lower() == 'all':
        member_ids = [f['id'] for f in friends]
        print(f"{Colors.GREEN}✅ Đã chọn tất cả {len(member_ids)} người{Colors.RESET}")
    elif choice:
        # Xử lý input
        selected_indices = set()
        parts = choice.split(',')
        
        for part in parts:
            part = part.strip()
            if '-' in part:
                # Khoảng số
                try:
                    start, end = part.split('-')
                    start = int(start.strip())
                    end = int(end.strip())
                    for i in range(start, end + 1):
                        if 1 <= i <= len(friends):
                            selected_indices.add(i - 1)
                except:
                    pass
            else:
                # Số đơn
                try:
                    idx = int(part)
                    if 1 <= idx <= len(friends):
                        selected_indices.add(idx - 1)
                except:
                    pass
        
        member_ids = [friends[i]['id'] for i in sorted(selected_indices)]
        
        if member_ids:
            print(f"\n{Colors.GREEN}✅ Đã chọn {len(member_ids)} thành viên:{Colors.RESET}")
            show_count = min(5, len(member_ids))
            for i in sorted(list(selected_indices))[:show_count]:
                print(f"  • {friends[i]['name']}")
            if len(member_ids) > show_count:
                print(f"  ... và {len(member_ids) - show_count} người khác")
    else:
        print(f"{Colors.YELLOW}⚠️ Sẽ tạo nhóm rỗng (không có thành viên){Colors.RESET}")
    
    return member_ids


def start_create_session(bot):
    """Bắt đầu session tạo nhóm"""
    print(f"\n{Colors.CYAN}{'='*UI_WIDTH}{Colors.RESET}")
    print(f"{Colors.BOLD}🚀 TẠO NHÓM CHO: {bot.account_name}{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*UI_WIDTH}{Colors.RESET}\n")
    
    # Hỏi tên nhóm cơ bản
    group_base_name = input(f"📛 Tên nhóm cơ bản: ").strip()
    
    if not group_base_name:
        print(f"{Colors.RED}❌ Tên nhóm không được để trống!{Colors.RESET}\n")
        return
    
    # Hỏi chế độ: vô hạn hay giới hạn
    print(f"\n{Colors.CYAN}📊 CHẾ ĐỘ TẠO NHÓM:{Colors.RESET}")
    print("  1. Tạo vô hạn (cho đến khi dừng)")
    print("  2. Tạo giới hạn số lượng")
    
    mode = input(f"\n👉 Chọn chế độ (1/2, mặc định 2): ").strip()
    
    max_count = None
    if mode != '1':
        count_str = input(f"🔢 Số lượng nhóm cần tạo: ").strip()
        if count_str.isdigit() and int(count_str) > 0:
            max_count = int(count_str)
        else:
            print(f"{Colors.RED}❌ Số lượng không hợp lệ!{Colors.RESET}\n")
            return
    
    # Xem trước tên nhóm
    if max_count:
        print(f"\n{Colors.GREEN}✅ Sẽ tạo {max_count} nhóm:{Colors.RESET}")
        preview_count = min(5, max_count)
        for i in range(1, preview_count + 1):
            print(f"  {i}. {group_base_name} {i}")
        if max_count > preview_count:
            print(f"  ... và {max_count - preview_count} nhóm khác")
    else:
        print(f"\n{Colors.GREEN}✅ Sẽ tạo nhóm vô hạn:{Colors.RESET}")
        print(f"  1. {group_base_name} 1")
        print(f"  2. {group_base_name} 2")
        print(f"  3. {group_base_name} 3")
        print(f"  ...")
    
    # Hỏi có muốn thêm thành viên không
    add_members = input(f"\n👥 Thêm bạn bè vào nhóm? (y/n, mặc định n): ").strip().lower()
    
    member_ids = []
    if add_members == 'y':
        member_ids = select_friends(bot)
    
    # Hỏi delay
    delay_str = input(f"\n⏱️  Delay giữa các lần tạo (giây, mặc định 2): ").strip()
    delay = int(delay_str) if delay_str.isdigit() else 2
    
    # Xác nhận
    print(f"\n{Colors.CYAN}📊 TỔNG KẾT:{Colors.RESET}")
    print(f"  🔖 Tài khoản: {bot.account_name}")
    print(f"  📛 Tên cơ bản: {group_base_name}")
    if max_count:
        print(f"  🔢 Số lượng: {max_count} nhóm")
    else:
        print(f"  🔢 Số lượng: Vô hạn (∞)")
    print(f"  👥 Thành viên: {len(member_ids)} người")
    print(f"  ⏱️  Delay: {delay}s")
    
    confirm = input(f"\n{Colors.YELLOW}⚠️ Bắt đầu tạo? (y/n): {Colors.RESET}").strip().lower()
    
    if confirm != 'y':
        print(f"{Colors.YELLOW}❌ Đã hủy{Colors.RESET}\n")
        return
    
    # Bắt đầu tạo
    print(f"\n{Colors.CYAN}🚀 Đang khởi động...{Colors.RESET}\n")
    
    session_id = bot.start_infinite_session(group_base_name, delay, member_ids, max_count)
    
    mode_text = f"{max_count} nhóm" if max_count else "Vô hạn (∞)"
    print(f"{Colors.GREEN}✅ Đã bắt đầu tạo nhóm!")
    print(f"   🔖 Tài khoản: {bot.account_name}")
    print(f"   📊 Chế độ: {mode_text}")
    print(f"   👥 Thành viên: {len(member_ids)} người")
    print(f"   ⏱️  Delay: {delay}s{Colors.RESET}\n")


def add_account_interactive(manager):
    """Thêm tài khoản mới"""
    print(f"\n{Colors.CYAN}{'='*UI_WIDTH}{Colors.RESET}")
    print(f"{Colors.BOLD}➕ THÊM TÀI KHOẢN MỚI{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*UI_WIDTH}{Colors.RESET}\n")
    
    account_name = input(f"📛 Tên tài khoản (Enter = tự động): ").strip()
    imei = input(f"📱 IMEI: ").strip()
    
    if not imei:
        print(f"{Colors.RED}❌ IMEI không được để trống!{Colors.RESET}\n")
        return None
    
    cookie_str = input(f"🍪 Cookie (JSON): ").strip()
    
    try:
        cookies = json.loads(cookie_str)
    except:
        print(f"{Colors.RED}❌ Cookie không hợp lệ!{Colors.RESET}\n")
        return None
    
    print(f"\n{Colors.CYAN}🔄 Đang khởi tạo tài khoản...{Colors.RESET}")
    account_id, bot = manager.add_account(imei, cookies, account_name if account_name else None)
    
    if not bot:
        print(f"{Colors.RED}❌ Không thể tạo tài khoản!{Colors.RESET}\n")
        return None
    
    print(f"{Colors.GREEN}✅ Tài khoản {bot.account_name} đã được thêm thành công!{Colors.RESET}\n")
    
    start_now = input(f"🚀 Bắt đầu tạo nhóm ngay? (y/n, mặc định n): ").strip().lower()
    
    if start_now == 'y':
        start_create_session(bot)
    
    return bot


def run_infinite_group_tool():
    """Chạy tool tạo nhóm vô hạn"""
    clear_screen()
    
    draw_box("TOOL TẠO NHÓM ZALO VÔ HẠN", [
        "📱 Tool tạo nhóm tự động với số lượng tùy chỉnh",
        "",
        "✨ Tính năng:",
        "   • Tạo nhóm vô hạn hoặc giới hạn số lượng",
        "   • Thêm bạn bè vào nhóm tự động",
        "   • Hỗ trợ nhiều tài khoản cùng lúc",
        "   • Xuất danh sách nhóm đã tạo",
        "   • Quản lý session theo thời gian thực"
    ], Colors.CYAN)
    
    # Đăng nhập tài khoản đầu tiên
    account_name = input("\n📛 Tên tài khoản (Enter = Acc1): ").strip()
    imei = input("📱 IMEI: ").strip()
    cookie_str = input("🍪 Cookie (JSON): ").strip()
    
    try:
        cookies = json.loads(cookie_str)
    except:
        draw_box("LỖI", ["❌ Cookie không hợp lệ!"], Colors.RED)
        input("\nNhấn Enter để quay lại...")
        return
    
    # Khởi tạo manager và bot đầu tiên
    manager = MultiAccountManager()
    account_id, bot = manager.add_account(imei, cookies, account_name if account_name else None)
    
    if not bot:
        draw_box("LỖI", ["❌ Không thể tạo tài khoản!"], Colors.RED)
        input("\nNhấn Enter để quay lại...")
        return
    
    print(f"\n{Colors.GREEN}✅ Đã khởi tạo tài khoản: {bot.account_name}{Colors.RESET}\n")
    
    # Bắt đầu session tạo nhóm cho tài khoản đầu tiên
    start_create_session(bot)
    
    # Menu quản lý
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*UI_WIDTH}{Colors.RESET}")
    print(f"{Colors.BOLD}🎯 TOOL ĐANG CHẠY - Nhấn Enter để xem menu{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*UI_WIDTH}{Colors.RESET}\n")
    
    while True:
        try:
            cmd = input().strip().lower()
            
            if cmd == "":
                print(f"\n{Colors.CYAN}📊 MENU QUẢN LÝ:{Colors.RESET}")
                print("  themacc  - Thêm tài khoản mới")
                print("  create   - Tạo nhóm cho tài khoản")
                print("  status   - Xem trạng thái chi tiết")
                print("  listacc  - Danh sách tài khoản")
                print("  export   - Xuất danh sách nhóm đã tạo")
                print("  stop     - Dừng session cụ thể")
                print("  stopall  - Dừng tất cả session")
                print("  exit     - Thoát tool")
                print()
            
            elif cmd == "themacc":
                add_account_interactive(manager)
            
            elif cmd == "create":
                # Chọn tài khoản để tạo nhóm
                print(f"\n{Colors.CYAN}📋 DANH SÁCH TÀI KHOẢN:{Colors.RESET}\n")
                bot_list = list(manager.bots.items())
                for i, (acc_id, b) in enumerate(bot_list, 1):
                    created_count = len(b.get_created_groups())
                    status = "🔄 Đang chạy" if b.is_running else "⏸️  Dừng"
                    print(f"  {i}. {b.account_name} - {status} (đã tạo {created_count} nhóm)")
                
                choice = input(f"\n👉 Chọn tài khoản (số): ").strip()
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(bot_list):
                        selected_bot = bot_list[idx][1]
                        start_create_session(selected_bot)
                    else:
                        print(f"{Colors.RED}❌ Số không hợp lệ!{Colors.RESET}\n")
                except ValueError:
                    print(f"{Colors.RED}❌ Vui lòng nhập số!{Colors.RESET}\n")
            
            elif cmd == "listacc":
                print(f"\n{Colors.CYAN}📋 DANH SÁCH TÀI KHOẢN:{Colors.RESET}\n")
                for i, (acc_id, b) in enumerate(manager.bots.items(), 1):
                    created_count = len(b.get_created_groups())
                    status = "🔄 Đang chạy" if b.is_running else "⏸️  Dừng"
                    print(f"  {i}. {b.account_name} - {status}")
                    print(f"     Đã tạo: {created_count} nhóm")
                print()
            
            elif cmd == "status":
                all_status = manager.get_all_status()
                if not all_status:
                    print(f"\n{Colors.YELLOW}⚠️ Không có session nào đang chạy{Colors.RESET}\n")
                else:
                    print(f"\n{Colors.CYAN}{'='*UI_WIDTH}{Colors.RESET}")
                    print(f"{Colors.BOLD}📊 TRẠNG THÁI CHI TIẾT{Colors.RESET}")
                    print(f"{Colors.CYAN}{'='*UI_WIDTH}{Colors.RESET}\n")
                    
                    for s in all_status:
                        status_icon = "🔄" if s['running'] else "✅"
                        total_text = s['total'] if s['total'] != "∞" else "∞"
                        
                        print(f"{status_icon} {Colors.BOLD}{s['account_name']}{Colors.RESET}")
                        print(f"   📛 Tên nhóm: {s['base_name']}")
                        print(f"   📊 Tiến độ: {s['current']}/{total_text}")
                        print(f"   ✅ Thành công: {s['success']} | ❌ Thất bại: {s['fail']}")
                        print(f"   👥 Thành viên: {s['members']} người")
                        print(f"   ⏱️  Delay: {s['delay']}s")
                        print(f"   🕐 Bắt đầu: {s['start_time']}")
                        print(f"   🆔 Session: {s['session_id']}")
                        print()
            
            elif cmd == "export":
                all_groups = manager.get_all_created_groups()
                
                if not any(groups for groups in all_groups.values()):
                    print(f"\n{Colors.YELLOW}⚠️ Chưa có nhóm nào được tạo{Colors.RESET}\n")
                else:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filepath = f"created_groups_{timestamp}.txt"
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(f"# DANH SÁCH NHÓM ĐÃ TẠO - TOOL TẠO NHÓM VÔ HẠN\n")
                        f.write(f"# Xuất lúc: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"{'='*60}\n\n")
                        
                        total_all = 0
                        for account_name, groups in all_groups.items():
                            if groups:
                                f.write(f"\n{'='*60}\n")
                                f.write(f"TÀI KHOẢN: {account_name}\n")
                                f.write(f"Tổng số: {len(groups)} nhóm\n")
                                f.write(f"{'='*60}\n\n")
                                
                                for idx, group in enumerate(groups, 1):
                                    f.write(f"{idx}. {group['name']}\n")
                                    f.write(f"   ID: {group['id']}\n")
                                    f.write(f"   Thành viên: {group.get('members', 0)} người\n")
                                    f.write(f"   Thời gian: {group['time']}\n\n")
                                
                                total_all += len(groups)
                        
                        f.write(f"\n{'='*60}\n")
                        f.write(f"TỔNG CỘNG: {total_all} nhóm từ {len([g for g in all_groups.values() if g])} tài khoản\n")
                        f.write(f"{'='*60}\n")
                    
                    print(f"\n{Colors.GREEN}✅ Đã xuất danh sách ra: {filepath}{Colors.RESET}")
                    print(f"   📊 Tổng: {total_all} nhóm\n")
            
            elif cmd == "stop":
                all_status = manager.get_all_status()
                running_sessions = [s for s in all_status if s['running']]
                
                if not running_sessions:
                    print(f"\n{Colors.YELLOW}⚠️ Không có session nào đang chạy{Colors.RESET}\n")
                else:
                    print(f"\n{Colors.CYAN}📋 SESSION ĐANG CHẠY:{Colors.RESET}\n")
                    for i, s in enumerate(running_sessions, 1):
                        print(f"  {i}. {s['account_name']} - {s['base_name']} ({s['current']}/{s['total']})")
                    
                    choice = input(f"\n👉 Chọn session cần dừng (số): ").strip()
                    try:
                        idx = int(choice) - 1
                        if 0 <= idx < len(running_sessions):
                            session_id = running_sessions[idx]['session_id']
                            account_name = running_sessions[idx]['account_name']
                            
                            # Tìm bot và dừng session
                            for bot in manager.bots.values():
                                if bot.account_name == account_name:
                                    bot.stop_session(session_id)
                                    print(f"{Colors.GREEN}✅ Đã dừng session của {account_name}!{Colors.RESET}\n")
                                    break
                        else:
                            print(f"{Colors.RED}❌ Số không hợp lệ!{Colors.RESET}\n")
                    except ValueError:
                        print(f"{Colors.RED}❌ Vui lòng nhập số!{Colors.RESET}\n")
            
            elif cmd == "stopall":
                confirm = input(f"\n{Colors.YELLOW}⚠️ Dừng tất cả session đang chạy? (y/n): {Colors.RESET}").strip().lower()
                if confirm == 'y':
                    manager.stop_all()
                    print(f"{Colors.GREEN}✅ Đã dừng tất cả session!{Colors.RESET}\n")
            
            elif cmd == "exit":
                confirm = input(f"\n{Colors.YELLOW}⚠️ Thoát tool? Tất cả session sẽ bị dừng. (y/n): {Colors.RESET}").strip().lower()
                if confirm == 'y':
                    manager.stop_all()
                    print(f"\n{Colors.GREEN}✅ Đã thoát tool. Cảm ơn bạn đã sử dụng!{Colors.RESET}\n")
                    break
            
            else:
                print(f"{Colors.RED}❌ Lệnh không hợp lệ! Nhấn Enter để xem menu.{Colors.RESET}\n")
        
        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}⚠️ Đã nhận Ctrl+C{Colors.RESET}")
            confirm = input(f"Thoát tool? (y/n): ").strip().lower()
            if confirm == 'y':
                manager.stop_all()
                print(f"\n{Colors.GREEN}✅ Đã thoát!{Colors.RESET}\n")
                break
        
        except Exception as e:
            print(f"{Colors.RED}❌ Lỗi: {e}{Colors.RESET}\n")


if __name__ == "__main__":
    try:
        run_infinite_group_tool()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.GREEN}✅ Tool đã được dừng!{Colors.RESET}\n")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Lỗi nghiêm trọng: {e}{Colors.RESET}\n")
        import traceback
        traceback.print_exc()