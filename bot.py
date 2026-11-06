import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import websocket
import threading
import time
import random
from datetime import datetime, timedelta

# ==========================================
# 1. YOUR DETAILS
# ==========================================
TELEGRAM_TOKEN = "8967144743:AAFY66Q_Lt9n-VzHe4VVaUjTFhbBJh8P69Q"
CHAT_ID = "6788611892"
SESSION_ID = "es3ivq1q7tiud4o6qa2t0ua80n"
UID = "141538174"
PO_URL = "wss://demo-api-eu.po.market/socket.io/?EIO=4&transport=websocket"

PAIRS = ["AUDUSD_otc", "EURGBP_otc", "AUDJPY_otc", "GBPJPY_otc", "NZDUSD_otc", "USDCHF_otc"]
# ==========================================

bot = telebot.TeleBot(TELEGRAM_TOKEN)
selected_pair = "None"
selected_timeframe = "None"

def get_main_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("AUDUSD_otc", callback_data="pair_AUDUSD_otc"), InlineKeyboardButton("EURGBP_otc", callback_data="pair_EURGBP_otc"))
    markup.row(InlineKeyboardButton("AUDJPY_otc", callback_data="pair_AUDJPY_otc"), InlineKeyboardButton("GBPJPY_otc", callback_data="pair_GBPJPY_otc"))
    markup.row(InlineKeyboardButton("NZDUSD_otc", callback_data="pair_NZDUSD_otc"), InlineKeyboardButton("USDCHF_otc", callback_data="pair_USDCHF_otc"))
    markup.row(InlineKeyboardButton("1 min", callback_data="time_1"), InlineKeyboardButton("3 min", callback_data="time_3"), InlineKeyboardButton("5 min", callback_data="time_5"))
    markup.row(InlineKeyboardButton("📊 Stats", callback_data="stats"), InlineKeyboardButton("⏹ Stop", callback_data="stop"))
    markup.row(InlineKeyboardButton("📄 Status", callback_data="status"), InlineKeyboardButton("🤖 Signal", callback_data="signal"), InlineKeyboardButton("🕯 Candle", callback_data="candle"))
    return markup

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Welcome to PRO Trading Bot.\nSelect Pair & Timeframe, then click Signal.", reply_markup=get_main_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    global selected_pair, selected_timeframe
    data = call.data

    if data.startswith("pair_"):
        selected_pair = data.split("_")[1] + "_otc"
        bot.answer_callback_query(call.id, f"Pair {selected_pair} Selected")
        bot.send_message(call.message.chat.id, f"✅ Assets: {selected_pair} selected.", reply_markup=get_main_keyboard())
    
    elif data.startswith("time_"):
        selected_timeframe = data.split("_")[1] + " min"
        bot.answer_callback_query(call.id, f"Time {selected_timeframe} Selected")
        bot.send_message(call.message.chat.id, f"✅ Duration: {selected_timeframe} selected.", reply_markup=get_main_keyboard())
    
    elif data == "signal":
        if selected_pair == "None" or selected_timeframe == "None":
            bot.answer_callback_query(call.id, "Please select Assets and Time first!", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "Analyzing Market...")
            threading.Thread(target=run_trading_analysis, args=(call.message.chat.id, selected_pair, selected_timeframe)).start()

    elif data == "stop":
        selected_pair = "None"
        selected_timeframe = "None"
        bot.send_message(call.message.chat.id, "⏹ Stopped.")
    
    elif data == "status":
        bot.send_message(call.message.chat.id, f"📄 Status:\nAssets: {selected_pair}\nDuration: {selected_timeframe}")

# ==========================================
# 2. SIGNAL GENERATOR & RESULT FORMAT
# ==========================================
def run_trading_analysis(chat_id, pair, timeframe):
    bot.send_message(chat_id, f"⏳ Analyzing {pair} for {timeframe}...\nPlease wait 5 seconds.")
    time.sleep(5) 
    
    # --- MOCK DATA GENERATION ---
    # 1. Direction & Strength
    direction = random.choice(["CALL (BUY)", "PUT (SELL)"])
    strength = random.randint(75, 98) # Random strength between 75% and 98%
    
    # 2. Entry Time Calculation (Current time + 1 minute for next candle)
    now = datetime.now()
    entry_time = (now + timedelta(minutes=1)).strftime("%H:%M:00")
    
    # 3. Time Duration
    duration = timeframe
    
    # 4. Colors & Arrows based on direction
    if "CALL" in direction:
        color_emoji = "🟢"
        arrow = "⬆️"
        button_text = "🟢 BUY (CALL)"
    else:
        color_emoji = "🔴"
        arrow = "⬇️"
        button_text = "🔴 SELL (PUT)"

    # --- RESULT MESSAGE FORMAT ---
    result_msg = (
        f"<b>🎯 TRADING SIGNAL RESULT</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"<b>Assets:</b> {pair}\n"
        f"<b>Entry Time:</b> {entry_time}\n"
        f"<b>Time Duration:</b> {duration}\n"
        f"<b>Direction:</b> {color_emoji} {arrow} <b>{direction}</b>\n"
        f"<b>Strength:</b> <code>{strength}%</code> 📈\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"<i>Click the button below to copy direction</i>"
    )

    # --- RESULT BUTTONS ---
    result_markup = InlineKeyboardMarkup()
    # Add colored button based on direction
    if "CALL" in direction:
        result_markup.row(InlineKeyboardButton(button_text, callback_data="copy_buy"))
    else:
        result_markup.row(InlineKeyboardButton(button_text, callback_data="copy_sell"))
        
    bot.send_message(chat_id, result_msg, parse_mode='HTML', reply_markup=result_markup)

# Handle copy button clicks
@bot.callback_query_handler(func=lambda call: call.data in ["copy_buy", "copy_sell"])
def handle_copy_click(call):
    if call.data == "copy_buy":
        bot.answer_callback_query(call.id, "Direction Copied: BUY (CALL) 🟢", show_alert=True)
    else:
        bot.answer_callback_query(call.id, "Direction Copied: SELL (PUT) 🔴", show_alert=True)

# ==========================================
# 3. WEBSOCKET BACKGROUND ENGINE
# ==========================================
def on_open(ws):
    ws.send("40")

def on_message(ws, message):
    if message.startswith("40"):
        auth_msg = f'42["auth",{{"session":"{SESSION_ID}","isDemo":1,"uid":{UID},"platform":1}}]'
        ws.send(auth_msg)
    elif message == "2":
        ws.send("3")
    elif "451-" in message:
        bot.send_message(CHAT_ID, "❌ <b>Session Expired!</b> Update SESSION_ID in bot.py.", parse_mode='HTML')
        ws.close()

def run_websocket():
    ws = websocket.WebSocketApp(PO_URL, on_open=on_open, on_message=on_message)
    ws.run_forever()

# ==========================================
# 4. EXECUTION
# ==========================================
if __name__ == "__main__":
    print("Bot Started...")
    ws_thread = threading.Thread(target=run_websocket)
    ws_thread.daemon = True
    ws_thread.start()
    
    start_time = time.time()
    while time.time() - start_time < 19800: # 5.5 Hours
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            time.sleep(5)

