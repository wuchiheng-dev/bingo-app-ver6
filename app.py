from flask import Flask, jsonify, request, render_template
import requests, random, os, time

app = Flask(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0"}

# =========================
# ✅ API（加強版：重試）
# =========================
def fetch_api():
    url = "https://api.taiwanlottery.com/TLCAPIWeB/Lottery/LatestBingoResult"

    for i in range(3):  # ✅ 重試3次
        try:
            r = requests.get(url, headers=HEADERS, timeout=5)

            if r.status_code != 200:
                continue

            data = r.json()

            d = data["content"]["lotteryBingoLatestPost"]

            term = int(d["drawTerm"])

            if term > 0:
                return {
                    "numbers": [int(x) for x in d["bigShowOrder"]],
                    "term": term,
                    "time": d["dDate"].replace("T", " "),
                    "source": "api"
                }

        except Exception as e:
            print("API錯誤:", e)

        time.sleep(1)

    return None

# =========================
# ✅ JSON備援（穩定來源）
# =========================
def fetch_backup():
    return {
        "term": 11526884,  # ✅ 你提供的最新期
        "time": "2026-05-13 14:24",
        "numbers": [3,9,12,14,18,24,26,30,35,39,40,43,46,47,58,59,60,68,69,79],
        "source": "backup"
    }

# =========================
# ✅ 最新資料（核心）
# =========================
def get_latest():

    api = fetch_api()

    if api:
        return api

    # ✅ API失敗 → 用備援
    return fetch_backup()

# =========================
# ✅ 統計選號
# =========================
def smart_pick(k):
    step = 80 // k
    nums = []

    for i in range(k):
        low = i*step + 1
        high = (i+1)*step

        nums.append(random.randint(low, high))

    return sorted(nums)

# =========================
# ✅ 命中
# =========================
def check_hit(pick, draw):
    return list(set(pick) & set(draw))

# =========================
# ✅ UI
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
    k = int(data.get("count", 3))

    return jsonify({"numbers": smart_pick(k)})

# =========================
# ✅ 監控
# =========================
@app.route("/monitor")
def monitor():

    nums = request.args.get("nums", "")
    my = [int(x) for x in nums.split(",") if x]

    latest = get_latest()
    hit = check_hit(my, latest["numbers"])

    print("DEBUG:", latest)

    return jsonify({
        "term": latest["term"],
        "time": latest["time"],
        "draw": latest["numbers"],
        "hit": hit,
        "source": latest["source"]
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
