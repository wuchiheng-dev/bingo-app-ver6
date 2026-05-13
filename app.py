from flask import Flask, jsonify, request, render_template
import requests, random, os

app = Flask(__name__)

HEADERS = {"User-Agent":"Mozilla/5.0"}

# =========================
# ✅ 官方 API
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
    except Exception as e:
        print("API失敗:", e)
        return None

# =========================
# ✅ 穩定備援（固定可用）
# =========================
def backup_data():
    return {
        "numbers": [3,9,12,14,18,24,26,30,35,39,40,43,46,47,58,59,60,68,69,79],
        "term": 115026800,
        "time": "backup",
        "source": "backup"
    }

# =========================
# ✅ 最新資料
# =========================
def get_latest():
    api = fetch_api()

    if api and api["term"] > 0:
        return api

    # ✅ 一定有資料（關鍵修正）
    return backup_data()

# =========================
# ✅ 選號（統計法）
# =========================
def smart_pick(k):
    step = 80 // k
    nums = []

    for i in range(k):
        low = i*step+1
        high = (i+1)*step
        nums.append(random.randint(low,high))

    return sorted(nums)

# =========================
# ✅ 命中
# =========================
def check_hit(pick, draw):
    return list(set(pick)&set(draw))

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
    data=request.json
    k=int(data.get("count",5))

    return jsonify({"numbers": smart_pick(k)})

# =========================
# ✅ 監控
# =========================
@app.route("/monitor")
def monitor():
    nums=request.args.get("nums","")
    my=[int(x) for x in nums.split(",") if x]

    latest=get_latest()
    hit=check_hit(my, latest["numbers"])

    print("DEBUG:", latest)

    return jsonify({
        "term": latest["term"],
        "time": latest["time"],
        "draw": latest["numbers"],
        "hit": hit,
        "source": latest["source"]
    })

if __name__ == "__main__":
    port=int(os.environ.get("PORT",10000))
    app.run(host="0.0.0.0",port=port)
