from flask import Flask, jsonify, request, render_template
import requests, random, os
from bs4 import BeautifulSoup

app = Flask(__name__)

# =========================
# ✅ 三來源（簡化穩定版）
# =========================
def fetch_api():
    try:
        url = "https://api.taiwanlottery.com/TLCAPIWeB/Lottery/LatestBingoResult"
        r = requests.get(url, timeout=5).json()
        d = r["content"]["lotteryBingoLatestPost"]

        return {
            "numbers": [int(x) for x in d["bigShowOrder"]],
            "time": d["dDate"].replace("T"," "),
            "term": int(d["drawTerm"]),
            "source": "api"
        }
    except:
        return None

# =========================
# ✅ 最新資料
# =========================
def get_latest():
    data = [fetch_api()]
    data = [d for d in data if d]

    if not data:
        return {"numbers":[], "term":0, "time":"error", "source":"none"}

    return max(data, key=lambda x: x["term"])

# =========================
# ✅ 選號（核心）
# =========================
def smart_pick(k):
    step = 80 // k
    nums = [(i * step + random.randint(1, step)) for i in range(k)]
    return sorted(set([min(80, max(1,x)) for x in nums]))

# =========================
# ✅ 命中
# =========================
def check_hit(pick, draw):
    return list(set(pick) & set(draw))

# =========================
# ✅ 頁面
# =========================
@app.route("/")
def index():
    return render_template("index.html")

# =========================
# ✅ 選號
# =========================
@app.route("/pick", methods=["POST"])
def pick():
    data = request.json
    k = int(data.get("count", 10))

    return jsonify({
        "numbers": smart_pick(k),
        "weekday": "AI策略"
    })

# =========================
# ✅ 即時監控
# =========================
@app.route("/monitor")
def monitor():
    nums = request.args.get("nums","")
    my = [int(x) for x in nums.split(",") if x]

    latest = get_latest()
    hit = check_hit(my, latest["numbers"])

    return jsonify({
        "draw": latest["numbers"],
        "term": latest["term"],
        "time": latest["time"],
        "hit": hit
    })

@app.route("/health")
def health():
    return {"ok":True}

if __name__ == "__main__":
    port=int(os.environ.get("PORT",10000))
    app.run(host="0.0.0.0",port=port)
