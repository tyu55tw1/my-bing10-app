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

# ==========================================
# 🔑 API 金鑰 (自動切換)
# ==========================================
# 1. 先嘗試讀取雲端設定
# 2. 如果失敗，使用您提供的備用金鑰
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    GEMINI_API_KEY = "AIzaSyACLssBFMWfLpIprNmx7TdQe_k4k4JCLEM"

# ==========================================
# 📱 頁面設定 (隱藏選單，全螢幕感)
# ==========================================
st.set_page_config(
    page_title="Jarvis Mobile",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS 優化：隱藏多餘元素，優化手機閱讀
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stChatInput {
        position: fixed;
        bottom: 0px;
        background-color: white;
        padding-bottom: 15px;
        z-index: 999;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 6rem;
    }
    .search-card {
        background-color: #262730;
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 10px;
        border: 1px solid #444;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    a {text-decoration: none; color: #4da6ff !important; font-weight: bold; font-size: 16px;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 🧠 核心邏輯
# ==========================================
class WebSearcher:
    @staticmethod
    def decode_ddg_url(raw_url):
        try:
            if raw_data := re.search(r'uddg=([^&]+)', raw_url):
                return urllib.parse.unquote(raw_data.group(1))
            return raw_url if raw_url.startswith('http') else ""
        except: return ""

    @staticmethod
    def search_web(query):
        """搜尋功能 (即使 AI 離線也能運作)"""
        results_list = []
        snippets_text = []
        # 使用手機 User-Agent 模擬
        headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'}
        
        # 1. 維基百科
        try:
            res = requests.get("https://zh.wikipedia.org/w/api.php", params={"action":"query","format":"json","list":"search","srsearch":query,"srlimit":2}, timeout=5)
            for item in res.json().get("query",{}).get("search",[]):
                t = item["title"]; s = re.sub(r'<[^>]+>','',item["snippet"])
                results_list.append({"title":f"📚 {t}","link":f"https://zh.wikipedia.org/wiki/{t}","snippet":s})
                snippets_text.append(f"Wiki: {t}-{s}")
        except: pass

        # 2. DuckDuckGo
        try:
            res = requests.get(f"https://html.duckduckgo.com/html/?q={query}", headers=headers, timeout=8)
            soup = BeautifulSoup(res.text, 'html.parser')
            for i, r in enumerate(soup.find_all('div', class_='result'), 1):
                if i>6: break
                ta = r.find('a', class_='result__a'); sa = r.find('a', class_='result__snippet')
                if ta:
                    t = ta.get_text(strip=True)
                    l = WebSearcher.decode_ddg_url(ta['href'])
                    s = sa.get_text(strip=True) if sa else ""
                    if l: results_list.append({"title":t,"link":l,"snippet":s}); snippets_text.append(f"{t}-{s}")
        except: pass
        
        # 就算沒找到 AI 摘要，也要回傳列表
        return results_list, "\n".join(snippets_text[:6])

class LottoAlgorithm:
    # ... (樂透算法保持不變) ...
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
        else: return "⚠️ 未知", []
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

class BingoAlgorithm:
    @staticmethod
    def analyze_and_predict(stars=5):
        try:
            # 使用電腦版 UA 以防被擋
            res = requests.get("https://www.pilio.idv.tw/bingo/list.asp", headers={'User-Agent':'Mozilla/5.0'}, timeout=10, verify=False)
            res.encoding='big5'
            soup = BeautifulSoup(res.text, 'html.parser')
            nums = []
            for tr in soup.find_all('tr'):
                t = tr.get_text(strip=True)
                # 兼容 113, 114 年
                if re.search(r'11[3-9]\d{6}', t):
                    n = [int(x) for x in re.findall(r'\d+', t) if int(x)<=80][:20]
                    if len(n)==20: nums.extend(n)
            if not nums: return "❌ 來源阻擋", []
            hot = [n for n,c in Counter(nums).most_common(stars)]
            return f"🎱 **賓果 {stars} 星 (追熱)**\n\n🔥 推薦：**{sorted(hot)}**", []
        except: return "⚠️ 連線錯誤", []

class DirectInfo:
    @staticmethod
    def get_stock(code):
        try:
            ts = int(time.time()*1000)
            res = requests.get(f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_{code}.tw|otc_{code}.tw&json=1&_={ts}", timeout=5, verify=False)
            d = res.json()
            if d['msgArray']:
                i = d['msgArray'][0]
                p = i.get('z','-'); p = i.get('b','-').split('_')[0] if p=='-' else p
                color = "red" if float(p) > float(i.get('y',0)) else "green"
                return f"📈 **{code} {i.get('n','')}**\n💰 現價：:{color}[{p}]\n📊 昨收：{i.get('y','-')}", []
            return "⚠️ 查無", []
        except: return "⚠️ 忙線", []

# 腦袋與邏輯
def get_model():
    try:
        if not GEMINI_API_KEY: return None, "無金鑰"
        genai.configure(api_key=GEMINI_API_KEY)
        # 嘗試列出模型，確認金鑰有效
        list(genai.list_models())
        return genai.GenerativeModel('gemini-1.5-flash'), "線上"
    except: return None, "離線 (金鑰無效或額度滿)"

def jarvis_think(txt, model):
    txt = txt.lower()
    
    # 🟢 修正 1: 賓果星數 (加入中文數字判斷)
    if "賓果" in txt or "星" in txt:
        s = 5
        # 先抓阿拉伯數字 (如 3星)
        if m := re.search(r'(\d+)\s*星', txt): s = int(m.group(1))
        # 再抓中文數字 (如 三星)，優先權高
        cn = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10}
        for k,v in cn.items(): 
            if k in txt: s = v
        return BingoAlgorithm.analyze_and_predict(s)
    
    if "股" in txt and (m:=re.search(r'\d{4,6}', txt)): return DirectInfo.get_stock(m.group(0))
    
    # 搜尋與閒聊
    search_keys = ["時間","日期","新聞","報名","報考","多少","查","誰","天氣"]
    if any(k in txt for k in search_keys) or (model and len(txt)>4):
        res, raw = WebSearcher.search_web(txt)
        ans = "🔍 搜尋完畢 (AI 離線，請看下方連結)"
        
        # 🟢 修正 2: 如果 AI 活著，才讓他總結；死掉就回傳固定文字
        if model and raw:
            try: 
                ans = model.generate_content(f"基於以下資料回答'{txt}'，簡短即可：\n{raw}").text
            except: 
                ans = "⚠️ AI 回應失敗，請直接點擊下方連結。"
        elif not res:
            ans = "❌ 找不到相關資料"
            
        return ans, res
    
    if model:
        try: return model.generate_content(txt).text, []
        except: pass
    
    return "🤖 請輸入指令 (或 AI 目前離線)", []

# === 介面啟動 ===
if "model" not in st.session_state:
    m, status = get_model()
    st.session_state.model = m
    st.session_state.status = status

if "msgs" not in st.session_state: st.session_state.msgs = []
if "res" not in st.session_state: st.session_state.res = []

st.title(f"🤖 Jarvis ({st.session_state.status})")

# 聊天顯示區
for role, txt in st.session_state.msgs:
    with st.chat_message(role): st.markdown(txt)

# 搜尋結果區 (置底顯示)
if st.session_state.res:
    st.markdown("---")
    st.caption("🌐 相關資訊 (點擊開啟)")
    for item in st.session_state.res:
        st.markdown(f"""
        <div class="search-card">
            <a href="{item['link']}" target="_blank">{item['title']}</a>
            <div style="color:#bbb;font-size:12px;margin-top:4px;">{item['snippet'][:60]}...</div>
        </div>
        """, unsafe_allow_html=True)

# 輸入區
if prompt := st.chat_input("輸入指令..."):
    st.session_state.msgs.append(("user", prompt))
    st.rerun()

# 處理回應
if st.session_state.msgs and st.session_state.msgs[-1][0] == "user":
    user_txt = st.session_state.msgs[-1][1]
    with st.chat_message("assistant"):
        with st.spinner("..."):
            ans, res = jarvis_think(user_txt, st.session_state.model)
            st.markdown(ans)
    st.session_state.msgs.append(("assistant", ans))
    st.session_state.res = res
    st.rerun()