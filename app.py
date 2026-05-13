from flask import Flask, jsonify, request, render_template
import requests, random, os
from bs4 import BeautifulSoup

app = Flask(__name__)

HEADERS = {"User-Agent":"Mozilla/5.0"}

# =========================
# ✅ 官方開獎
# =========================
def fetch_api():
    try:
        url="https://api.taiwanlottery.com/TLCAPIWeB/Lottery/LatestBingoResult"
        r=requests.get(url,headers=HEADERS,timeout=5).json()
        d=r["content"]["lotteryBingoLatestPost"]

        return {
            "numbers":[int(x) for x in d["bigShowOrder"]],
            "term":int(d["drawTerm"]),
            "time":d["dDate"].replace("T"," "),
            "source":"api"
        }
    except:
        return None

# =========================
# ✅ 最新一期
# =========================
def get_latest():
    data = fetch_api()

    if data:
        return data

    return {
        "numbers":[],
        "term":0,
        "time":"error",
        "source":"none"
    }

# =========================
# ✅ 統計選號（核心）
# =========================
def smart_pick(k):
    step = 80 // k
    result = []

    for i in range(k):
        low = i*step + 1
        high = (i+1)*step
        result.append(random.randint(low, high))

    return sorted(result)

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
    k = int(data.get("count",5))

    return jsonify({
        "numbers": smart_pick(k)
    })

# =========================
# ✅ 監控
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
        "hit": hit,
        "source": latest["source"]
    })

if __name__=="__main__":
    port=int(os.environ.get("PORT",10000))
    app.run(host="0.0.0.0",port=port)
