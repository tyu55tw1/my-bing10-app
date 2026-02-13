import streamlit as st
import requests
import re
import itertools
import urllib3
import time
import urllib.parse
import google.generativeai as genai
from collections import Counter
from bs4 import BeautifulSoup

# 1. 基礎設定
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
st.set_page_config(
    page_title="Jarvis Web v24", 
    page_icon="🤖", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 🔑 安全金鑰讀取系統 (Security Core)
# ==========================================
# 程式會自動去 "保險箱" (Secrets) 找密碼
# 如果找不到 (例如在本機且沒設定)，會顯示警告但不會崩潰
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    status_indicator = "🟢 線上 (Secure)"
else:
    api_key = None
    status_indicator = "🔴 離線 (無金鑰)"

# ==========================================
# 🎨 CSS 戰情室風格
# ==========================================
st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: #e2e8f0; }
    /* 聊天輸入框置底 */
    .stChatInput { position: fixed; bottom: 0px; background: #0f172a; z-index: 1000; padding-bottom: 20px; }
    .block-container { padding-bottom: 120px; }
    
    /* 搜尋卡片樣式 */
    .search-card { 
        background: #1e293b; 
        padding: 15px; 
        border-radius: 10px; 
        border-left: 5px solid #3b82f6; 
        margin-bottom: 10px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        transition: transform 0.2s;
    }
    .search-card:hover { transform: translateY(-2px); }
    a { color: #60a5fa !important; text-decoration: none; font-weight: bold; font-size: 1.1em; }
    
    /* 側邊欄美化 */
    [data-testid="stSidebar"] { background-color: #111827; border-right: 1px solid #374151; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🧠 核心演算法 (移植自您的代碼)
# ==========================================

class WebSearcher:
    @staticmethod
    def decode_ddg_url(raw_url):
        try:
            if m := re.search(r'uddg=([^&]+)', raw_url): return urllib.parse.unquote(m.group(1))
            return raw_url if raw_url.startswith('http') else ""
        except: return ""

    @staticmethod
    def search_advanced(query, model):
        results_list = []
        snippets_text = []
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        
        # 1. Wiki
        try:
            res = requests.get("https://zh.wikipedia.org/w/api.php", params={"action":"query","format":"json","list":"search","srsearch":query,"srlimit":2}, timeout=3)
            for item in res.json().get("query",{}).get("search",[]):
                t, s = item["title"], re.sub(r'<[^>]+>','',item["snippet"])
                link = f"https://zh.wikipedia.org/wiki/{t}"
                results_list.append({"title":f"📚 {t}", "link":link, "snippet":s})
                snippets_text.append(f"Wiki: {t}-{s}")
        except: pass

        # 2. DuckDuckGo
        try:
            res = requests.get(f"https://html.duckduckgo.com/html/?q={query}", headers=headers, timeout=8)
            soup = BeautifulSoup(res.text, 'html.parser')
            for i, r in enumerate(soup.find_all('div', class_='result'), 1):
                if i > 6: break
                a = r.find('a', class_='result__a')
                s = r.find('a', class_='result__snippet')
                if a:
                    link = WebSearcher.decode_ddg_url(a['href'])
                    if link:
                        title = a.get_text(strip=True)
                        snip = s.get_text(strip=True) if s else ""
                        results_list.append({"title":title, "link":link, "snippet":snip})
                        snippets_text.append(f"Web: {title}-{snip}")
        except: pass
        
        # AI 總結
        raw_data = "\n".join(snippets_text[:5])
        ai_summary = "❌ 搜尋無結果。"
        if raw_data:
            if model:
                try: ai_summary = model.generate_content(f"根據以下資料回答『{query}』(重點即可)：\n{raw_data}").text
                except: ai_summary = f"**搜尋摘要**：\n{raw_data[:300]}..."
            else:
                ai_summary = f"**搜尋摘要**：\n{raw_data[:300]}..."
        elif not results_list:
            ai_summary = "❌ 找不到相關資料，請換個關鍵字。"

        return ai_summary, results_list

class LottoAlgorithm:
    @staticmethod
    def calculate_ac(n):
        r=len(n); d=set(); 
        for p in itertools.combinations(n,2): d.add(abs(p[0]-p[1]))
        return len(d)-(r-1)
    @staticmethod
    def is_prime(n):
        if n<2: return False
        for i in range(2,int(n**0.5)+1): 
            if n%i==0: return False
        return True
    @staticmethod
    def predict(t):
        if "大樂透" in t: mn,pk,ac=49,6,7
        elif "威力" in t: mn,pk,ac=38,6,7
        elif "539" in t: mn,pk,ac=39,5,4
        else: return "⚠️ 未知彩種", []
        primes=[x for x in range(1,mn+1) if LottoAlgorithm.is_prime(x)]
        best=None
        for _ in range(3000):
            c=sorted(random.sample(range(1,mn+1),pk))
            if LottoAlgorithm.calculate_ac(c)<ac: continue
            if not (1<=sum(1 for x in c if x in primes)<=3): continue
            best=c; break
        if not best: best=sorted(random.sample(range(1,mn+1),pk))
        sp = f" + 第二區 [{random.randint(1,8):02d}]" if "威力" in t else ""
        return f"🎰 **{t.replace('熱','樂')}**\n\n🔢 **{best}** {sp}\n📊 AC值: {LottoAlgorithm.calculate_ac(best)}", []

class LogicCore:
    @staticmethod
    def bingo(text):
        stars = 5
        # 中文數字轉換
        cn = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10}
        for k,v in cn.items(): 
            if k in text: stars = v
        if m := re.search(r'(\d+)\s*星', text): stars = int(m.group(1))
        
        try:
            res = requests.get("https://www.pilio.idv.tw/bingo/list.asp", headers={'User-Agent':'Mozilla/5.0'}, timeout=8, verify=False)
            res.encoding='big5'
            soup = BeautifulSoup(res.text, 'html.parser')
            nums = []
            for tr in soup.find_all('tr'):
                t = tr.get_text(strip=True)
                if re.search(r'11[0-9]\d{6}', t):
                    n = [int(x) for x in re.findall(r'\d+', t) if int(x)<=80][:20]
                    if len(n)==20: nums.extend(n)
            if not nums: return "❌ 來源阻擋", []
            hot = [n for n,c in Counter(nums).most_common(stars)]
            return f"🎱 **賓果 {stars} 星 (追熱)**\n\n🔥 推薦：**{sorted(hot)}**", []
        except: return "⚠️ 連線錯誤", []

    @staticmethod
    def stock(text):
        code = re.search(r'\d{4,6}', text).group(0)
        try:
            ts = int(time.time()*1000)
            res = requests.get(f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_{code}.tw|otc_{code}.tw&json=1&_={ts}", timeout=5, verify=False)
            d = res.json()
            if d['msgArray']:
                i = d['msgArray'][0]
                p = i.get('z','-'); p = i.get('b','-').split('_')[0] if p=='-' else p
                color = "red" if float(p) > float(i.get('y',0)) else "green"
                return f"📈 **{code} {i.get('n','')}**\n💰 現價：:{color}[{p}]\n📊 昨收：{i.get('y','-')}", []
            return "⚠️ 查無代碼", []
        except: return "⚠️ 股價忙線", []

# ==========================================
# 🧠 Jarvis 大腦 (Router)
# ==========================================
def jarvis_think(text, model):
    t = text.lower()
    
    # 1. 樂透
    if "大樂透" in t or "威力" in t or "539" in t:
        if "預測" in t or "算牌" in t:
            if "大樂透" in t: return LottoAlgorithm.predict("大樂透")
            if "威力" in t: return LottoAlgorithm.predict("威力彩")
            if "539" in t: return LottoAlgorithm.predict("539")
    
    # 2. 賓果
    if "賓果" in t or "星" in t: return LogicCore.bingo(t)
    
    # 3. 股票
    if "股" in t and re.search(r'\d{4,6}', t): return LogicCore.stock(t)
    
    # 4. 搜尋 (含天氣/新聞/查詢)
    search_triggers = ["時間","日期","新聞","報名","報考","多少","查","誰","天氣","收尋","搜尋"]
    if any(k in t for k in search_triggers) or (model and len(t)>4):
        return WebSearcher.search_advanced(text, model)
        
    # 5. 純閒聊
    if model:
        try: return model.generate_content(text).text, []
        except: pass
        
    return "🤖 請輸入明確指令 (如: 預測大樂透, 00919股價, 2026五專報名)", []

# ==========================================
# 🚀 介面啟動
# ==========================================

# 初始化 AI
model = None
if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
    except: status_indicator = "🔴 金鑰無效"

if "history" not in st.session_state: st.session_state.history = []
if "search_res" not in st.session_state: st.session_state.search_res = []

# 標題與狀態
c1, c2 = st.columns([8,2])
with c1: st.title("Jarvis Web")
with c2: st.caption(f"Status: {status_indicator}")

# 介面佈局：左側聊天 | 右側(或下方)資訊
col_chat, col_info = st.columns([2, 1])

with col_chat:
    chat_container = st.container(height=600)
    for role, txt in st.session_state.history:
        with chat_container.chat_message(role): st.markdown(txt)

with col_info:
    st.subheader("🌐 即時資訊流")
    if not st.session_state.search_res:
        st.info("尚無搜尋資料")
    else:
        for item in st.session_state.search_res:
            st.markdown(f"""
            <div class="search-card">
                <a href="{item['link']}" target="_blank">{item['title']}</a>
                <div style="color:#94a3b8;font-size:13px;margin-top:5px;">{item['snippet']}</div>
            </div>
            """, unsafe_allow_html=True)

# 輸入處理
if prompt := st.chat_input("請輸入指令..."):
    st.session_state.history.append({"role": "user", "content": prompt})
    with chat_container.chat_message("user"): st.write(prompt)
    
    with chat_container.chat_message("assistant"):
        if not model and "搜尋" not in prompt and "賓果" not in prompt:
             # 如果沒金鑰，還是允許跑非 AI 的功能(如賓果)，但 AI 功能會擋
             pass
        
        with st.spinner("Jarvis 運算中..."):
            reply, res = jarvis_think(prompt, model)
            st.markdown(reply)
            
    st.session_state.search_res = res
    st.session_state.history.append({"role": "assistant", "content": reply})
    st.rerun()