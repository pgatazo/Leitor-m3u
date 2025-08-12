# Leitor M3U — Streamlit

Leitor simples de playlists M3U com player HLS (hls.js) para testar no Streamlit Cloud.

## Local
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy no Streamlit Community Cloud
1. Suba estes ficheiros para um repositório no GitHub.
2. Vá a https://share.streamlit.io → **New app**.
3. Selecione o repositório/branch e defina o `app.py` como entrypoint.
4. Deploy.

> Nota: Para **playback**, os streams precisam permitir reprodução no browser.
