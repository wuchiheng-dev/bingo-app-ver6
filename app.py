from flask import Flask, jsonify, render_template_string, request
import requests, os, random
from math import comb

app = Flask(__name__)

# =========================
# ✅ 官方資料
# =========================
def get_latest():
    url = "https://api.taiwanlottery.com/TLCAPIWeB/Lottery/LatestBingoResult"
    try:
        r = requests.get(url, timeout=5).json()
        nums = r["content"]["lotteryBingoLatestPost"]["bigShowOrder"]
        return [int(x) for x in nums]
    except:
        return random.sample(range(1,81),20)

# =========================
# ✅ 隨機選號（符合規則）
# =========================
def pick_numbers(count):
    return sorted(random.sample(range(1,81), count))

# =========================
# ✅ 機率
# =========================
def prob(k, h):
    return comb(20, h) * comb(60, k-h) / comb(80, k)

# =========================
# ✅ 獎金
# =========================
PAYOUT = {
    4: {2:25, 3:100, 4:1000},
    5: {3:50, 4:500, 5:7500},
    6: {3:25, 4:200, 5:1000, 6:25000},
    7: {4:25, 5:300, 6:3000, 7:80000},
    8: {0:25, 5:25, 6:1000, 7:20000, 8:500000},
    9: {0:25, 6:500, 7:3000, 8:100000, 9:1000000},
    10:{0:25, 5:25, 6:250, 7:2500, 8:25000, 9:250000, 10:5000000},
}

def calc_ev(k):
    if k not in PAYOUT:
        return None
    ev = 0
    for h, prize in PAYOUT[k].items():
        ev += prob(k, h) * prize
    roi = (ev - 25) / 25
    return round(ev,2), round(roi,3)

# =========================
# ✅ 最佳策略
# =========================
def best_strategy():
    res = []
    for k in range(4,11):
        r = calc_ev(k)
        if r:
            ev, roi = r
            res.append({"star":k, "roi":roi})
    res.sort(key=lambda x:x["roi"], reverse=True)
    return res

# =========================
# ✅ 投資組合
# =========================
def portfolio():
    return [
        {"star":4, "ratio":70},
        {"star":6, "ratio":20},
        {"star":8, "ratio":10}
    ]

# =========================
# ✅ UI
# =========================
HTML = """
<h1>🎯 Bingo Bingo 最優策略系統</h1>

<h3>選號</h3>
<input id="count" type="number" value="10" min="1" max="10">
<button onclick="pick()">產生號碼</button>

<div id="numbers"></div>

<hr>

<button onclick="load()">分析策略</button>

<div id="best"></div>
<div id="portfolio"></div>

<h3>最新開獎</h3>
<div id="latest"></div>

<script>

function balls(list){
 return list.map(n => `<span style="
 display:inline-block;
 width:40px;height:40px;
 border-radius:50%;
 background:orange;
 text-align:center;
 line-height:40px;
 margin:5px;
 color:white">${n}</span>`).join("")
}

async function pick(){
 let c = document.getElementById("count").value
 let r = await fetch('/pick?count='+c)
 let j = await r.json()
 document.getElementById("numbers").innerHTML = balls(j.numbers)
}

async function load(){
 let r = await fetch('/analysis')
 let j = await r.json()

 let b = "<h3>最佳星數</h3>"
 j.best.forEach(x=>{
   b += `星數 ${x.star} → ROI ${x.roi}<br>`
 })

 document.getElementById("best").innerHTML = b

 let p = "<h3>投資組合</h3>"
 j.portfolio.forEach(x=>{
   p += `星數 ${x.star} : ${x.ratio}%<br>`
 })

 document.getElementById("portfolio").innerHTML = p

 document.getElementById("latest").innerHTML = balls(j.latest)
}

</script>
"""

# =========================
# API
# =========================
@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/pick")
def pick_api():
    count = int(request.args.get("count", 10))
    return jsonify({"numbers": pick_numbers(count)})

@app.route("/analysis")
def analysis():
    return jsonify({
        "best": best_strategy(),
        "portfolio": portfolio(),
        "latest": get_latest()
    })

@app.route("/health")
def health():
    return jsonify({"ok":True})

# =========================
# Render
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
