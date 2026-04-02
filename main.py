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
import io

# --- RENDER KEEP-ALIVE SERVER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running 24/7", 200

def run_flask():
    # Use port 10000 for Render
    app.run(host='0.0.0.0', port=10000)

flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()

# --- BOT INITIALIZATION ---
# Replace with your actual token
BOT_TOKEN = os.getenv('BOT_TOKEN', '8411999028:AAHI_lRK4GgKqRAZgFfqw4PCK2h5ajJ_CfY')
bot = telebot.TeleBot(BOT_TOKEN)

# User State Tracking (Stores Session and Data)
user_states = {}

# --- CORE DATA ---
INDIAN_FIRST_NAMES = ["Aarav","Vihaan","Vivaan","Ananya","Diya","Advik","Kabir","Aaradhya","Reyansh","Sai","Arjun","Ishaan","Rudra","Sia","Myra","Ayaan","Shaurya","Anaya","Krisha","Kavya","Rohan","Shreya","Ishita","Yash","Priya","Riya","Rahul","Amit","Sumit","Pooja","Neha","Raj","Simran","Aditya","Krishna","Laksh","Tanvi","Ishika","Ved","Yuvraj","Anushka","Divya","Sanya","Ria","Jay","Virat","Ravindra","Sneha","Nikhil"]
INDIAN_LAST_NAMES = ["Sharma","Verma","Gupta","Kumar","Singh","Patel","Reddy","Rao","Yadav","Jha","Malhotra","Mehta","Choudhary","Thakur","Mishra","Trivedi","Dwivedi","Pandey","Tiwari","Joshi","Desai","Shah","Nair","Menon","Iyer","Khan","Ansari","Sheikh"]
TITLES = ["official","real","the","ig","india","indian","fan","lover","world","zone"]

# --- HELPER FUNCTIONS ---

def generate_indian_username():
    first = random.choice(INDIAN_FIRST_NAMES).lower()
    last = random.choice(INDIAN_LAST_NAMES).lower()
    title = random.choice(TITLES).lower()
    num = random.randint(10, 9999)
    patterns = [
        f"{first}{last}{num}", f"{first}_{last}{num}", f"{first}.{last}{num}",
        f"{first}{num}{last}", f"{title}{first}{last}{num}", f"{first}{last}{title}{num}"
    ]
    return random.choice(patterns)

def get_initial_session():
    """Initializes a session and gets the required Instagram cookies/headers."""
    session = requests.Session()
    ua = f'Mozilla/5.0 (Linux; Android {random.randint(9,13)}; SM-G9{random.randint(100,999)}B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
    session.headers.update({'user-agent': ua})
    
    try:
        # Initial hits to get cookies
        session.get('https://www.instagram.com/accounts/emailsignup/', timeout=30)
        resp = session.get('https://www.instagram.com/', timeout=30)
        
        # Extract App ID from page source
        appid = resp.text.split('APP_ID":"')[1].split('"')[0]
        rollout = resp.text.split('rollout_hash":"')[1].split('"')[0]
        
        csrf = session.cookies.get_dict().get('csrftoken')
        
        session.headers.update({
            'authority': 'www.instagram.com',
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.instagram.com',
            'referer': 'https://www.instagram.com/accounts/emailsignup/',
            'x-csrftoken': str(csrf),
            'x-ig-app-id': str(appid),
            'x-instagram-ajax': str(rollout),
            'x-web-device-id': session.cookies.get_dict().get('ig_did'),
        })
        return session
    except Exception:
        return None

def check_username_availability(session, username):
    try:
        r = session.post('https://www.instagram.com/api/v1/users/check_username/', data={'username': username}, timeout=30)
        return r.json().get('available', False)
    except:
        return False

def get_random_photo():
    """Download random high-quality photo."""
    try:
        url = f"https://picsum.photos/1080/1080?random={random.randint(1, 1000)}"
        res = requests.get(url, timeout=20)
        return res.content if res.status_code == 200 else None
    except:
        return None

def upload_pfp(session, photo_data):
    try:
        url = "https://www.instagram.com/api/v1/accounts/change_profile_picture/"
        files = {'profile_pic': ('p.jpg', photo_data, 'image/jpeg')}
        h = session.headers.copy()
        h.pop('content-type', None)
        r = session.post(url, headers=h, files=files, timeout=30)
        return r.status_code == 200
    except:
        return False

def upload_post(session, photo_data, caption=""):
    try:
        upload_id = str(int(time.time() * 1000))
        # Step 1: Upload
        up_url = "https://www.instagram.com/api/v1/web/library/upload_photo/"
        h = session.headers.copy()
        h.pop('content-type', None)
        r1 = session.post(up_url, headers=h, data={'upload_id': upload_id, 'media_type': '1'}, files={'photo': ('f.jpg', photo_data, 'image/jpeg')}, timeout=30)
        
        if r1.status_code == 200:
            # Step 2: Configure
            conf_url = "https://www.instagram.com/api/v1/media/configure/"
            r2 = session.post(conf_url, data={'upload_id': upload_id, 'caption': caption}, timeout=30)
            return r2.status_code == 200
    except:
        return False

# --- TELEGRAM BOT HANDLERS ---

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "🚀 *Instagram Creator v6.0*\nAuto PFP + 2 Posts included.\n\nUse /create to begin.", parse_mode='Markdown')

@bot.message_handler(commands=['create'])
def start_create(message):
    bot.send_message(message.chat.id, "📧 *Step 1:* Enter Email address:")
    bot.register_next_step_handler(message, handle_email)

def handle_email(message):
    email = message.text.strip()
    chat_id = message.chat.id
    
    bot.send_message(chat_id, "⏳ Initializing secure session...")
    session = get_initial_session()
    
    if not session:
        bot.send_message(chat_id, "❌ Session error. Try /create again.")
        return

    bot.send_message(chat_id, "📩 Sending verification code...")
    try:
        mid = session.cookies.get_dict().get('mid')
        r = session.post('https://www.instagram.com/api/v1/accounts/send_verify_email/', 
                        data={'device_id': mid, 'email': email}, timeout=30)
        
        if 'email_sent":true' in r.text:
            user_states[chat_id] = {'session': session, 'email': email}
            bot.send_message(chat_id, f"✅ Code sent to {email}\n\n🔢 *Step 2:* Enter the 6-digit OTP:")
            bot.register_next_step_handler(message, handle_otp)
        else:
            bot.send_message(chat_id, f"❌ SMS failed: {r.text[:100]}")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error: {str(e)}")

def handle_otp(message):
    chat_id = message.chat.id
    otp = message.text.strip()
    
    if chat_id not in user_states:
        bot.send_message(chat_id, "Session expired. Use /create")
        return

    state = user_states[chat_id]
    session = state['session']
    
    bot.send_message(chat_id, "🔄 Verifying code...")
    try:
        mid = session.cookies.get_dict().get('mid')
        r = session.post('https://www.instagram.com/api/v1/accounts/check_confirmation_code/', 
                        data={'code': otp, 'device_id': mid, 'email': state['email']}, timeout=30)
        
        if 'status":"ok' in r.text:
            signup_code = r.json().get('signup_code')
            bot.send_message(chat_id, "✅ Code accepted! Creating account...")
            finish_creation(chat_id, signup_code)
        else:
            bot.send_message(chat_id, "❌ Invalid code. Try /create again.")
    except Exception as e:
        bot.send_message(chat_id, f"❌ OTP Error: {str(e)}")

def finish_creation(chat_id, signup_code):
    state = user_states[chat_id]
    session = state['session']
    email = state['email']
    
    try:
        # Generate Details
        fname = names.get_first_name()
        uname = generate_indian_username()
        while not check_username_availability(session, uname):
            uname = generate_indian_username()
        
        password = fname + "@" + str(random.randint(111, 999))
        
        data = {
            'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{round(time.time())}:{password}',
            'email': email,
            'username': uname,
            'first_name': fname,
            'month': random.randint(1, 12),
            'day': random.randint(1, 28),
            'year': random.randint(1992, 2002),
            'client_id': session.cookies.get_dict().get('mid'),
            'seamless_login_enabled': '1',
            'tos_version': 'row',
            'force_sign_up_code': signup_code,
        }

        r = session.post('https://www.instagram.com/api/v1/web/accounts/web_create_ajax/', data=data, timeout=45)
        
        if '"account_created":true' in r.text:
            bot.send_message(chat_id, "🎉 Account Created! Starting auto-uploads...")
            
            # --- AUTO MEDIA ---
            # 1. Profile Picture
            photo = get_random_photo()
            if photo and upload_pfp(session, photo):
                bot.send_message(chat_id, "✅ Profile picture updated.")
            
            # 2. Two Posts
            for i in range(1, 3):
                post_p = get_random_photo()
                if post_p and upload_post(session, post_p, caption=f"Post {i} #vibes"):
                    bot.send_message(chat_id, f"✅ Post {i}/2 uploaded.")
                time.sleep(2)

            # --- FINAL OUTPUT ---
            cookies = session.cookies.get_dict()
            cookie_str = f"mid={cookies.get('mid')}; ig_did={cookies.get('ig_did')}; csrftoken={cookies.get('csrftoken')}; sessionid={cookies.get('sessionid')}; ds_user_id={cookies.get('ds_user_id')}"
            
            res_msg = (
                f"✅ *SUCCESS!*\n\n"
                f"👤 *User:* `{uname}`\n"
                f"🔑 *Pass:* `{password}`\n"
                f"📧 *Email:* `{email}`\n\n"
                f"🍪 *Cookies:* `{cookie_str}`"
            )
            bot.send_message(chat_id, res_msg, parse_mode='Markdown')
        else:
            bot.send_message(chat_id, f"❌ Failed: {r.text[:200]}")
            
    except Exception as e:
        bot.send_message(chat_id, f"❌ Final Step Error: {str(e)}")

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling() 
