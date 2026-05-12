from flask import Flask, jsonify, render_template_string
import random, os
from math import comb
import matplotlib.pyplot as plt

app = Flask(__name__)

# =========================
# ✅ 模擬歷史資料（1000期）
# =========================
def gen_data(n=1000):
    return [random.sample(range(1,81),20) for _ in range(n)]

# =========================
# ✅ 機率
# =========================
def prob(k,h):
    return comb(20,h)*comb(60,k-h)/comb(80,k)

PAYOUT = {
    4:{2:25,3:100,4:1000},
    6:{3:25,4:200,5:1000,6:25000}
}

# =========================
# ✅ 隨機選號（分散）
# =========================
def pick(k):
    return random.sample(range(1,81),k)

# =========================
# ✅ 命中
# =========================
def hit(pick, draw):
    return len(set(pick)&set(draw))

# =========================
# ✅ 單注盈利
# =========================
def reward(k,h):
    return PAYOUT.get(k,{}).get(h,0)

# =========================
# ✅ 策略（組合）
# =========================
def strategy():
    # ✅ 投資組合
    return [
        {"k":4, "n":8},   # 8注4星
        {"k":6, "n":2}    # 2注6星
    ]

# =========================
# ✅ 回測
# =========================
def backtest():
    data = gen_data(500)
    balance = 0
    history = []

    for d in data:
        cost = 0
        profit = 0

        for s in strategy():
            for _ in range(s["n"]):
                p = pick(s["k"])
                h = hit(p,d)
                profit += reward(s["k"],h)
                cost += 25

        balance += (profit - cost)
        history.append(balance)

    return history

# =========================
# ✅ 畫圖
# =========================
def plot(history):
    plt.figure()
    plt.plot(history)
    plt.title("ROI Backtest")
    plt.xlabel("round")
    plt.ylabel("profit")

    path = "static.png"
    plt.savefig(path)
    plt.close()
    return path

# =========================
# ✅ API
# =========================
@app.route("/")
def index():
    return """
    <h1>🎯 Bingo 策略引擎</h1>
    <button onclick="run()">回測</button>
    <div id="img"></div>

    <script>
    async function run(){
        let r = await fetch('/run')
        let j = await r.json()
        document.getElementById("img").innerHTML =
        "<img src='"+j.img+"?t="+Date.now()+"'>"
    }
    </script>
    """

@app.route("/run")
def run():
    h = backtest()
    img = plot(h)

    return jsonify({"img": "/" + img})

@app.route("/health")
def health():
    return {"ok":True}

if __name__ == "__main__":
    port=int(os.environ.get("PORT",10000))
    app.run(host="0.0.0.0",port=port)
