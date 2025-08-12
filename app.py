import re
import requests
import pandas as pd
import streamlit as st
from urllib.parse import urlparse
import json

st.set_page_config(page_title="M3U Player (Streamlit)", page_icon="📺", layout="wide")

ATTR_RE = re.compile(r'(\w[\w-]*?)="([^"]*)"')

def parse_m3u(text: str) -> pd.DataFrame:
    lines = text.splitlines()
    data = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF"):
            info = line
            j = i + 1
            while j < len(lines) and (lines[j].strip() == "" or lines[j].startswith("#")):
                j += 1
            url = lines[j].strip() if j < len(lines) else ""
            attrs = dict((m[0].lower(), m[1]) for m in ATTR_RE.findall(info))
            name = info.split(",")[-1].strip() if "," in info else attrs.get("tvg-name", "Sem nome")
            data.append({
                "name": name or attrs.get("tvg-name") or "Sem nome",
                "url": url,
                "group": attrs.get("group-title", ""),
                "logo": attrs.get("tvg-logo", ""),
                "tvg_id": attrs.get("tvg-id", ""),
                "raw": info + "\n" + url
            })
            i = j + 1
        else:
            i += 1
    df = pd.DataFrame(data)
    if not df.empty:
        df = df.drop_duplicates(subset=["url"])
    return df

def fetch_text_from_url(url: str, timeout: int = 20) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }
    r = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
    r.raise_for_status()
    if "text" in r.headers.get("content-type","") or r.content.startswith(b"#EXTM3U"):
        return r.text
    return r.content.decode("utf-8", errors="ignore")

def hls_player(url: str, height: int = 480):
    import streamlit.components.v1 as components
    html = f"""
    <div id=\"app\" style=\"width:100%;\">
      <video id=\"video\" controls autoplay playsinline style=\"width:100%; height:{height}px; background:#000; border-radius:12px;\"></video>
    </div>
    <script src=\"https://cdn.jsdelivr.net/npm/hls.js@1.5.13/dist/hls.min.js\"></script>
    <script>
      const url = {json.dumps(url)};
      const video = document.getElementById('video');
      function canPlayNative() {{ return video.canPlayType('application/vnd.apple.mpegurl'); }}
      if (url.endsWith('.m3u8') || url.includes('m3u8')) {{ 
        if (window.Hls && !canPlayNative()) {{ 
          const hls = new Hls({{maxBufferLength: 30}}); 
          hls.loadSource(url); hls.attachMedia(video);
        }} else {{ video.src = url; }}
      }} else {{
        video.src = url;
      }}
    </script>
    """
    components.html(html, height=height+16, scrolling=False)

st.title("Leitor M3U — Streamlit")
st.sidebar.title("📺 Entrada")

uploaded = st.sidebar.file_uploader("Ficheiro .m3u/.m3u8", type=["m3u","m3u8","txt"])
url_input = st.sidebar.text_input("URL da playlist (.m3u/.m3u8)")
fetch_btn = st.sidebar.button("Carregar URL")
demo_btn = st.sidebar.button("Usar exemplo HLS")

df = pd.DataFrame()
error = None

try:
    if uploaded is not None:
        text = uploaded.read().decode("utf-8", errors="ignore")
        df = parse_m3u(text)
    elif fetch_btn and url_input:
        text = fetch_text_from_url(url_input)
        if text.strip().startswith("#EXTM3U"):
            df = parse_m3u(text)
        else:
            df = pd.DataFrame([{"name":"Stream direto","url":url_input,"group":"","logo":"","tvg_id":"","raw":url_input}])
    elif demo_btn:
        df = pd.DataFrame([{"name":"Big Buck Bunny (HLS)","url":"https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8","group":"Demo","logo":"","tvg_id":"","raw":""}])
except Exception as e:
    error = str(e)

left, right = st.columns([2,1])
with left:
    st.subheader("Player")
    current = st.session_state.get("current_url")
    if current:
        hls_player(current, height=500)
        st.caption(current)
    else:
        st.info("Carrega um ficheiro .m3u ou usa um URL para começar.")

with right:
    st.subheader("Canais")
    if error:
        st.error(f"Erro ao carregar: {error}")
    if df.empty:
        st.write("Sem lista carregada ainda.")
    else:
        q = st.text_input("Pesquisar", "")
        groups = ["Todos"] + sorted([g for g in df["group"].dropna().unique() if g])
        gsel = st.selectbox("Grupo", groups, index=0)
        filtered = df.copy()
        if q:
            ql = q.lower()
            filtered = filtered[filtered["name"].str.lower().str.contains(ql) | filtered["group"].str.lower().str.contains(ql)]
        if gsel != "Todos":
            filtered = filtered[filtered["group"] == gsel]
        st.dataframe(filtered[["name","group","url"]], use_container_width=True, hide_index=True)
        opts = (filtered["name"] + " — " + filtered["url"]).tolist()
        pick = st.selectbox("Escolhe um canal", opts if opts else ["(nenhum)"])
        if opts and pick:
            st.session_state["current_url"] = pick.split(" — ", 1)[1]
            st.success("Canal selecionado.")    
