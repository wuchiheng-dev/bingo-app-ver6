from flask import Flask, jsonify, request, render_template
import requests, random, os
from bs4 import BeautifulSoup

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# =========================
# ✅ 來源1：官方 API
# =========================
def fetch_api():
    try:
        url = "https://api.taiwanlottery.com/TLCAPIWeB/Lottery/LatestBingoResult"
        r = requests.get(url, headers=HEADERS, timeout=5).json()
        d = r["content"]["lotteryBingoLatestPost"]

        return {
            "numbers": [int(x) for x in d["bigShowOrder"]],
            "term": int(d["drawTerm"]),
            "time": d["dDate"].replace("T"," "),
            "source": "api"
        }
    except:
        return None

# =========================
# ✅ 來源2：auzo（較穩）
# =========================
def fetch_auzo():
    try:
        html = requests.get("https://lotto.auzonet.com/bingobingoV1.php", headers=HEADERS, timeout=5).text
        soup = BeautifulSoup(html, "lxml")

        for tr in soup.find_all("tr"):
            text = tr.get_text(" ", strip=True)
            parts = text.split()

            if len(parts) >= 22 and parts[0].isdigit():
                return {
                    "term": int(parts[0]),
                    "time": parts[1],
                    "numbers": list(map(int, parts[2:22])),
                    "source": "auzo"
                }
    except:
        return None

# =========================
# ✅ 來源3：pilio（備援）
# =========================
def fetch_pilio():
    try:
        html = requests.get("https://www.pilio.idv.tw/bingo/list.asp", headers=HEADERS, timeout=5).text
        soup = BeautifulSoup(html, "lxml")

        text = soup.get_text()
        for line in text.split("\n"):
            parts = line.strip().split()

            if len(parts) >= 21 and parts[0].isdigit():
                return {
                    "term": int(parts[0]),
                    "numbers": list(map(int, parts[1:21])),
                    "time": "latest",
                    "source": "pilio"
                }
    except:
        return None

# =========================
# ✅ 三來源整合（關鍵）
# =========================
def get_latest():
    sources = [fetch_api(), fetch_auzo(), fetch_pilio()]
    sources = [s for s in sources if s]

    if not sources:
        # ✅ 強制 fallback（永不空）
        return {
            "term": 999999,
            "time": "fallback",
            "numbers": random.sample(range(1,81),20),
            "source": "fallback"
        }

    # ✅ 用期數判斷最新
    return max(sources, key=lambda x: x["term"])

# =========================
# ✅ 選號（優化版）
# =========================
def smart_pick(k):
    step = 80 // k
    nums = [(i*step + random.randint(1,step)) for i in range(k)]
    return sorted(list(set([min(80,max(1,n)) for n in nums])))

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
    k = int(data.get("count",10))

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
        "term": latest["term"],
        "time": latest["time"],
        "draw": latest["numbers"],
        "hit": hit,
        "source": latest["source"]
    })

@app.route("/health")
def health():
    return {"ok": True}

if __name__ == "__main__":
    port = int(os.environ.get("PORT",10000))
    app.run(host="0.0.0.0", port=port)
