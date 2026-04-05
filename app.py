import streamlit as st
import os
import google.generativeai as genai
from dotenv import load_dotenv, set_key
from pathlib import Path
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from pdf_analyzer import PDFAnalyzer

load_dotenv()

ENV_FILE = Path(__file__).parent / ".env"

# ── Model emoji helper ─────────────────────────────────────────────────────────
def _model_emoji(name: str) -> str:
    n = name.lower()
    if "2.5-flash" in n and "lite" not in n: return "⚡"
    if "2.5-pro"   in n: return "🧠"
    if "2.5"       in n: return "🪶"
    if "3.1-pro"   in n: return "🧠"
    if "3.1"       in n: return "🪶"
    if "3-flash"   in n or "3-pro" in n: return "🚀"
    if "2.0-flash" in n: return "✨"
    if "gemma-4"   in n: return "💎"
    if "gemma-3"   in n: return "💎"
    return "🤖"

def fetch_models_from_api(api_key: str) -> dict:
    """API'dan generateContent destekleyen text modellerini çeker."""
    try:
        genai.configure(api_key=api_key)
        result = {}
        skip = ["tts", "image", "video", "veo", "imagen", "audio", "live",
                "embedding", "retrieval", "vision", "aqa", "nano-banana",
                "lyria", "robotics", "computer-use", "deep-research"]
        for m in genai.list_models():
            if "generateContent" not in (m.supported_generation_methods or []):
                continue
            name = m.name.replace("models/", "")
            if any(k in name.lower() for k in skip):
                continue
            result[name] = f"{_model_emoji(name)} {m.display_name}"
        return result or {}
    except Exception as e:
        return {"_error": str(e)}

def save_api_key_to_env(key: str):
    ENV_FILE.touch(exist_ok=True)
    set_key(str(ENV_FILE), "GOOGLE_API_KEY", key)
    load_dotenv(override=True)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Documentor – PDF AI Analyst",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp {
    background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
    color: #e2e8f0;
}
#MainMenu, footer, header { visibility: hidden; }

[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.03);
    border-right: 1px solid rgba(255,255,255,0.08);
    backdrop-filter: blur(10px);
}
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }

.main-header { text-align: center; padding: 2rem 0 1rem; }
.main-header h1 {
    font-size: 2.5rem; font-weight: 700;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 0.3rem;
}
.main-header p { color: #94a3b8; font-size: 1rem; }

.chat-container {
    max-height: 62vh; overflow-y: auto; padding: 1rem 0;
    scrollbar-width: thin; scrollbar-color: rgba(102,126,234,0.4) transparent;
}
.message-row { display: flex; margin-bottom: 1.2rem; animation: fadeSlide 0.3s ease-out; }
@keyframes fadeSlide {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
}
.message-row.user { justify-content: flex-end; }
.message-row.bot  { justify-content: flex-start; }
.avatar {
    width: 38px; height: 38px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem; flex-shrink: 0;
}
.avatar.user { background: linear-gradient(135deg,#667eea,#764ba2); margin-left: 10px; order: 2; }
.avatar.bot  { background: linear-gradient(135deg,#f093fb,#f5576c); margin-right: 10px; }
.bubble {
    max-width: 72%; padding: 0.85rem 1.1rem; border-radius: 18px;
    font-size: 0.92rem; line-height: 1.6; word-wrap: break-word;
}
.bubble.user {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: #fff; border-bottom-right-radius: 4px;
}
.bubble.bot {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.1);
    color: #e2e8f0; border-bottom-left-radius: 4px;
}

.stTextInput > div > div > input,
.stTextArea  > div > div > textarea {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 14px !important; color: #e2e8f0 !important;
    font-family: 'Inter', sans-serif !important; font-size: 0.95rem !important;
}
.stTextInput > div > div > input:focus,
.stTextArea  > div > div > textarea:focus {
    border-color: rgba(102,126,234,0.7) !important;
    box-shadow: 0 0 0 3px rgba(102,126,234,0.15) !important;
}

.stButton > button {
    background: linear-gradient(135deg,#667eea,#764ba2) !important;
    color: white !important; border: none !important;
    border-radius: 12px !important; padding: 0.55rem 1.4rem !important;
    font-weight: 600 !important; font-family: 'Inter', sans-serif !important;
    box-shadow: 0 4px 15px rgba(102,126,234,0.3) !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(102,126,234,0.45) !important;
}

.stat-card {
    background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px; padding: 1rem; text-align: center; transition: all 0.2s;
}
.stat-card:hover {
    background: rgba(255,255,255,0.08); border-color: rgba(102,126,234,0.4);
    transform: translateY(-2px);
}
.stat-value {
    font-size: 1.6rem; font-weight: 700;
    background: linear-gradient(135deg,#667eea,#f093fb);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.stat-label { font-size: 0.78rem; color: #64748b; margin-top: 0.2rem; }

.gradient-divider {
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(102,126,234,0.5), transparent);
    border: none; margin: 1rem 0;
}

::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(102,126,234,0.4); border-radius: 10px; }

[data-testid="stExpander"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 12px !important;
}

.badge { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
.badge-green { background: rgba(52,211,153,0.15); color: #34d399; border: 1px solid rgba(52,211,153,0.3); }
.badge-blue  { background: rgba(102,126,234,0.15); color: #818cf8; border: 1px solid rgba(102,126,234,0.3); }
</style>
""", unsafe_allow_html=True)


# ── Session state ──────────────────────────────────────────────────────────────
def init_session():
    defaults = {
        "messages":        [],
        "analyzer":        None,
        "file_name":       None,
        "api_key_set":     False,
        "selected_model":  "gemini-2.5-flash-preview-04-17",
        "key_just_saved":  False,
        "available_models": {},
        "models_loaded":   False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()


# ── Render chat ────────────────────────────────────────────────────────────────
def render_chat():
    if not st.session_state.messages:
        st.markdown("""
        <div style='text-align:center; padding:3rem 0; color:#475569;'>
            <div style='font-size:3rem;'>💬</div>
            <div style='margin-top:0.5rem; font-size:0.95rem;'>
                Bir PDF dosyası yükle ve analiz etmemi iste!
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    html = '<div class="chat-container">'
    for msg in st.session_state.messages:
        role    = msg["role"]
        content = msg["content"].replace("\n", "<br>")
        if role == "user":
            html += f"""
            <div class="message-row user">
                <div class="bubble user">{content}</div>
                <div class="avatar user">👤</div>
            </div>"""
        else:
            html += f"""
            <div class="message-row bot">
                <div class="avatar bot">🤖</div>
                <div class="bubble bot">{content}</div>
            </div>"""
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# ── AI response ────────────────────────────────────────────────────────────────
def get_ai_response(user_input: str, api_key: str) -> str:
    try:
        llm = ChatGoogleGenerativeAI(
            model=st.session_state.selected_model,
            google_api_key=api_key,
            temperature=0.7,
        )

        system_prompt = (
            "Sen Documentor adında profesyonel bir belge analizi asistanısın.\n"
            "Kullanıcının yüklediği PDF dosyalarını analiz eder, özetler çıkarır,\n"
            "içgörüler üretir ve net, anlaşılır raporlar oluşturursun.\n"
            "Türkçe ve/veya İngilizce sorulara yanıt verebilirsin.\n"
            "Yanıtların kısa, net ve eyleme dönüştürülebilir olsun.\n"
            "Gerektiğinde markdown formatı kullan ama HTML tag'i kullanma."
        )

        if st.session_state.analyzer:
            ctx = st.session_state.analyzer.get_context_summary()
            system_prompt += f"\n\nMevcut PDF verisi:\n{ctx}"

        messages = [SystemMessage(content=system_prompt)]
        for m in st.session_state.messages[-10:]:
            if m["role"] == "user":
                messages.append(HumanMessage(content=m["content"]))
            else:
                messages.append(AIMessage(content=m["content"]))
        messages.append(HumanMessage(content=user_input))

        response = llm.invoke(messages)
        return response.content

    except Exception as e:
        return f"❌ Hata: {str(e)}"


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding:1.2rem 0 0.5rem;'>
        <div style='font-size:2.5rem;'>📄</div>
        <div style='font-weight:700; font-size:1.15rem; color:#e2e8f0;'>Documentor</div>
        <div style='font-size:0.75rem; color:#64748b; margin-top:2px;'>PDF AI Analyst</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    # ── API Key ────────────────────────────────────────────────────────────────
    st.markdown("##### 🔑 Gemini API Key")
    env_key       = os.getenv("GOOGLE_API_KEY", "")
    env_key_valid = bool(env_key and env_key != "your_gemini_api_key_here")

    if env_key_valid:
        api_key = env_key
        st.session_state.api_key_set = True
        if st.session_state.key_just_saved:
            st.success("✅ .env'e kaydedildi!")
            st.session_state.key_just_saved = False
        else:
            st.markdown('<span class="badge badge-green">✓ .env\'den yüklendi</span>',
                        unsafe_allow_html=True)
        with st.expander("🔄 Key'i güncelle"):
            new_key = st.text_input("Yeni API Key", type="password",
                                    placeholder="AIza...", key="update_key_input")
            if st.button("💾 Güncelle ve Kaydet", key="update_save_btn"):
                if new_key.strip():
                    save_api_key_to_env(new_key.strip())
                    st.session_state.key_just_saved = True
                    st.session_state.models_loaded  = False
                    st.rerun()
    else:
        api_key_input = st.text_input("API Key", type="password", placeholder="AIza...",
                                      label_visibility="collapsed", key="api_key_input")
        if api_key_input:
            api_key = api_key_input
            st.session_state.api_key_set = True
            col_b, col_s = st.columns(2)
            with col_b:
                st.markdown('<span class="badge badge-green">✓ Girildi</span>',
                            unsafe_allow_html=True)
            with col_s:
                if st.button("💾 .env'e Kaydet", key="save_key_btn",
                             use_container_width=True):
                    save_api_key_to_env(api_key_input.strip())
                    st.session_state.key_just_saved = True
                    st.session_state.models_loaded  = False
                    st.rerun()
        else:
            api_key = ""
            st.markdown('<span class="badge badge-blue">⚠ Gerekli</span>',
                        unsafe_allow_html=True)

    st.divider()

    # ── Model Selector ─────────────────────────────────────────────────────────
    st.markdown("##### 🤖 Model Seçimi")

    if st.session_state.api_key_set and not st.session_state.models_loaded:
        with st.spinner("🔄 Modeller yükleniyor..."):
            fetched = fetch_models_from_api(api_key)
            if "_error" not in fetched and fetched:
                st.session_state.available_models = fetched
                st.session_state.models_loaded    = True
                if st.session_state.selected_model not in fetched:
                    st.session_state.selected_model = next(iter(fetched))

    model_map = st.session_state.available_models

    if not model_map:
        st.markdown('<span class="badge badge-blue">⏳ API key girilince yüklenir</span>',
                    unsafe_allow_html=True)
    else:
        model_keys   = list(model_map.keys())
        model_labels = list(model_map.values())
        cur_idx      = model_keys.index(st.session_state.selected_model) \
                       if st.session_state.selected_model in model_keys else 0
        chosen = st.selectbox("Model", options=model_labels, index=cur_idx,
                              label_visibility="collapsed", key="model_selectbox")
        st.session_state.selected_model = model_keys[model_labels.index(chosen)]
        st.markdown(f'<span style="font-size:0.72rem;color:#475569;">📶 {len(model_map)} model mevcut</span>',
                    unsafe_allow_html=True)
        if st.button("🔄 Listeyi Yenile", key="refresh_models", use_container_width=True):
            st.session_state.models_loaded = False
            st.rerun()

    st.divider()

    # ── PDF Upload ─────────────────────────────────────────────────────────────
    st.markdown("##### 📂 PDF Dosyası")
    uploaded_file = st.file_uploader(
        "PDF yükle", type=["pdf"],
        label_visibility="collapsed", key="file_uploader",
    )

    if uploaded_file:
        if uploaded_file.name != st.session_state.file_name:
            with st.spinner("📖 PDF okunuyor..."):
                try:
                    file_bytes = uploaded_file.read()
                    analyzer   = PDFAnalyzer(file_bytes, uploaded_file.name)
                    st.session_state.analyzer  = analyzer
                    st.session_state.file_name = uploaded_file.name
                    welcome = analyzer.generate_welcome_message()
                    st.session_state.messages.append({"role": "assistant", "content": welcome})
                    st.rerun()
                except Exception as e:
                    st.error(f"PDF okunamadı: {e}")

    if st.session_state.analyzer:
        a = st.session_state.analyzer
        st.markdown(f"**📄 {st.session_state.file_name}**")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""<div class="stat-card">
                <div class="stat-value">{a.page_count}</div>
                <div class="stat-label">Sayfa</div></div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class="stat-card">
                <div class="stat-value">{a.word_count:,}</div>
                <div class="stat-label">Kelime</div></div>""", unsafe_allow_html=True)

    st.divider()

    # ── Quick Prompts ──────────────────────────────────────────────────────────
    st.markdown("##### ⚡ Hızlı Sorgular")
    quick_prompts = [
        ("📋 Özet çıkar",              "Bu PDF'i kısa ve öz şekilde özetle"),
        ("🔑 Anahtar noktalar",        "Belgedeki en önemli noktaları listele"),
        ("📈 Sayısal veriler",          "Belgedeki tüm sayısal verileri ve istatistikleri çıkar"),
        ("❓ Soru & Cevap",            "Bu belgeden 5 önemli soru ve cevap oluştur"),
        ("📝 Kapsamlı rapor",          "Bu belge için profesyonel bir rapor oluştur"),
        ("🌐 İngilizce'ye çevir",      "Bu belgeyi İngilizce'ye çevir"),
    ]
    for label, prompt in quick_prompts:
        if st.button(label, use_container_width=True, key=f"qp_{label}"):
            if not st.session_state.api_key_set:
                st.warning("Önce API key girin!")
            elif not st.session_state.analyzer:
                st.warning("Önce PDF yükleyin!")
            else:
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.spinner("🤔 Düşünüyor..."):
                    resp = get_ai_response(prompt, api_key)
                st.session_state.messages.append({"role": "assistant", "content": resp})
                st.rerun()

    st.divider()
    if st.button("🗑 Sohbeti Temizle", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="main-header">
    <h1>📄 Documentor</h1>
    <p>PDF dosyalarınızı AI ile analiz edin, özetleyin ve raporlayın</p>
</div>
<hr class="gradient-divider">
""", unsafe_allow_html=True)

# ── PDF Preview ────────────────────────────────────────────────────────────────
if st.session_state.analyzer:
    with st.expander("📖 İçerik Önizleme (ilk 1500 karakter)", expanded=False):
        st.text(st.session_state.analyzer.preview()[:1500])

# ── Chat ───────────────────────────────────────────────────────────────────────
render_chat()

st.markdown("<hr class='gradient-divider'>", unsafe_allow_html=True)

# ── Input (form → clear_on_submit prevents rerun loop) ────────────────────────
with st.form(key="chat_form", clear_on_submit=True):
    col_in, col_send = st.columns([8, 1])
    with col_in:
        user_input = st.text_input(
            "Mesajınız",
            placeholder="PDF hakkında bir şey sorun… (örn: bu belgenin özeti nedir?)",
            label_visibility="collapsed",
        )
    with col_send:
        send_clicked = st.form_submit_button("➤", use_container_width=True)

if send_clicked and user_input.strip():
    if not st.session_state.api_key_set:
        st.warning("⚠️ Lütfen önce sol panelden Gemini API Key girin.")
    elif not st.session_state.analyzer:
        st.warning("⚠️ Lütfen önce sol panelden bir PDF dosyası yükleyin.")
    else:
        st.session_state.messages.append({"role": "user", "content": user_input.strip()})
        with st.spinner("🤔 Düşünüyor..."):
            resp = get_ai_response(user_input.strip(), api_key)
        st.session_state.messages.append({"role": "assistant", "content": resp})
        st.rerun()
