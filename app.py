from flask import Flask, jsonify, render_template_string
import requests, os
from math import comb

app = Flask(__name__)

# =========================
# ✅ 台彩最新資料
# =========================
def get_latest():
    url = "https://api.taiwanlottery.com/TLCAPIWeB/Lottery/LatestBingoResult"
    try:
        r = requests.get(url, timeout=5).json()
        nums = r["content"]["lotteryBingoLatestPost"]["bigShowOrder"]
        return [int(x) for x in nums]
    except:
        return []

# =========================
# ✅ 機率模型（超幾何分布）
# =========================
def prob(k, h):
    return comb(20, h) * comb(60, k-h) / comb(80, k)

# =========================
# ✅ 獎金表（簡化版）
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

# =========================
# ✅ EV 계산
# =========================
def calc_ev(k):
    if k not in PAYOUT:
        return None

    ev = 0
    for h, prize in PAYOUT[k].items():
        ev += prob(k, h) * prize

    cost = 25
    roi = (ev - cost) / cost
    return round(ev,2), round(roi,3)

# =========================
# ✅ 找最佳星數
# =========================
def best_strategy():
    results = []

    for k in range(4,11):
        v = calc_ev(k)
        if v:
            ev, roi = v
            results.append({
                "star": k,
                "ev": ev,
                "roi": roi
            })

    # 按 ROI 排序
    results.sort(key=lambda x: x["roi"], reverse=True)
    return results

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
<h1>🎯 Bingo Bingo 數學最優策略</h1>

<button onclick="load()">分析</button>

<div id="best"></div>
<div id="portfolio"></div>
<div id="latest"></div>

<script>

async function load(){
 let r = await fetch('/analysis')
 let j = await r.json()

 let html = "<h2>最佳星數</h2>"
 j.best.forEach(x=>{
   html += `星數 ${x.star} → ROI ${x.roi}<br>`
 })

 document.getElementById("best").innerHTML = html

 // 投資組合
 let p = "<h2>推薦投資組合</h2>"
 j.portfolio.forEach(x=>{
   p += `星數 ${x.star} : ${x.ratio}%<br>`
 })

 document.getElementById("portfolio").innerHTML = p

 // 最新開獎
 let l = "<h2>最新開獎</h2>" + j.latest.join(" ")
 document.getElementById("latest").innerHTML = l
}

</script>
"""

# =========================
# API
# =========================
@app.route("/")
def index():
    return render_template_string(HTML)

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
# Render PORT
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
