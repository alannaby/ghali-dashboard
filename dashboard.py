from flask import Flask, render_template_string, request, redirect, url_for, session
import sqlite3
import pandas as pd
from datetime import datetime
import hashlib
import os

app = Flask(__name__)
app.secret_key = "ghali_trading_2024_secret_key_xK9mP2"

DB_PATH = r"C:\Users\hp\bybit_data\learning_center.db"
PASSWORD = "ghali2024"
PASSWORD_HASH = hashlib.sha256(PASSWORD.encode()).hexdigest()

def get_db():
    return sqlite3.connect(DB_PATH)

def check_auth():
    return session.get("logged_in", False)

LOGIN_HTML = """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <title>غالي — دخول</title>
    <style>
        * { margin:0; padding:0; box-sizing:border-box; }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #0a0a1a 0%, #0d1b2a 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .box {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(0,212,255,0.3);
            border-radius: 24px;
            padding: 50px 40px;
            width: 380px;
            text-align: center;
            backdrop-filter: blur(10px);
            box-shadow: 0 0 60px rgba(0,212,255,0.1);
        }
        .logo { font-size: 60px; margin-bottom: 10px; animation: pulse 2s infinite; }
        @keyframes pulse { 0%,100%{transform:scale(1)} 50%{transform:scale(1.1)} }
        h1 { color: #00d4ff; font-size: 28px; margin-bottom: 5px; }
        .sub { color: #888; margin-bottom: 30px; font-size: 14px; }
        input {
            width: 100%;
            padding: 14px;
            border: 1px solid rgba(0,212,255,0.3);
            border-radius: 10px;
            background: rgba(255,255,255,0.05);
            color: white;
            font-size: 16px;
            margin-bottom: 15px;
            text-align: center;
            outline: none;
        }
        input:focus { border-color: #00d4ff; }
        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #00d4ff, #0096ff);
            border: none;
            border-radius: 10px;
            color: #0a0a1a;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
        }
        .err { color: #ff6b6b; margin-bottom: 15px; }
        .lock { color: #555; font-size: 12px; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="box">
        <div class="logo">🤖</div>
        <h1>غالي التداولي</h1>
        <p class="sub">لوحة التحكم الذكية V14</p>
        {% if error %}<div class="err">{{ error }}</div>{% endif %}
        <form method="POST">
            <input type="password" name="password" placeholder="🔑 كلمة المرور" autofocus>
            <button type="submit">دخول 🚀</button>
        </form>
        <p class="lock">🔒 محمية ومشفرة</p>
    </div>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <title>غالي — لوحة التحكم</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --bg: #0a0a1a;
            --panel: rgba(255,255,255,0.03);
            --border: rgba(255,255,255,0.1);
            --text: #ffffff;
            --text2: #888888;
            --blue: #00d4ff;
            --green: #00ff64;
            --red: #ff6b6b;
            --gold: #ffd700;
        }
        .light {
            --bg: #f0f4f8;
            --panel: rgba(255,255,255,0.9);
            --border: rgba(0,0,0,0.1);
            --text: #1a202c;
            --text2: #666666;
            --blue: #0096ff;
            --green: #00aa44;
            --red: #dd2222;
            --gold: #cc8800;
        }
        * { margin:0; padding:0; box-sizing:border-box; }
        body { font-family: 'Segoe UI', Arial, sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; }
        .nav {
            background: rgba(0,0,0,0.3);
            border-bottom: 1px solid var(--border);
            padding: 12px 25px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 100;
            backdrop-filter: blur(10px);
        }
        .nav h1 { color: var(--blue); font-size: 20px; }
        .nav-right { display: flex; align-items: center; gap: 10px; }
        .time-badge { background: var(--panel); border: 1px solid var(--border); padding: 6px 12px; border-radius: 8px; font-size: 13px; color: var(--text2); }
        .theme-btn { background: var(--panel); border: 1px solid var(--border); color: var(--text); padding: 8px 16px; border-radius: 10px; cursor: pointer; font-size: 14px; }
        .logout-btn { background: rgba(255,50,50,0.1); border: 1px solid rgba(255,50,50,0.3); color: var(--red); padding: 8px 16px; border-radius: 10px; text-decoration: none; font-size: 14px; }
        .wrap { padding: 20px 25px; max-width: 1300px; margin: 0 auto; }
        .conds { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 20px; }
        .cond { background: rgba(0,255,100,0.08); border: 1px solid rgba(0,255,100,0.25); color: var(--green); padding: 5px 14px; border-radius: 20px; font-size: 12px; font-weight: bold; }
        .cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }
        .card { background: var(--panel); border: 1px solid var(--border); border-radius: 16px; padding: 22px; text-align: center; transition: transform 0.2s; }
        .card:hover { transform: translateY(-3px); }
        .card-icon { font-size: 32px; margin-bottom: 10px; }
        .card-val { font-size: 26px; font-weight: bold; margin-bottom: 5px; }
        .card-lbl { color: var(--text2); font-size: 13px; }
        .c-blue  { border-color: rgba(0,212,255,0.4); } .c-blue  .card-val { color: var(--blue); }
        .c-green { border-color: rgba(0,255,100,0.4); } .c-green .card-val { color: var(--green); }
        .c-gold  { border-color: rgba(255,200,0,0.4); } .c-gold  .card-val { color: var(--gold); }
        .c-pnl   { border-color: rgba(0,255,100,0.4); } .c-pnl   .card-val { color: var(--green); }
        .row { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px; }
        .panel { background: var(--panel); border: 1px solid var(--border); border-radius: 16px; padding: 20px; margin-bottom: 15px; }
        .panel h2 { color: var(--blue); font-size: 16px; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid var(--border); }
        table { width: 100%; border-collapse: collapse; }
        th { color: var(--text2); font-size: 12px; padding: 8px 10px; text-align: right; border-bottom: 1px solid var(--border); font-weight: normal; }
        td { padding: 11px 10px; border-bottom: 1px solid var(--border); font-size: 13px; }
        tr:last-child td { border-bottom: none; }
        .win { color: var(--green); } .loss { color: var(--red); } .open { color: var(--blue); }
        .badge { background: rgba(0,212,255,0.1); border: 1px solid rgba(0,212,255,0.25); color: var(--blue); padding: 3px 8px; border-radius: 6px; font-size: 11px; }
        .chart-box { height: 230px; position: relative; }
        .sym-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
        .sym-card { background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 14px; text-align: center; transition: transform 0.2s; }
        .sym-card:hover { transform: translateY(-2px); border-color: var(--blue); }
        .sym-name { color: var(--blue); font-size: 13px; font-weight: bold; margin-bottom: 4px; }
        .sym-pf { font-size: 20px; font-weight: bold; color: var(--green); margin-bottom: 3px; }
        .sym-wr { color: var(--text2); font-size: 11px; }
        .no-data { color: var(--text2); text-align: center; padding: 25px; font-size: 14px; }
        .refresh-info { text-align: center; color: var(--text2); font-size: 12px; padding: 15px; }
    </style>
</head>
<body>
    <div class="nav">
        <h1>🤖 غالي التداولي V14</h1>
        <div class="nav-right">
            <span class="time-badge" id="clock">{{ now }}</span>
            <button class="theme-btn" onclick="toggleTheme()" id="themeBtn">☀️ نهاري</button>
            <a href="/logout" class="logout-btn">خروج 🔒</a>
        </div>
    </div>

    <div class="wrap">
        <div class="conds">
            <span class="cond">✅ 15د + 30د صاعدين</span>
            <span class="cond">✅ RSI 30د &lt; 65</span>
            <span class="cond">✅ EMA50 &gt; EMA200 (30د)</span>
            <span class="cond">✅ gann_1x1 محذوف</span>
            <span class="cond">⭐ الساعة = نقاط إضافية</span>
            <span class="cond">📈 RSI 5د صاعد = +20 نقطة</span>
        </div>

        <div class="cards">
            <div class="card c-blue">
                <div class="card-icon">💰</div>
                <div class="card-val">${{ capital }}</div>
                <div class="card-lbl">رأس المال الحالي</div>
            </div>
            <div class="card c-green">
                <div class="card-icon">🎯</div>
                <div class="card-val">{{ win_rate }}%</div>
                <div class="card-lbl">نسبة الفوز</div>
            </div>
            <div class="card c-gold">
                <div class="card-icon">📊</div>
                <div class="card-val">{{ total_trades }}</div>
                <div class="card-lbl">إجمالي الصفقات</div>
            </div>
            <div class="card c-pnl">
                <div class="card-icon">🏆</div>
                <div class="card-val">{{ pnl_str }}</div>
                <div class="card-lbl">الربح / الخسارة</div>
            </div>
        </div>

        <div class="row">
            <div class="panel">
                <h2>🔄 الصفقات المفتوحة ({{ open_count }})</h2>
                {% if open_trades %}
                <table>
                    <tr><th>العملة</th><th>الدخول</th><th>الوقف</th><th>هدف 2</th><th>الأداة</th></tr>
                    {% for t in open_trades %}
                    <tr>
                        <td class="open" style="font-weight:bold">{{ t.symbol }}</td>
                        <td>{{ t.entry_price }}</td>
                        <td class="loss">{{ t.stop_loss }}</td>
                        <td class="win">{{ t.target2 }}</td>
                        <td><span class="badge">{{ t.entry_tool }}</span></td>
                    </tr>
                    {% endfor %}
                </table>
                {% else %}
                <p class="no-data">😴 لا توجد صفقات مفتوحة</p>
                {% endif %}
            </div>

            <div class="panel">
                <h2>📈 أداء رأس المال</h2>
                <div class="chart-box">
                    <canvas id="chart"></canvas>
                </div>
            </div>
        </div>

        <div class="panel">
            <h2>📋 آخر الصفقات المغلقة</h2>
            {% if closed_trades %}
            <table>
                <tr><th>العملة</th><th>النتيجة</th><th>الربح%</th><th>أداة الدخول</th><th>سبب الخروج</th><th>التاريخ</th></tr>
                {% for t in closed_trades %}
                <tr>
                    <td style="font-weight:bold">{{ t.symbol }}</td>
                    <td class="{{ 'win' if t.result == 'win' else 'loss' }}">
                        {{ '✅ ربح' if t.result == 'win' else '❌ خسارة' }}
                    </td>
                    <td class="{{ 'win' if (t.pnl_pct or 0)|float > 0 else 'loss' }}">{{ t.pnl_pct }}%</td>
                    <td><span class="badge">{{ t.entry_tool }}</span></td>
                    <td style="color:var(--text2)">{{ t.exit_tool }}</td>
                    <td style="color:var(--text2);font-size:11px">{{ t.exit_time }}</td>
                </tr>
                {% endfor %}
            </table>
            {% else %}
            <p class="no-data">لا توجد صفقات مغلقة بعد</p>
            {% endif %}
        </div>

        <div class="row">
            <div class="panel">
                <h2>🔧 أداء الأدوات</h2>
                {% if tool_stats %}
                <table>
                    <tr><th>الأداة</th><th>صفقات</th><th>Win%</th><th>متوسط $</th></tr>
                    {% for t in tool_stats %}
                    <tr>
                        <td><span class="badge">{{ t.tool }}</span></td>
                        <td>{{ t.total }}</td>
                        <td class="{{ 'win' if t.wr|float > 50 else ('open' if t.wr|float > 35 else 'loss') }}">{{ t.wr }}%</td>
                        <td class="{{ 'win' if t.avg|float > 0 else 'loss' }}">${{ t.avg }}</td>
                    </tr>
                    {% endfor %}
                </table>
                {% else %}
                <p class="no-data">لا توجد بيانات كافية بعد</p>
                {% endif %}
            </div>

            <div class="panel">
                <h2>📊 ملخص الأداء</h2>
                <table>
                    <tr><th>المؤشر</th><th>القيمة</th></tr>
                    <tr><td>رأس المال الأولي</td><td class="open">$10,000.00</td></tr>
                    <tr><td>رأس المال الحالي</td><td class="win">${{ capital }}</td></tr>
                    <tr><td>الربح/الخسارة</td><td class="win">{{ pnl_str }}</td></tr>
                    <tr><td>نسبة الفوز</td><td class="win">{{ win_rate }}%</td></tr>
                    <tr><td>صفقات رابحة</td><td class="win">✅ {{ wins }}</td></tr>
                    <tr><td>صفقات خاسرة</td><td class="loss">❌ {{ losses }}</td></tr>
                    <tr><td>صفقات مفتوحة</td><td class="open">🔄 {{ open_count }}</td></tr>
                </table>
            </div>
        </div>

        <div class="panel">
            <h2>🏆 أفضل العملات — باكتست 40 عملة × 3 سنوات</h2>
            <div class="sym-grid">
                {% for s in top_symbols %}
                <div class="sym-card">
                    <div class="sym-name">{{ s.symbol }}</div>
                    <div class="sym-pf">PF {{ s.pf }}</div>
                    <div class="sym-wr">WR {{ s.wr }}% | {{ s.tool }}</div>
                </div>
                {% endfor %}
            </div>
        </div>

        <p class="refresh-info">🔄 يتحدث تلقائياً كل دقيقة</p>
    </div>

    <script>
        function updateClock() {
            const now = new Date();
            document.getElementById('clock').textContent =
                now.toLocaleDateString('ar-SA') + ' — ' + now.toLocaleTimeString('ar-SA');
        }
        setInterval(updateClock, 1000); updateClock();

        let isLight = false;
        function toggleTheme() {
            isLight = !isLight;
            document.body.classList.toggle('light', isLight);
            document.getElementById('themeBtn').textContent = isLight ? '🌙 ليلي' : '☀️ نهاري';
            localStorage.setItem('theme', isLight ? 'light' : 'dark');
        }
        if (localStorage.getItem('theme') === 'light') {
            isLight = true;
            document.body.classList.add('light');
            document.getElementById('themeBtn').textContent = '🌙 ليلي';
        }

        const ctx = document.getElementById('chart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: {{ chart_labels | safe }},
                datasets: [{
                    data: {{ chart_data | safe }},
                    borderColor: '#00d4ff',
                    backgroundColor: 'rgba(0,212,255,0.08)',
                    borderWidth: 2.5,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointBackgroundColor: '#00d4ff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { color:'#888', font:{size:10}, maxTicksLimit:8 }, grid: { color:'rgba(255,255,255,0.05)' } },
                    y: { ticks: { color:'#888', callback: v => '$'+v.toLocaleString() }, grid: { color:'rgba(255,255,255,0.05)' } }
                }
            }
        });
        setTimeout(() => location.reload(), 60000);
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET","POST"])
def login():
    if check_auth():
        return redirect(url_for("dashboard"))
    error = None
    if request.method == "POST":
        pwd = request.form.get("password","")
        if hashlib.sha256(pwd.encode()).hexdigest() == PASSWORD_HASH:
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        else:
            error = "كلمة المرور غير صحيحة ❌"
    return render_template_string(LOGIN_HTML, error=error)

@app.route("/dashboard")
def dashboard():
    if not check_auth():
        return redirect(url_for("login"))
    conn = get_db()
    try:
        try:
            cap_df = pd.read_sql_query("SELECT capital FROM vt_capital ORDER BY id DESC LIMIT 1", conn)
            capital = round(float(cap_df.iloc[0]["capital"]),2) if not cap_df.empty else 10000.0
        except: capital = 10000.0

        try:
            open_df = pd.read_sql_query("SELECT * FROM vt_trades WHERE status='open'", conn)
        except: open_df = pd.DataFrame()

        try:
            closed_df = pd.read_sql_query(
                "SELECT * FROM vt_trades WHERE status='closed' ORDER BY exit_time DESC LIMIT 15", conn)
        except: closed_df = pd.DataFrame()

        wins   = int(len(closed_df[closed_df["result"]=="win"]))  if not closed_df.empty else 0
        losses = int(len(closed_df[closed_df["result"]=="loss"])) if not closed_df.empty else 0
        total  = wins + losses
        win_rate = round(float(wins)/float(total)*100.0,1) if total>0 else 0.0
        pnl = round(capital - 10000.0, 2)
        pnl_str = ("+$" if pnl>=0 else "-$") + f"{abs(pnl):,.2f}"

        tool_stats = []
        if not closed_df.empty and total>0:
            try:
                tool_df = pd.read_sql_query("""
                    SELECT entry_tool as tool, COUNT(*) as total,
                    SUM(CASE WHEN result='win' THEN 1 ELSE 0 END) as wins,
                    AVG(pnl_usd) as avg_pnl
                    FROM vt_trades WHERE status='closed'
                    GROUP BY entry_tool HAVING total>=2
                    ORDER BY avg_pnl DESC
                """, conn)
                for _,r in tool_df.iterrows():
                    t=int(r["total"]); w=int(r["wins"])
                    wr=round(float(w)/float(t)*100.0,1) if t>0 else 0.0
                    avg=round(float(r["avg_pnl"]) if r["avg_pnl"] else 0.0,2)
                    tool_stats.append({"tool":str(r["tool"]),"total":t,"wr":wr,"avg":avg})
            except: pass

        chart_labels=[]; chart_data=[]
        try:
            rep_df = pd.read_sql_query(
                "SELECT capital, report_time FROM vt_reports ORDER BY id ASC LIMIT 20", conn)
            if not rep_df.empty:
                chart_labels=[str(t)[:16] for t in rep_df["report_time"].tolist()]
                chart_data=[round(float(c),2) for c in rep_df["capital"].tolist()]
        except: pass
        if not chart_data:
            chart_labels=["الآن"]; chart_data=[capital]

        top_symbols=[
            {"symbol":"ANKR","pf":2.43,"wr":36.0,"tool":"rsi_low"},
            {"symbol":"KSM","pf":1.82,"wr":36.9,"tool":"rsi_bounce"},
            {"symbol":"COMP","pf":1.53,"wr":38.2,"tool":"bb_bounce"},
            {"symbol":"1INCH","pf":1.47,"wr":33.7,"tool":"vwap_cross"},
            {"symbol":"GRT","pf":1.46,"wr":35.8,"tool":"fib_50"},
            {"symbol":"TRX","pf":1.39,"wr":35.5,"tool":"fib_61.8"},
            {"symbol":"ALGO","pf":1.32,"wr":34.9,"tool":"high_volume"},
            {"symbol":"MKR","pf":1.30,"wr":35.5,"tool":"ema9_cross"},
            {"symbol":"AVAX","pf":1.29,"wr":35.5,"tool":"rsi_bounce"},
        ]

        return render_template_string(DASHBOARD_HTML,
            capital=f"{capital:,.2f}", win_rate=win_rate,
            total_trades=total, pnl_str=pnl_str,
            wins=wins, losses=losses, open_count=len(open_df) if not open_df.empty else 0,
            open_trades=open_df.to_dict("records") if not open_df.empty else [],
            closed_trades=closed_df.to_dict("records") if not closed_df.empty else [],
            tool_stats=tool_stats, top_symbols=top_symbols,
            chart_labels=str(chart_labels), chart_data=str(chart_data),
            now=datetime.now().strftime("%Y-%m-%d %H:%M")
        )
    except Exception as e:
        return f"<div style='background:#0a0a1a;color:white;padding:30px;direction:rtl'><h2 style='color:#ff6b6b'>خطأ: {str(e)}</h2><a href='/logout' style='color:#00d4ff'>خروج</a></div>"
    finally:
        conn.close()

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("="*55)
    print("  🌐 لوحة تحكم غالي التداولي")
    print(f"  افتح: http://localhost:{port}")
    print(f"  كلمة المرور: {PASSWORD}")
    print("="*55)
    app.run(debug=False, host="0.0.0.0", port=port)