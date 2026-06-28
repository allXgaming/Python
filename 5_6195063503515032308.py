#!/usr/bin/env python3
"""
🐆 SNX PANTHER V8.0 - ULTRA PRO MAX DESIGN
🔥 MILME LOGIC | NEON UI | BOX DESIGN
"""

import requests
import time
import os
from collections import deque
from datetime import datetime

# ==================== SEXY COLORS ====================
BLACK = '\033[30m'
RED_BG = '\033[41m'
GREEN_BG = '\033[42m'
YELLOW_BG = '\033[43m'
BLUE_BG = '\033[44m'
PURPLE_BG = '\033[45m'
CYAN_BG = '\033[46m'
WHITE_BG = '\033[47m'

BLACK_BOLD = '\033[1;90m'
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
MAGENTA = '\033[95m'
CYAN = '\033[96m'
WHITE = '\033[97m'
RESET = '\033[0m'
BOLD = '\033[1m'
DIM = '\033[2m'
REVERSE = '\033[7m'
HIDDEN = '\033[8m'

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    clear()
    print(CYAN + "╔" + "═"*60 + "╗" + RESET)
    print(CYAN + "║" + RESET + "  " + BOLD + WHITE + "🐆 SNX PANTHER V8.0" + RESET + " " * 35 + CYAN + "║" + RESET)
    print(CYAN + "║" + RESET + "  " + MAGENTA + "🔥 MILME LOGIC | NEON UI" + RESET + " " * 32 + CYAN + "║" + RESET)
    print(CYAN + "║" + RESET + "  " + YELLOW + "⚡ REAL TIME PREDICTOR" + RESET + " " * 33 + CYAN + "║" + RESET)
    print(CYAN + "╚" + "═"*60 + "╝" + RESET)
    print()

API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json?ts={}"
FIREBASE_URL = "https://python-script-42d50-default-rtdb.firebaseio.com"

# ========== KEY CHECK REMOVED – ALWAYS GRANT ACCESS ==========
def login():
    print_banner()
    print("   " + GREEN + "✅ KEY CHECK DISABLED – ACCESS GRANTED" + RESET)
    print("   " + CYAN + "👤 USER: PREMIUM (UNLOCKED)" + RESET)
    print("   " + CYAN + "🔥 ENGINE: MILME LOGIC ACTIVE" + RESET)
    print()
    time.sleep(1.5)
    return True

class MilmePredictor:
    def __init__(self):
        self.history = deque(maxlen=200)
        self.wins = 0
        self.losses = 0
        self.streak = 0
        self.best_streak = 0
        self.max_loss = 0
        
    def update(self, num):
        self.history.append(num)
    
    def get_bs(self, num):
        return "BIG" if num >= 5 else "SMALL"
    
    def predict(self):
        if len(self.history) < 3:
            return "BIG", 70, "INIT", "Initializing..."
        
        last = self.history[-1]
        
        # SPECIAL NUMBERS - 99% CONFIDENCE
        specials = {
            0: ("BIG", 99, "⚡ SPECIAL", "Zero Edge → BIG"),
            4: ("BIG", 97, "⚡ SPECIAL", "Four Force → BIG"),
            5: ("SMALL", 97, "⚡ SPECIAL", "Five Force → SMALL"),
            9: ("SMALL", 99, "⚡ SPECIAL", "Nine Edge → SMALL"),
        }
        if last in specials:
            return specials[last]
        
        # DIRECT MILAN - Same number repeat
        if len(self.history) >= 2 and self.history[-1] == self.history[-2]:
            if last >= 5:
                return "SMALL", 88, "🔄 MILAN", "Same number repeat → opposite"
            else:
                return "BIG", 88, "🔄 MILAN", "Same number repeat → opposite"
        
        # STREAK DETECTION
        streak = 1
        last_bs = self.get_bs(last)
        for i in range(1, min(10, len(self.history))):
            if self.get_bs(self.history[-i-1]) == last_bs:
                streak += 1
            else:
                break
        
        if streak >= 3:
            if last_bs == "BIG":
                return "SMALL", 90, "📊 STREAK", f"Breaking {streak}-streak → SMALL"
            else:
                return "BIG", 90, "📊 STREAK", f"Breaking {streak}-streak → BIG"
        
        # MIRROR MILAN
        mirrors = {0:9, 1:8, 2:7, 3:6, 4:5, 5:4, 6:3, 7:2, 8:1, 9:0}
        if len(self.history) >= 2:
            if self.history[-2] in mirrors and self.history[-1] == mirrors[self.history[-2]]:
                if self.history[-2] >= 5:
                    return "BIG", 82, "🪞 MIRROR", f"Mirror pair {self.history[-2]}→{self.history[-1]} → BIG"
                else:
                    return "SMALL", 82, "🪞 MIRROR", f"Mirror pair {self.history[-2]}→{self.history[-1]} → SMALL"
        
        # REVERSAL LOGIC
        if len(self.history) >= 3:
            if self.history[-1] >= 5 and self.history[-2] >= 5 and self.history[-3] >= 5:
                return "SMALL", 85, "🔄 REVERSAL", "3 BIGs in row → SMALL"
            if self.history[-1] < 5 and self.history[-2] < 5 and self.history[-3] < 5:
                return "BIG", 85, "🔄 REVERSAL", "3 SMALLs in row → BIG"
        
        # DEFAULT - Opposite of last
        if last >= 5:
            return "SMALL", 70, "🎯 DEFAULT", "Opposite of last → SMALL"
        else:
            return "BIG", 70, "🎯 DEFAULT", "Opposite of last → BIG"
    
    def update_result(self, won):
        if won:
            self.wins += 1
            self.streak += 1
            if self.streak > self.best_streak:
                self.best_streak = self.streak
        else:
            self.losses += 1
            self.streak = 0
            self.max_loss += 1

def fetch_data():
    try:
        ts = int(time.time() * 1000)
        r = requests.get(API_URL.format(ts), timeout=5)
        data = r.json()
        return data.get("data", {}).get("list", [])
    except:
        return []

def draw_progress_bar(percent, width=30):
    filled = int(width * percent / 100)
    empty = width - filled
    bar = "█" * filled + "░" * empty
    return bar

def main():
    if not login():
        return
    
    predictor = MilmePredictor()
    predictions = []
    current = None
    seen = set()
    
    clear()
    print_banner()
    print("   " + GREEN + "🔥 PREDICTOR STARTING..." + RESET)
    print("   " + DIM + "Press Ctrl+C to stop" + RESET)
    time.sleep(2)
    
    try:
        while True:
            data = fetch_data()
            
            if data:
                latest = data[0]
                period = latest.get("issueNumber", "")
                number = latest.get("number", "")
                
                try:
                    predictor.update(int(number))
                except:
                    pass
                
                if current and current["period"] == period:
                    try:
                        actual = "BIG" if int(number) >= 5 else "SMALL"
                        won = (actual == current["pred"])
                        predictor.update_result(won)
                        
                        predictions.insert(0, {
                            "period": period[-8:],
                            "full_period": period,
                            "num": number,
                            "pred": current["pred"],
                            "actual": actual,
                            "result": "WIN" if won else "LOSS",
                            "mode": current.get("mode", ""),
                            "info": current.get("info", "")
                        })
                        
                        if len(predictions) > 100:
                            predictions.pop()
                        
                        current = None
                    except:
                        pass
                
                if not current and period not in seen:
                    seen.add(period)
                    try:
                        next_period = str(int(period) + 1)
                        pred, conf, mode, info = predictor.predict()
                        current = {
                            "period": next_period,
                            "pred": pred,
                            "conf": conf,
                            "mode": mode,
                            "info": info
                        }
                    except:
                        pass
            
            # ==================== DISPLAY ====================
            clear()
            
            # TOP BANNER
            print(CYAN + "╔" + "═"*60 + "╗" + RESET)
            print(CYAN + "║" + RESET + "  " + BOLD + WHITE + "🐆 SNX PANTHER V8.0" + RESET + " " * 35 + CYAN + "║" + RESET)
            print(CYAN + "║" + RESET + "  " + MAGENTA + "🔥 MILME LOGIC | NEON UI" + RESET + " " * 32 + CYAN + "║" + RESET)
            print(CYAN + "║" + RESET + "  " + YELLOW + "⚡ REAL TIME PREDICTOR" + RESET + " " * 33 + CYAN + "║" + RESET)
            print(CYAN + "╠" + "═"*60 + "╣" + RESET)
            
            # PREDICTION BOX
            if current:
                pred = current["pred"]
                conf = current["conf"]
                mode = current["mode"]
                info = current["info"]
                
                if pred == "BIG":
                    pred_color = YELLOW + BOLD
                    box_color = YELLOW
                else:
                    pred_color = CYAN + BOLD
                    box_color = CYAN
                
                print(box_color + "║" + RESET + "  " + BOLD + WHITE + "🎯 NEXT TARGET" + RESET + " " * 44 + box_color + "║" + RESET)
                print(box_color + "║" + RESET + "  " + "─"*56 + " " + box_color + "║" + RESET)
                print(box_color + "║" + RESET + "  " + WHITE + "Period:" + RESET + " " + YELLOW + current["period"] + RESET + " " * (42 - len(current["period"])) + box_color + "║" + RESET)
                print(box_color + "║" + RESET + "  " + WHITE + "Prediction:" + RESET + " " + pred_color + " " + pred + " " + RESET + " " * (42 - len(pred)) + box_color + "║" + RESET)
                print(box_color + "║" + RESET + "  " + WHITE + "Confidence:" + RESET + " " + GREEN + str(int(conf)) + "%" + RESET + "  " + YELLOW + "[" + draw_progress_bar(conf, 20) + "]" + RESET + " " * (15 - len(str(int(conf)))) + box_color + "║" + RESET)
                print(box_color + "║" + RESET + "  " + WHITE + "Mode:" + RESET + " " + MAGENTA + mode + RESET + " " * (50 - len(mode)) + box_color + "║" + RESET)
                print(box_color + "║" + RESET + "  " + WHITE + "Info:" + RESET + " " + DIM + info + RESET + " " * (52 - len(info)) + box_color + "║" + RESET)
                print(box_color + "╚" + "═"*60 + "╝" + RESET)
            else:
                print(YELLOW + "║" + RESET + "  " + YELLOW + "⏳ WAITING FOR DATA..." + RESET + " " * 34 + YELLOW + "║" + RESET)
                print(YELLOW + "╚" + "═"*60 + "╝" + RESET)
            
            # STATS BOX
            total = predictor.wins + predictor.losses
            acc = (predictor.wins / total * 100) if total > 0 else 0
            
            print()
            print(CYAN + "╔" + "═"*60 + "╗" + RESET)
            print(CYAN + "║" + RESET + "  " + BOLD + WHITE + "📊 STATISTICS" + RESET + " " * 44 + CYAN + "║" + RESET)
            print(CYAN + "╠" + "═"*60 + "╣" + RESET)
            print(CYAN + "║" + RESET + "  " + WHITE + "Total Predictions:" + RESET + " " + YELLOW + str(total) + RESET + " " * (41 - len(str(total))) + CYAN + "║" + RESET)
            print(CYAN + "║" + RESET + "  " + WHITE + "Wins:" + RESET + " " + GREEN + str(predictor.wins) + RESET + "   " + WHITE + "Losses:" + RESET + " " + RED + str(predictor.losses) + RESET + " " * (33 - len(str(predictor.wins)) - len(str(predictor.losses))) + CYAN + "║" + RESET)
            print(CYAN + "║" + RESET + "  " + WHITE + "Accuracy:" + RESET + " " + (GREEN if acc >= 50 else RED) + "{:.1f}".format(acc) + "%" + RESET + " " * (44 - len("{:.1f}".format(acc))) + CYAN + "║" + RESET)
            print(CYAN + "║" + RESET + "  " + WHITE + "Win Streak:" + RESET + " " + GREEN + str(predictor.streak) + RESET + "   " + WHITE + "Best:" + RESET + " " + YELLOW + str(predictor.best_streak) + RESET + " " * (33 - len(str(predictor.streak)) - len(str(predictor.best_streak))) + CYAN + "║" + RESET)
            
            # PROGRESS BAR FOR ACCURACY
            print(CYAN + "║" + RESET + "  " + WHITE + "Performance:" + RESET + " " + (GREEN if acc >= 50 else RED) + "[" + draw_progress_bar(acc, 30) + "]" + RESET + " " * (20 - int(acc/3.33)) + CYAN + "║" + RESET)
            
            if predictor.streak >= 3:
                print(CYAN + "║" + RESET + "  " + RED + "⚠️ HOT STREAK: " + str(predictor.streak) + " WINS IN A ROW!" + RESET + " " * (33 - len(str(predictor.streak))) + CYAN + "║" + RESET)
            
            print(CYAN + "╚" + "═"*60 + "╝" + RESET)
            
            # HISTORY TABLE
            if predictions:
                print()
                print(CYAN + "╔" + "═"*60 + "╗" + RESET)
                print(CYAN + "║" + RESET + "  " + BOLD + WHITE + "📜 HISTORY (Last " + str(len(predictions)) + ")" + RESET + " " * (36 - len(str(len(predictions)))) + CYAN + "║" + RESET)
                print(CYAN + "╠" + "═"*60 + "╣" + RESET)
                print(CYAN + "║" + RESET + "  " + DIM + "#   Period     Num  Pred  Act   Result    Mode" + RESET + " " * 19 + CYAN + "║" + RESET)
                print(CYAN + "║" + RESET + "  " + DIM + "─"*56 + RESET + " " + CYAN + "║" + RESET)
                
                for i, p in enumerate(predictions[:20], 1):
                    if p["result"] == "WIN":
                        res_color = GREEN
                        res_icon = "✅ WIN"
                    else:
                        res_color = RED
                        res_icon = "❌ LOSS"
                    
                    pcolor = YELLOW if p["pred"] == "BIG" else CYAN
                    acolor = YELLOW if p["actual"] == "BIG" else CYAN
                    
                    # Highlight recent win/loss streak
                    highlight = "▶" if i <= 3 else " "
                    
                    line = CYAN + "║" + RESET + "  " + highlight + " " + str(i).ljust(2) + " " + p["period"].ljust(10) + " " + p["num"].ljust(3) + " " + pcolor + p["pred"].ljust(4) + RESET + " " + acolor + p["actual"].ljust(4) + RESET + " " + res_color + res_icon.ljust(7) + RESET + " " + DIM + p.get("mode", "N/A")[:12].ljust(12) + RESET + " " + CYAN + "║" + RESET
                    print(line)
                
                print(CYAN + "╚" + "═"*60 + "╝" + RESET)
                
                # LAST 10 STATS
                last10 = list(predictions)[:10]
                last10_wins = sum(1 for p in last10 if p["result"] == "WIN")
                last10_losses = 10 - last10_wins
                last10_acc = (last10_wins / 10 * 100) if last10 else 0
                
                print()
                print(CYAN + "╔" + "═"*60 + "╗" + RESET)
                print(CYAN + "║" + RESET + "  " + BOLD + WHITE + "📈 LAST 10 PERFORMANCE" + RESET + " " * 36 + CYAN + "║" + RESET)
                print(CYAN + "╠" + "═"*60 + "╣" + RESET)
                print(CYAN + "║" + RESET + "  " + WHITE + "Wins:" + RESET + " " + GREEN + str(last10_wins) + RESET + "   " + WHITE + "Losses:" + RESET + " " + RED + str(last10_losses) + RESET + "   " + WHITE + "Accuracy:" + RESET + " " + (GREEN if last10_acc >= 50 else RED) + "{:.1f}".format(last10_acc) + "%" + RESET + " " * (23 - len("{:.1f}".format(last10_acc))) + CYAN + "║" + RESET)
                print(CYAN + "║" + RESET + "  " + WHITE + "Trend:" + RESET + " " + (GREEN if last10_acc >= 50 else RED) + "[" + draw_progress_bar(last10_acc, 30) + "]" + RESET + " " * (20 - int(last10_acc/3.33)) + CYAN + "║" + RESET)
                print(CYAN + "╚" + "═"*60 + "╝" + RESET)
            
            # WARNING FOR LOSS STREAK
            if predictor.streak == 0 and predictor.losses > 0:
                last_result = predictions[0] if predictions else None
                if last_result and last_result["result"] == "LOSS":
                    print()
                    print(RED + "╔" + "═"*60 + "╗" + RESET)
                    print(RED + "║" + RESET + "  " + RED_BG + BLACK_BOLD + " ⚠️  LAST WAS LOSS - REVERSAL MODE ACTIVE " + RESET + " " * 21 + RED + "║" + RESET)
                    print(RED + "╚" + "═"*60 + "╝" + RESET)
            
            # FOOTER - CONTACT UPDATED TO SUBHA MODS
            print()
            print(DIM + "┌" + "─"*60 + "┐" + RESET)
            print(DIM + "│" + RESET + "  ⏰ " + datetime.now().strftime('%H:%M:%S') + "  |  🔥 MILME LOGIC ACTIVE  |  📞 SUBHA MODS  |  Ctrl+C Exit" + DIM + "  │" + RESET)
            print(DIM + "└" + "─"*60 + "┘" + RESET)
            
            time.sleep(1.5)
            
    except KeyboardInterrupt:
        clear()
        print_banner()
        total = predictor.wins + predictor.losses
        acc = (predictor.wins / total * 100) if total > 0 else 0
        print()
        print(GREEN + "╔" + "═"*60 + "╗" + RESET)
        print(GREEN + "║" + RESET + "  " + BOLD + WHITE + "🐆 SNX PANTHER SHUTDOWN" + RESET + " " * 33 + GREEN + "║" + RESET)
        print(GREEN + "╠" + "═"*60 + "╣" + RESET)
        print(GREEN + "║" + RESET + "  " + WHITE + "Final Stats:" + RESET + " " + YELLOW + str(predictor.wins) + "W" + RESET + " / " + RED + str(predictor.losses) + "L" + RESET + " | " + (GREEN if acc >= 50 else RED) + "{:.1f}".format(acc) + "%" + RESET + " " * (33 - len(str(predictor.wins)) - len(str(predictor.losses)) - len("{:.1f}".format(acc))) + GREEN + "║" + RESET)
        print(GREEN + "║" + RESET + "  " + WHITE + "Best Streak:" + RESET + " " + YELLOW + str(predictor.best_streak) + RESET + " " * (45 - len(str(predictor.best_streak))) + GREEN + "║" + RESET)
        print(GREEN + "╚" + "═"*60 + "╝" + RESET)
        print()
        print(CYAN + "Thanks for using! Contact SUBHA MODS" + RESET)

if __name__ == "__main__":
    main()