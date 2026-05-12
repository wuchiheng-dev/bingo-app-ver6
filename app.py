from flask import Flask, jsonify, request, render_template_string
import requests, os, random, datetime
from math import comb
from bs4 import BeautifulSoup

app = Flask(__name__)

# =========================
# ✅ 官方 API
# =========================
def fetch_api():
    try:
        url = "https://api.taiwanlottery.com/TLCAPIWeB/Lottery/LatestBingoResult"
        r = requests.get(url, timeout=5).json()
        d = r["content"]["lotteryBingoLatestPost"]

        return {
            "numbers": [int(x) for x in d["bigShowOrder"]],
            "time": d["dDate"].replace("T"," "),
            "source": "api"
        }
    except:
        return None

# =========================
# ✅ 即時網站（備援）
# =========================
def fetch_web():
    try:
        url = "https://lotto.auzonet.com/bingobingoV1.php"
        html = requests.get(url, timeout=5).text
        soup = BeautifulSoup(html, "lxml")

        row = soup.select("table tr")[1]
        cols = row.text.split()

        return {
            "numbers": list(map(int, cols[2:22])),
            "time": cols[1],
            "source": "web"
        }
    except:
        return None

# =========================
# ✅ 比較最新一期
# =========================
def get_latest():
    api = fetch_api()
    web = fetch_web()

    if api and web:
        return max([api, web], key=lambda x: x["time"])

    return api or web or {
        "numbers": random.sample(range(1,81),20),
        "time": "fallback",
        "source": "fallback"
    }

# =========================
# ✅ 倒數（5分鐘）
# =========================
def countdown():
    now = datetime.datetime.now()

    minute = now.minute
    next_min = ((minute // 5) + 1) * 5

    if next_min == 60:
        next_time = now.replace(hour=now.hour+1, minute=0, second=0)
    else:
        next_time = now.replace(minute=next_min, second=0)

    return (next_time - now).seconds

# =========================
# ✅ 選號
# =========================
def pick_numbers(n):
    return sorted(random.sample(range(1,81), n))

# =========================
# ✅ 命中
# =========================
def check_hit(pick, draw):
    return list(set(pick) & set(draw))

# =========================
# ✅ ROI最佳星數
# =========================
def prob(k, h):
    return comb(20,h)*comb(60,k-h)/comb(80,k)

PAYOUT = {
    4:{2:25,3:100,4:1000},
    5:{3:50,4:500,5:7500},
    6:{3:25,4:200,5:1000,6:25000},
    7:{4:25,5:300,6:3000,7:80000},
    8:{0:25,5:25,6:1000,7:20000,8:500000},
    9:{0:25,6:500,7:3000,8:100000,9:1000000},
    10:{0:25,5:25,6:250,7:2500,8:25000,9:250000,10:5000000}
}

def best_star():
    res=[]
    for k in range(4,11):
        ev=0
        for h,p in PAYOUT[k].items():
            ev+=prob(k,h)*p
        roi=(ev-25)/25
        res.append((k,roi))
    res.sort(key=lambda x:x[1],reverse=True)
    return res[0][0]

# =========================
# ✅ UI
# =========================
HTML = """
<h1>🎯 Bingo 即時同步系統</h1>

<h3>選號</h3>
<input id="count" value="10" type="number" min="1" max="10">
<button onclick="pick()">產生號碼</button>

<div id="my"></div>
<div id="hit"></div>

<hr>

<button onclick="start()">開始監控</button>

<h3 id="time"></h3>
<div id="draw"></div>
<div id="cd"></div>
<div id="strategy"></div>

<script>
let myNumbers=[]
let lastTime=""

function balls(list,hit=[]){
 return list.map(n=>{
  let c=hit.includes(n)?"red":"orange"
  return `<span style="display:inline-block;width:40px;height:40px;border-radius:50%;background:${c};color:white;text-align:center;line-height:40px;margin:5px">${n}</span>`
 }).join("")
}

async function pick(){
 let c=document.getElementById("count").value
 let r=await fetch('/pick?count='+c)
 let j=await r.json()
 myNumbers=j.numbers
 document.getElementById("my").innerHTML="你的號碼<br>"+balls(myNumbers)
}

function start(){
 update()
 setInterval(update,2000)
}

async function update(){
 let r=await fetch('/monitor?numbers='+myNumbers.join(","))
 let j=await r.json()

 if(j.time!=lastTime){
   lastTime=j.time

   document.getElementById("time").innerHTML=
   "最新開獎: "+j.time+" ("+j.source+")"

   document.getElementById("draw").innerHTML=
   balls(j.draw,j.hit)

   document.getElementById("hit").innerHTML=
   "命中:"+j.hit.join(",")

   if(j.hit.length>=3){
     alert("🎯 命中 "+j.hit.length+" 顆")
   }
 }

 document.getElementById("cd").innerHTML=
 "下期倒數:"+j.countdown+" 秒"

 document.getElementById("strategy").innerHTML=
 "建議星數:"+j.best
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
def pick():
    c=int(request.args.get("count",10))
    return jsonify({"numbers": pick_numbers(c)})

@app.route("/monitor")
def monitor():
    nums=request.args.get("numbers","")
    my=[int(x) for x in nums.split(",") if x]

    latest=get_latest()
    hit=check_hit(my,latest["numbers"])

    return jsonify({
        "draw":latest["numbers"],
        "time":latest["time"],
        "source":latest["source"],
        "hit":hit,
        "countdown":countdown(),
        "best":best_star()
    })

@app.route("/health")
def health():
    return jsonify({"ok":True})

if __name__=="__main__":
    port=int(os.environ.get("PORT",10000))
    app.run(host="0.0.0.0",port=port)
