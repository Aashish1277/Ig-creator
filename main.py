import os
import random
import string
import time
import names
import requests
import telebot
from flask import Flask
import threading
from telebot import types

# --- RENDER KEEP-ALIVE SERVER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running 24/7", 200

def run_flask():
    app.run(host='0.0.0.0', port=10000)

# Start Flask in background thread
flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()

# --- BOT INITIALIZATION ---
BOT_TOKEN = os.getenv('BOT_TOKEN', '8411999028:AAHI_lRK4GgKqRAZgFfqw4PCK2h5ajJ_CfY')
bot = telebot.TeleBot(BOT_TOKEN)

# User State Tracking
user_states = {}

# --- ORIGINAL CORE DATA & LOGIC (100% RETAINED) ---
INDIAN_FIRST_NAMES = ["Aarav","Vihaan","Vivaan","Ananya","Diya","Advik","Kabir","Aaradhya","Reyansh","Sai","Arjun","Ishaan","Rudra","Sia","Myra","Ayaan","Shaurya","Anaya","Krisha","Kavya","Rohan","Shreya","Ishita","Yash","Priya","Riya","Rahul","Amit","Sumit","Pooja","Neha","Raj","Simran","Aditya","Krishna","Laksh","Tanvi","Ishika","Ved","Yuvraj","Anushka","Divya","Sanya","Ria","Jay","Virat","Ravindra","Sneha","Nikhil"]
INDIAN_LAST_NAMES = ["Sharma","Verma","Gupta","Kumar","Singh","Patel","Reddy","Rao","Yadav","Jha","Malhotra","Mehta","Choudhary","Thakur","Mishra","Trivedi","Dwivedi","Pandey","Tiwari","Joshi","Desai","Shah","Nair","Menon","Iyer","Khan","Ansari","Sheikh"]
TITLES = ["official","real","the","ig","india","indian","fan","lover","world","zone"]

def generate_indian_username():
    first = random.choice(INDIAN_FIRST_NAMES).lower()
    last = random.choice(INDIAN_LAST_NAMES).lower()
    title = random.choice(TITLES).lower()
    num = random.randint(10, 9999)
    patterns = [
        f"{first}{last}{num}", f"{first}_{last}{num}", f"{first}.{last}{num}",
        f"{first}{num}{last}", f"{title}{first}{last}{num}", f"{first}{last}{title}{num}",
        f"{first}{random.randint(100,999)}", f"{first}{last}{random.randint(1000,9999)}"
    ]
    return random.choice(patterns)

def check_username_availability(username, headers):
    try:
        r = requests.post(
            'https://www.instagram.com/api/v1/users/check_username/',
            headers=headers, data={'username': username}, timeout=30
        )
        if r.status_code == 200:
            return r.json().get('available', False)
    except:
        pass
    return False

def get_headers(Country='US', Language='en'):
    try:
        an_agent = f'Mozilla/5.0 (Linux; Android {random.randint(9,13)}; {"".join(random.choices(string.ascii_uppercase, k=3))}{random.randint(111,999)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
        r = requests.get('https://www.instagram.com/api/v1/web/accounts/login/ajax/', 
                       headers={'user-agent': an_agent}, timeout=30).cookies
        resp = requests.get('https://www.instagram.com/', headers={'user-agent': an_agent}, timeout=30)
        appid = resp.text.split('APP_ID":"')[1].split('"')[0]
        rollout = resp.text.split('rollout_hash":"')[1].split('"')[0]
        headers = {
            'authority': 'www.instagram.com',
            'accept': '*/*',
            'accept-language': f'{Language}-{Country},en-US;q=0.8,en;q=0.7',
            'content-type': 'application/x-www-form-urlencoded',
            'cookie': f'dpr=3; csrftoken={r["csrftoken"]}; mid={r["mid"]}; ig_did={r["ig_did"]}',
            'origin': 'https://www.instagram.com',
            'referer': 'https://www.instagram.com/accounts/signup/email/',
            'user-agent': an_agent,
            'x-csrftoken': r["csrftoken"],
            'x-ig-app-id': appid,
            'x-instagram-ajax': rollout,
            'x-web-device-id': r["ig_did"],
        }
        return headers
    except:
        return None

def build_ordered_cookie_string(cdict):
    order = ["mid", "ig_did", "csrftoken", "sessionid", "ds_user_id"]
    parts = [f"{key}={cdict[key]}" for key in order if key in cdict and cdict[key]]
    return '; '.join(parts)

def Send_SMS(Headers, Email):
    try:
        device_id = Headers['cookie'].split('mid=')[1].split(';')[0]
        data = {'device_id': device_id, 'email': Email}
        r = requests.post('https://www.instagram.com/api/v1/accounts/send_verify_email/', 
                         headers=Headers, data=data, timeout=30)
        return r.text
    except:
        return None

def Validate_Code(Headers, Email, Code):
    try:
        device_id = Headers['cookie'].split('mid=')[1].split(';')[0]
        data = {'code': Code, 'device_id': device_id, 'email': Email}
        r = requests.post('https://www.instagram.com/api/v1/accounts/check_confirmation_code/', 
                         headers=Headers, data=data, timeout=30)
        return r
    except:
        return None

# --- TELEGRAM INTERFACE ADAPTATION ---

@bot.message_handler(commands=['start'])
def start_cmd(message):
    logo = "✨ Instagram Auto Creator v4.6\nBy @SpeakeMarin | @Frozen_CC\n\nSend /create to begin."
    bot.send_message(message.chat.id, logo)

@bot.message_handler(commands=['create'])
def ask_email(message):
    bot.send_message(message.chat.id, "📧 Enter Your Email address:")
    bot.register_next_step_handler(message, process_email)

def process_email(message):
    email = message.text.strip()
    chat_id = message.chat.id
    
    bot.send_message(chat_id, "⏳ Fetching secure headers and sending code...")
    headers = get_headers()
    if not headers:
        bot.send_message(chat_id, "❌ Error generating session. Try again.")
        return

    ss = Send_SMS(headers, email)
    if ss and 'email_sent":true' in ss:
        user_states[chat_id] = {'email': email, 'headers': headers}
        bot.send_message(chat_id, f"✅ Code sent to {email}\n\n👩‍💻 Enter the verification code:")
        bot.register_next_step_handler(message, process_otp)
    else:
        bot.send_message(chat_id, "❌ Failed to send SMS. Check your email or try later.")

def process_otp(message):
    chat_id = message.chat.id
    otp = message.text.strip()
    
    if chat_id not in user_states:
        bot.send_message(chat_id, "Session expired. Use /create")
        return

    state = user_states[chat_id]
    bot.send_message(chat_id, "🔄 Validating OTP...")
    
    val_resp = Validate_Code(state['headers'], state['email'], otp)
    
    if val_resp and 'status":"ok' in val_resp.text:
        bot.send_message(chat_id, "✅ OTP Verified. Finalizing account creation...")
        signup_code = val_resp.json().get('signup_code')
        perform_creation(chat_id, state['headers'], state['email'], signup_code)
    else:
        bot.send_message(chat_id, "❌ Invalid OTP. Use /create to restart.")

def perform_creation(chat_id, Headers, Email, SignUpCode):
    try:
        firstname = names.get_first_name()
        # Find available username
        UserName = None
        for _ in range(5):
            candidate = generate_indian_username()
            if check_username_availability(candidate, Headers):
                UserName = candidate
                break
        
        if not UserName: UserName = generate_indian_username() + str(random.randint(100,999))
        
        Password = firstname.strip() + '@' + str(random.randint(111,999))
        
        data = {
            'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{round(time.time())}:{Password}',
            'email': Email,
            'username': UserName,
            'first_name': firstname,
            'month': random.randint(1, 12),
            'day': random.randint(1, 28),
            'year': random.randint(1990, 2001),
            'client_id': Headers['cookie'].split('mid=')[1].split(';')[0],
            'seamless_login_enabled': '1',
            'tos_version': 'row',
            'force_sign_up_code': SignUpCode,
        }

        response = requests.post(
            'https://www.instagram.com/api/v1/web/accounts/web_create_ajax/',
            headers=Headers, data=data, timeout=40
        )

        if '"account_created":true' in response.text:
            sessionid = response.cookies.get('sessionid')
            
            cookie_dict = {
                'sessionid': sessionid,
                'csrftoken': Headers.get('x-csrftoken'),
                'mid': Headers.get('cookie', '').split('mid=')[1].split(';')[0],
                'ig_did': Headers.get('cookie', '').split('ig_did=')[1].split(';')[0],
            }
            cookie_str = build_ordered_cookie_string(cookie_dict)

            success_msg = (
                f"🎉 *Account Created Successfully!*\n\n"
                f"👤 *Username:* `{UserName}`\n"
                f"🔑 *Password:* `{Password}`\n"
                f"📧 *Email:* `{Email}`\n\n"
                f"🍪 *Cookies:*\n`{cookie_str}`"
            )
            bot.send_message(chat_id, success_msg, parse_mode='Markdown')
            show_post_menu(chat_id)
        else:
            bot.send_message(chat_id, f"❌ Creation failed: {response.text[:200]}")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error: {str(e)}")

def show_post_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Create with SAME email", "Create with NEW email", "Exit")
    msg = bot.send_message(chat_id, "What would you like to do next?", reply_markup=markup)
    bot.register_next_step_handler(msg, handle_menu_choice)

def handle_menu_choice(message):
    chat_id = message.chat.id
    choice = message.text
    if "SAME" in choice:
        state = user_states.get(chat_id)
        if state:
            bot.send_message(chat_id, f"Using same email → {state['email']}")
            process_email(telebot.types.Message(None, None, None, chat_id, None, state['email'], None, None, None))
    elif "NEW" in choice:
        ask_email(message)
    else:
        bot.send_message(chat_id, "Goodbye! Use /create to return.", reply_markup=types.ReplyKeyboardRemove())

if __name__ == "__main__":
    print("Bot is starting on Render.com...")
    bot.infinity_polling()
