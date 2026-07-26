import time, threading, math, sqlite3, json, urllib.request, urllib.error, urllib.parse
from collections import deque, Counter
from datetime import datetime, timezone, timedelta
from flask import Flask
import os

# ═══════════════════════ FLASK KEEP-ALIVE ═══════════════════════
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()

# ═══════════════════════ CONFIGURATION ═══════════════════════
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"               # 🔁 আপনার বট টোকেন
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}/"
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json?ts={}"

SHEET_ID = "YOUR_GOOGLE_SHEET_ID_HERE"          # 🔁 আপনার শিট আইডি
SHEET_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

ADMIN_USER_IDS = {1234567890}                   # 🔁 অ্যাডমিন টেলিগ্রাম আইডি
ADMIN_USERNAME = "your_username"                # 🔁 অ্যাডমিন টেলিগ্রাম ইউজারনেম (@ ছাড়া)

IST = timezone(timedelta(hours=5, minutes=30))

# ═══════════════════ GOOGLE SHEETS SYNC ═══════════════════
sheet_data_cache = []
sheet_lock = threading.Lock()

def fetch_sheet_csv(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.read().decode('utf-8')
    except Exception as e:
        print("Sheet fetch error:", e)
        return None

def parse_sheet(csv_text):
    lines = csv_text.strip().split('\n')
    if len(lines) < 2:
        return []
    headers = [h.strip() for h in lines[0].split(',')]
    users = []
    for line in lines[1:]:
        if not line.strip():
            continue
        values = [v.strip() for v in line.split(',')]
        user = {}
        for i, header in enumerate(headers):
            user[header] = values[i] if i < len(values) else ''
        try:
            user['telegram_id'] = int(user.get('Telegram ID', '0'))
        except:
            user['telegram_id'] = 0
        users.append(user)
    return users

def refresh_sheet_cache():
    global sheet_data_cache
    while True:
        csv_text = fetch_sheet_csv(SHEET_CSV_URL)
        if csv_text:
            with sheet_lock:
                sheet_data_cache = parse_sheet(csv_text)
        time.sleep(30)

threading.Thread(target=refresh_sheet_cache, daemon=True).start()

def get_user_info(user_id):
    with sheet_lock:
        for user in sheet_data_cache:
            if user.get('telegram_id') == user_id:
                exp_str = user.get('Expired (Date and Time)', '').strip()
                if exp_str:
                    fmts = ["%Y-%m-%d %H:%M:%S", "%m/%d/%Y %H:%M:%S", "%d/%m/%Y %H:%M:%S"]
                    expired_dt = None
                    for f in fmts:
                        try:
                            expired_dt = datetime.strptime(exp_str, f)
                            break
                        except ValueError:
                            continue
                    if expired_dt:
                        expired_dt = expired_dt.replace(tzinfo=IST)
                        if datetime.now(IST) > expired_dt:
                            return 'deactive', user
                return 'active', user
    return 'not_found', None

def get_user_status(user_id):
    status, _ = get_user_info(user_id)
    return status

# ═══════════════════ DATABASE ═══════════════════
def init_db():
    conn = sqlite3.connect('predictions.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS rounds
                 (period TEXT PRIMARY KEY, number INTEGER, size TEXT,
                  prediction TEXT, result TEXT, range_pred TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    for col in ['range_pred', 'created_at']:
        try: c.execute(f"ALTER TABLE rounds ADD COLUMN {col} TEXT")
        except: pass
    conn.commit(); conn.close()

def save_round(period, number, size, prediction, result, range_pred):
    conn = sqlite3.connect('predictions.db')
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO rounds VALUES (?,?,?,?,?,?,CURRENT_TIMESTAMP)''',
              (period, number, size, prediction, result, range_pred))
    conn.commit(); conn.close()

def load_recent_history(limit=300):
    conn = sqlite3.connect('predictions.db')
    c = conn.cursor()
    try:
        c.execute('''SELECT period, number, size, prediction, result, range_pred FROM rounds
                     ORDER BY period DESC LIMIT ?''', (limit,))
        rows = c.fetchall()
    except:
        c.execute('''SELECT period, number, size, prediction, result FROM rounds
                     ORDER BY period DESC LIMIT ?''', (limit,))
        rows = [(r[0],r[1],r[2],r[3],r[4],None) for r in c.fetchall()]
    conn.close()
    return rows

def get_first_and_last():
    conn = sqlite3.connect('predictions.db')
    c = conn.cursor()
    c.execute("SELECT period, number, size, prediction, result, range_pred FROM rounds ORDER BY period ASC LIMIT 2")
    first_two = c.fetchall()
    c.execute("SELECT period, number, size, prediction, result, range_pred FROM rounds ORDER BY period DESC LIMIT 2")
    last_two_raw = c.fetchall()
    conn.close()
    return first_two, list(reversed(last_two_raw))

def get_db_stats():
    conn = sqlite3.connect('predictions.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM rounds")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM rounds WHERE result='WIN'")
    wins = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM rounds WHERE result='LOSS'")
    losses = c.fetchone()[0]
    conn.close()
    return total, wins, losses

init_db()

# ═══════════════════ HTTP HELPERS ═══════════════════
def http_get_json(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode('utf-8'))
    except: return None

def http_post_json(url, payload, timeout=10):
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode('utf-8')
    except: return None

# ═══════════════════ UI FORMATTERS ═══════════════════
def format_prediction_ui(pred_data, period):
    size = pred_data["size"]; conf = pred_data["confidence"]; rng = pred_data["range"]
    ma = pred_data.get("ma","BULLISH"); rsi = pred_data.get("rsi",63.8); std = pred_data.get("std","LOW")
    pattern = pred_data.get("pattern","ALTERNATING"); cycle = pred_data.get("cycle","STABLE")
    big_pct = pred_data.get("big_pct",78); small_pct = pred_data.get("small_pct",22)
    signal = "HIGH 🟢" if conf>=85 else "MEDIUM 🟡"
    big_bar = "█"*int(big_pct/10)+"░"*(10-int(big_pct/10))
    small_bar = "█"*int(small_pct/10)+"░"*(10-int(small_pct/10))
    pattern_short = pattern[:3].upper() if pattern else "---"
    ui = f"""
╭━━━ ⚡ PREDICTOR AI ⚡ ━━━╮
┃ 🎯 NEXT PREDICTION
┃ 🆔 {period}
┃ (🧠+🫀)FINAL PREDICTION  {size}
┃ 🔢 NUMBER : {rng}
┣━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ 📈 Trend : {ma}
┃ 📊 RSI   : {rsi:.1f}
┃ 📉 Vol.  : {std}
┃ 🔄 Ptrn. : {pattern_short}
┃ 🎯 Cycle : {cycle}
┣━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ 🧠BIG    {big_bar} {big_pct}%
┃ 🫀 SMALL  {small_bar} {small_pct}%
┣━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ 🎯 Conf : {conf}%
┃ 📶 Signal : {signal}
┣━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ ⚡ ACTIVE • LIVE
┃ 🧠 PREDICTOR AI
╰━━━━━━━━━━━━━━━━━━━━━━━━━╯
"""
    return ui

def format_result_ui(period, number, actual_size, result, pred, range_pred):
    if result == "WIN":
        status_emoji = "✅"; status_text = "WIN 🎉"; bg = "🟢"; jackpot_line = "🎰 JACKPOT! 🥳"
    else:
        status_emoji = "❌"; status_text = "LOSS 😞"; bg = "🔴"; jackpot_line = "😔 NEXT TIME"
    actual_emoji = "🐘" if actual_size == "BIG" else "🐭"
    ui = f"""
╭━━━ {status_emoji} RESULT ━━━╮
┃ {status_emoji} {status_text}  {bg}
┃ {jackpot_line}
┣━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ 📅 PERIOD    : {period}
┃ 🎯 PREDICT   : {pred}
┃ ✅ ACTUAL    : {actual_emoji} {actual_size} [{number}]
┃ 📊 RANGE     : {range_pred}
╰━━━━━━━━━━━━━━━━━━━━━━━━━╯
"""
    return ui

def format_profile(user_info):
    name = user_info.get('Name','')
    username = user_info.get('Username','')
    uid = user_info.get('UID','')
    tid = user_info.get('Telegram ID','')
    exp_raw = user_info.get('Expired (Date and Time)','')
    fmts = ["%Y-%m-%d %H:%M:%S", "%m/%d/%Y %H:%M:%S", "%d/%m/%Y %H:%M:%S"]
    exp_formatted = exp_raw
    for f in fmts:
        try:
            dt = datetime.strptime(exp_raw, f)
            exp_formatted = dt.strftime("%d/%m/%Y %H:%M:%S")
            break
        except:
            pass
    return f"""Profile 😇
━━━━━━━━━━━━━━━━━━━━━━
Name        : {name}
Username    : @{username}
ID          : {tid}
UID         : {uid}
Expired     : {exp_formatted}
━━━━━━━━━━━━━━━━━━━━━━"""

def format_first_last_ui(first_two, last_two):
    total, wins, losses = get_db_stats()
    text = f"Database Records 💀\nTotal Rounds: {total} | Wins: {wins} | Losses: {losses}\n"
    text += "━━━━━━━━━━━━━━━━\n🔹 First 2:\n"
    for row in first_two:
        text += f"✨ {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]}\n\n"
    text += "🔸 Last 2:\n"
    for row in last_two:
        text += f"✨ {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]}\n\n"
    text += "━━━━━━━━━━━━━━━━"
    return text

def format_user_list_ui():
    with sheet_lock:
        users = list(sheet_data_cache)
    total = len(users)
    active = deactive = 0
    lines = []
    for u in users:
        status, _ = get_user_info(u['telegram_id'])
        if status == 'active':
            active += 1
            icon = "🟢"
        else:
            deactive += 1
            icon = "🔴"
        name = u.get('Name','')
        username = u.get('Username','')
        uid = u.get('UID','')
        tid = u.get('Telegram ID','')
        exp = u.get('Expired (Date and Time)','')
        lines.append(f"{icon} {name} | @{username} | ID:{tid} | UID:{uid} | Exp: {exp}")
    header = f"👥 User List\n━━━━━━━━━━━━━━━━\n📊 Total: {total} | 🟢 Active: {active} | 🔴 Deactive: {deactive}\n━━━━━━━━━━━━━━━━\n"
    if lines:
        return header + "\n\n".join(lines)
    else:
        return header + "No users found."

# ═══════════════════ PREDICTOR CLASS ═══════════════════
class Predictor:
    def __init__(self, chat_id, user_id):
        self.chat_id = chat_id
        self.user_id = user_id
        self.history = deque(maxlen=300)
        self.wins = self.losses = self.streak = self.best_streak = self.total_predictions = 0
        self.running = False
        self.expiry_timer = None
        self.load_from_db()

    def load_from_db(self):
        for _, num, _, _, _, _ in load_recent_history(300):
            if num is not None: self.history.append(num)

    def update(self, num, period, prediction=None, result=None, range_pred=None):
        size = "BIG" if num >= 5 else "SMALL"
        self.history.append(num)
        save_round(period, num, size, prediction, result, range_pred)

    def fetch_data(self):
        try:
            data = http_get_json(API_URL.format(int(time.time()*1000)))
            return data.get("data",{}).get("list",[]) if data else []
        except: return []

    # ---------- Indicators ----------
    def ma(self, d, w): return sum(d[-w:])/w if len(d)>=w else (sum(d)/len(d) if d else 0)
    def rsi(self, d, w=14):
        if len(d)<w+1: return 50
        g=l=0
        for i in range(1,w+1):
            diff = d[-i]-d[-i-1]
            if diff>0: g+=diff
            else: l+=abs(diff)
        return 100 if l==0 else 100 - (100/(1+(g/l)))
    def std_dev(self, d, w=20):
        if len(d)<w: return 0
        arr = d[-w:]; mean = sum(arr)/w
        return math.sqrt(sum((x-mean)**2 for x in arr)/w)

    def predict_size(self):
        hist = list(self.history)
        if len(hist)<20:
            return "BIG",60,"5 • 9","BULLISH",50,"LOW","NEUTRAL","STABLE",50,50
        last = hist[-1]; last_size = "BIG" if last>=5 else "SMALL"
        specials = {0:("SMALL",99,"0 • 2"),4:("SMALL",99,"3 • 5"),
                    5:("BIG",99,"5 • 7"),9:("SMALL",99,"7 • 9")}
        if last in specials:
            s = specials[last]; return s[0],s[1],s[2],"BULLISH",70,"LOW","SPECIAL","STABLE",90,10

        streak=1
        for i in range(len(hist)-2,-1,-1):
            if (hist[i]>=5)==(last>=5): streak+=1
            else: break
        def is_alt(l):
            if len(hist)<l: return False
            for i in range(1,l):
                if (hist[-i]>=5)==(hist[-i-1]>=5): return False
            return True
        def get_range(ptype):
            recent=hist[-20:]
            nums=[x for x in recent if (x>=5)==(ptype=="BIG")]
            if len(nums)>=2:
                top=Counter(nums).most_common(2)
                return f"{top[0][0]} • {top[1][0]}"
            return "5 • 9" if ptype=="BIG" else "0 • 4"

        if streak>=5: pred=last_size; conf=98; rng=get_range(pred)
        elif streak==4: pred=last_size; conf=95; rng=get_range(pred)
        elif streak==3: pred="SMALL" if last_size=="BIG" else "BIG"; conf=92; rng=get_range(pred)
        elif streak==2: pred="SMALL" if last_size=="BIG" else "BIG"; conf=88; rng=get_range(pred)
        elif is_alt(8): pred="SMALL" if last_size=="BIG" else "BIG"; conf=93; rng=get_range(pred)
        elif is_alt(6): pred="SMALL" if last_size=="BIG" else "BIG"; conf=90; rng=get_range(pred)
        elif is_alt(5): pred=last_size; conf=87; rng=get_range(pred)
        else:
            ma5,ma10,ma20 = self.ma(hist,5),self.ma(hist,10),self.ma(hist,20)
            ma_trend="BULLISH" if ma5>ma10>ma20 else "BEARISH" if ma5<ma10<ma20 else "NEUTRAL"
            rsi_val=self.rsi(hist,14)
            rsi_trend="BULLISH" if rsi_val<30 else "BEARISH" if rsi_val>70 else "NEUTRAL"
            recent_30=hist[-30:] if len(hist)>=30 else hist
            big_c=sum(1 for x in recent_30 if x>=5); small_c=len(recent_30)-big_c
            std=self.std_dev(hist,20); std_text="LOW" if std<1.5 else "MEDIUM" if std<2.5 else "HIGH"
            votes={"BIG":0,"SMALL":0}
            votes["SMALL" if last_size=="BIG" else "BIG"]+=1
            if ma_trend=="BULLISH": votes["BIG"]+=3
            elif ma_trend=="BEARISH": votes["SMALL"]+=3
            if rsi_trend=="BULLISH": votes["BIG"]+=2
            elif rsi_trend=="BEARISH": votes["SMALL"]+=2
            if big_c>small_c+3: votes["SMALL"]+=2
            elif small_c>big_c+3: votes["BIG"]+=2
            pred=max(votes,key=votes.get); total=sum(votes.values())
            diff=votes[pred]-(total-votes[pred])
            conf=92 if diff>=4 else 85 if diff>=2 else 75
            big_pct=int(votes["BIG"]/total*100) if total else 50
            small_pct=int(votes["SMALL"]/total*100) if total else 50
            pattern_text="ALTERNATING" if is_alt(4) else "RANDOM"; cycle_text="STABLE" if std<1.5 else "UNSTABLE"
            rng=get_range(pred)
            return pred,conf,rng,ma_trend,rsi_val,std_text,pattern_text,cycle_text,big_pct,small_pct

        if streak>=5: extra = ("STRONG BULLISH",72,"LOW","DRAGON","STABLE",95,5)
        elif streak==4: extra = ("BULLISH",68,"LOW","4-STREAK","STABLE",90,10)
        elif streak==3: extra = ("BEARISH",55,"MEDIUM","3-STREAK BREAK","UNSTABLE",75,25)
        elif streak==2: extra = ("NEUTRAL",52,"MEDIUM","2-STREAK BREAK","STABLE",70,30)
        elif is_alt(8): extra = ("BULLISH",65,"LOW","ALTERNATING 8","STABLE",85,15)
        elif is_alt(6): extra = ("BULLISH",60,"LOW","ALTERNATING 6","STABLE",80,20)
        elif is_alt(5): extra = ("NEUTRAL",55,"MEDIUM","TRAP","STABLE",72,28)
        else: extra = ("NEUTRAL",50,"LOW","NEUTRAL","STABLE",50,50)
        return pred,conf,rng,extra[0],extra[1],extra[2],extra[3],extra[4],extra[5],extra[6]

    def get_next_prediction(self):
        size,conf,rng,ma,rsi,std,pattern,cycle,big_pct,small_pct = self.predict_size()
        return {"size":size,"confidence":conf,"range":rng,"ma":ma,"rsi":rsi,"std":std,
                "pattern":pattern,"cycle":cycle,"big_pct":big_pct,"small_pct":small_pct}

    def update_result(self, won):
        if won: self.wins+=1; self.streak+=1; self.best_streak=max(self.best_streak,self.streak)
        else: self.losses+=1; self.streak=0
        self.total_predictions+=1

    def send_message(self, text, parse_mode="Markdown"):
        if self.chat_id:
            try: http_post_json(TELEGRAM_API+"sendMessage",{"chat_id":self.chat_id,"text":text,"parse_mode":parse_mode})
            except: pass

    def start_loop(self):
        if self.running: return
        self.running = True
        _, info = get_user_info(self.user_id)
        if info:
            exp_str = info.get('Expired (Date and Time)','').strip()
            fmts = ["%Y-%m-%d %H:%M:%S", "%m/%d/%Y %H:%M:%S", "%d/%m/%Y %H:%M:%S"]
            for f in fmts:
                try:
                    exp_dt = datetime.strptime(exp_str, f)
                    exp_dt = exp_dt.replace(tzinfo=IST)
                    delay = (exp_dt - datetime.now(IST)).total_seconds()
                    if delay > 0:
                        self.expiry_timer = threading.Timer(delay, self._auto_stop)
                        self.expiry_timer.daemon = True
                        self.expiry_timer.start()
                    elif delay <= 0:
                        self._auto_stop()
                        return
                    break
                except: pass
        threading.Thread(target=self._loop, daemon=True).start()

    def _auto_stop(self):
        if self.running:
            self.running = False
            self.send_message("Stopped.")

    def stop_loop(self):
        if self.expiry_timer:
            self.expiry_timer.cancel()
        self.running = False

    def _loop(self):
        seen = set()
        current_prediction = None
        while self.running:
            status, _ = get_user_info(self.user_id)
            if status != 'active':
                self._auto_stop()
                break
            try:
                data = self.fetch_data()
                if not data: time.sleep(1); continue
                latest = data[0]; period = latest.get("issueNumber","")
                try: number = int(latest.get("number",""))
                except: number = None
                if not period or not period.isdigit(): time.sleep(1); continue

                # ---------- RESULT CHECK FIRST ----------
                if current_prediction and current_prediction["period"] == period and number is not None:
                    actual_size = "BIG" if number >= 5 else "SMALL"
                    won = (actual_size == current_prediction["size"])
                    res = "WIN" if won else "LOSS"
                    self.update_result(won)
                    self.update(number, period,
                                prediction=current_prediction["size"],
                                result=res,
                                range_pred=current_prediction["range"])
                    self.send_message(format_result_ui(period, number, actual_size, res,
                                                       current_prediction["size"],
                                                       current_prediction["range"]))
                    current_prediction = None

                # ---------- NEW PERIOD ----------
                if period not in seen:
                    if number is not None:
                        self.update(number, period)
                    seen.add(period)

                    next_period = str(int(period) + 1)
                    pred_data = self.get_next_prediction()
                    if pred_data["confidence"] >= 85:
                        current_prediction = {
                            "period": next_period,
                            "size": pred_data["size"],
                            "range": pred_data["range"]
                        }
                        self.send_message(format_prediction_ui(pred_data, next_period))

                time.sleep(1)
            except Exception as e:
                print("Loop error:", e); time.sleep(2)

# ═══════════════════ BOT HANDLERS ═══════════════════
predictors = {}
last_update_id = 0

def get_updates(offset=None):
    url = TELEGRAM_API + "getUpdates"
    params = {"timeout":30}
    if offset: params["offset"] = offset
    try:
        full_url = url + "?" + urllib.parse.urlencode(params)
        data = http_get_json(full_url, timeout=35)
        return data.get("result",[]) if data else []
    except: return []

def send_unauthorized(chat_id):
    http_post_json(TELEGRAM_API+"sendMessage", {
        "chat_id": chat_id,
        "text": "🚫 You are not authorized!",
        "parse_mode": "Markdown"
    })

def send_deactive(chat_id):
    keyboard = {
        "inline_keyboard": [
            [{"text": "Active", "url": f"https://t.me/{ADMIN_USERNAME}"}]
        ]
    }
    http_post_json(TELEGRAM_API+"sendMessage", {
        "chat_id": chat_id,
        "text": "⛔ Your account has been deactivated.",
        "reply_markup": keyboard,
        "parse_mode": "Markdown"
    })

def is_user_active(user_id):
    return get_user_status(user_id) == 'active'

def process_message(chat_id, user_id, text):
    if not is_user_active(user_id):
        status = get_user_status(user_id)
        if status == 'not_found':
            send_unauthorized(chat_id)
        else:
            send_deactive(chat_id)
        return

    if text == "/start":
        _, info = get_user_info(user_id)
        name = info.get("Name","User") if info else "User"
        is_admin = user_id in ADMIN_USER_IDS
        buttons = [
            [{"text":"START","callback_data":"start"}],
            [{"text":"STOP","callback_data":"stop"}],
            [{"text":"STATUS","callback_data":"status"}],
            [{"text":"PROFILE","callback_data":"profile"}]
        ]
        if is_admin:
            buttons.append([{"text":"USER LIST","callback_data":"user_list"},
                            {"text":"SHOW DATA","callback_data":"show_data"}])
        else:
            buttons.append([{"text":"CONTACT","url":"https://t.me/your_username"}])
        http_post_json(TELEGRAM_API+"sendMessage",{
            "chat_id":chat_id,
            "text":f"Predictor v1.0.0\nWelcome {name} 😈\n\nUse buttons below.",
            "reply_markup":{"inline_keyboard":buttons},
            "parse_mode":"Markdown"
        })

    elif text == "/stop":
        if chat_id in predictors:
            predictors[chat_id].stop_loop()
            http_post_json(TELEGRAM_API+"sendMessage",{"chat_id":chat_id,"text":"Stopped.","parse_mode":"Markdown"})
        else:
            http_post_json(TELEGRAM_API+"sendMessage",{"chat_id":chat_id,"text":"No active prediction.","parse_mode":"Markdown"})

    elif text == "/status":
        if chat_id in predictors:
            pred = predictors[chat_id]
            _, info = get_user_info(user_id)
            name = info.get('Name','User') if info else 'User'
            stats = (f"{name} 😎\n"
                     f"🤑 Wins: {pred.wins}\n"
                     f"😱 Losses: {pred.losses}\n"
                     f"🔥 Streak: {pred.streak}\n"
                     f"🤩 Best Streak: {pred.best_streak}\n"
                     f"🤯 Total: {pred.total_predictions}")
            http_post_json(TELEGRAM_API+"sendMessage",{"chat_id":chat_id,"text":stats,"parse_mode":"Markdown"})
        else:
            http_post_json(TELEGRAM_API+"sendMessage",{"chat_id":chat_id,"text":"No statistics yet.","parse_mode":"Markdown"})

    elif text == "/profile":
        _, info = get_user_info(user_id)
        if info:
            http_post_json(TELEGRAM_API+"sendMessage",{"chat_id":chat_id,"text":format_profile(info),"parse_mode":"Markdown"})
        else:
            http_post_json(TELEGRAM_API+"sendMessage",{"chat_id":chat_id,"text":"Profile not found.","parse_mode":"Markdown"})

    elif text == "/show_data":
        if user_id not in ADMIN_USER_IDS:
            http_post_json(TELEGRAM_API+"sendMessage",{"chat_id":chat_id,"text":"Admin only.","parse_mode":"Markdown"})
            return
        first, last = get_first_and_last()
        if not first and not last:
            resp = "No data collected yet."
        else:
            resp = format_first_last_ui(first, last)
        http_post_json(TELEGRAM_API+"sendMessage",{"chat_id":chat_id,"text":resp,"parse_mode":"Markdown"})

    elif text == "/userlist":
        if user_id not in ADMIN_USER_IDS:
            http_post_json(TELEGRAM_API+"sendMessage",{"chat_id":chat_id,"text":"Admin only.","parse_mode":"Markdown"})
            return
        user_list_msg = format_user_list_ui()
        http_post_json(TELEGRAM_API+"sendMessage",{"chat_id":chat_id,"text":user_list_msg})   # plain text

def process_callback(chat_id, user_id, data):
    status = get_user_status(user_id)
    if status != 'active':
        if status == 'not_found':
            send_unauthorized(chat_id)
        else:
            send_deactive(chat_id)
        return

    if chat_id not in predictors:
        predictors[chat_id] = Predictor(chat_id, user_id)
    pred = predictors[chat_id]

    if data == "start":
        if not pred.running:
            pred.start_loop()
            pred.send_message("Let's Goo...")
        else:
            pred.send_message("Prediction...")
    elif data == "stop":
        pred.stop_loop()
        pred.send_message("Stopped.")
    elif data == "status":
        _, info = get_user_info(user_id)
        name = info.get('Name','User') if info else 'User'
        stats = (f"{name} 😎\n"
                 f"🤑 Wins: {pred.wins}\n"
                 f"😱 Losses: {pred.losses}\n"
                 f"🔥 Streak: {pred.streak}\n"
                 f"🤩 Best Streak: {pred.best_streak}\n"
                 f"🤯 Total: {pred.total_predictions}")
        pred.send_message(stats)
    elif data == "profile":
        _, info = get_user_info(user_id)
        if info:
            pred.send_message(format_profile(info))
        else:
            pred.send_message("Profile not found.")
    elif data == "show_data":
        if user_id not in ADMIN_USER_IDS:
            pred.send_message("Admin only.")
            return
        first, last = get_first_and_last()
        if not first and not last:
            resp = "No data collected yet."
        else:
            resp = format_first_last_ui(first, last)
        pred.send_message(resp)
    elif data == "user_list":
        if user_id not in ADMIN_USER_IDS:
            pred.send_message("Admin only.")
            return
        user_list_msg = format_user_list_ui()
        pred.send_message(user_list_msg, parse_mode="")   # plain text

def main():
    global last_update_id
    print("Bot started with IST time, result before prediction, and fixed UI spacing.")
    while True:
        try:
            updates = get_updates(last_update_id+1 if last_update_id else None)
            for upd in updates:
                last_update_id = upd["update_id"]
                if "message" in upd:
                    msg = upd["message"]; chat_id=msg["chat"]["id"]; user_id=msg["from"]["id"]
                    text = msg.get("text","")
                    if text.startswith("/"):
                        process_message(chat_id, user_id, text)
                elif "callback_query" in upd:
                    cb = upd["callback_query"]; chat_id=cb["message"]["chat"]["id"]; user_id=cb["from"]["id"]
                    http_post_json(TELEGRAM_API+"answerCallbackQuery",{"callback_query_id":cb["id"]})
                    process_callback(chat_id, user_id, cb["data"])
            time.sleep(1)
        except Exception as e:
            print("Main error:", e); time.sleep(5)

if __name__ == "__main__":
    keep_alive()  # Start Flask health-check server in background
    main()        # Start Telegram bot polling in main thread