from flask import Flask, jsonify, request, render_template_string
import requests, random, os
from bs4 import BeautifulSoup

app = Flask(__name__)

# =========================
# ✅ 三來源抓取
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


def fetch_auzo():
    try:
        html = requests.get("https://lotto.auzonet.com/bingobingoV1.php", timeout=5).text
        soup = BeautifulSoup(html, "lxml")

        for tr in soup.find_all("tr"):
            text = tr.get_text(" ", strip=True)
            parts = text.split()

            if len(parts) > 22 and parts[0].isdigit():
                term = int(parts[0])
                time = parts[1]
                nums = list(map(int, parts[2:22]))

                return {
                    "numbers": nums,
                    "time": time,
                    "term": term,
                    "source": "auzo"
                }
    except:
        return None


def fetch_pilio():
    try:
        html = requests.get("https://www.pilio.idv.tw/bingo/list.asp", timeout=5).text
        soup = BeautifulSoup(html, "lxml")

        text = soup.get_text()
        for line in text.split("\n"):
            parts = line.strip().split()

            if len(parts) >= 21 and parts[0].isdigit():
                term = int(parts[0])
                nums = list(map(int, parts[1:21]))
                return {
                    "numbers": nums,
                    "time": "latest",
                    "term": term,
                    "source": "pilio"
                }
    except:
        return None


# =========================
# ✅ 取最新（用期數）
# =========================
def get_latest():
    data = [fetch_api(), fetch_auzo(), fetch_pilio()]
    data = [d for d in data if d]

    if not data:
        return {"numbers": [], "term": 0, "time": "error", "source": "none"}

    return max(data, key=lambda x: x["term"])


# =========================
# ✅ 選號（核心策略）
# =========================

def smart_pick(k):
    # ✅ 均勻分布
    step = 80 // k
    nums = [(i * step + random.randint(1, step)) for i in range(k)]
    return sorted(set([min(80, max(1,x)) for x in nums]))


# =========================
# ✅ 命中計算
# =========================
def check_hit(pick, draw):
    return list(set(pick) & set(draw))


# =========================
# ✅ UI
# =========================

HTML = """
<h1>🎯 Bingo AI選號 + 即時監控</h1>

<h3>選號（1~10星）</h3>
<input id="count" value="10">
<button onclick="pick()">產生號碼</button>

<div id="my"></div>
<div id="hit"></div>

<hr>

<button onclick="start()">開始監控</button>

<h3 id="info"></h3>
<div id="draw"></div>

<script>

let my=[]
let last=0

function balls(list, hit=[]){
 return list.map(n=>{
   let c = hit.includes(n) ? "red" : "orange"
   return `<span style="display:inline-block;width:40px;height:40px;border-radius:50%;background:${c};color:white;text-align:center;line-height:40px;margin:5px">${n}</span>`
 }).join("")
}

async function pick(){
 let c = document.getElementById("count").value
 let r = await fetch('/pick?count='+c)
 let j = await r.json()

 my=j.numbers

 document.getElementById("my").innerHTML =
 "<b>你的號碼</b><br>"+balls(my)
}

function start(){
 update()
 setInterval(update,3000)
}

async function update(){
 let r = await fetch('/monitor?nums='+my.join(","))
 let j = await r.json()

 if(j.term > last){
   last = j.term

   document.getElementById("info").innerHTML =
   "期數:"+j.term+"<br>時間:"+j.time+" ("+j.source+")"

   document.getElementById("draw").innerHTML =
   balls(j.draw, j.hit)

   document.getElementById("hit").innerHTML =
   "命中:"+j.hit.join(",")

   if(j.hit.length >= 3){
     alert("🎯 命中 "+j.hit.length+" 顆!!")
   }
 }
}

</script>
"""

# =========================
# ✅ API
# =========================

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/pick")
def pick_api():
    c=int(request.args.get("count",10))
    return {"numbers": smart_pick(c)}

@app.route("/monitor")
def monitor():
    nums = request.args.get("nums","")
    my = [int(x) for x in nums.split(",") if x]

    latest = get_latest()

    hit = check_hit(my, latest["numbers"])

    return {
        "draw": latest["numbers"],
        "term": latest["term"],
        "time": latest["time"],
        "source": latest["source"],
        "hit": hit
    }

@app.route("/health")
def health():
    return {"ok":True}

if __name__ == "__main__":
    port=int(os.environ.get("PORT",10000))
    app.run(host="0.0.0.0",port=port)
