import streamlit as st
from langdetect import detect_langs
import langid
from googletrans import Translator
import PyPDF2
import docx
from gtts import gTTS
from gtts.lang import tts_langs
import tempfile

# ----------------------------
# Language codes to names
# ----------------------------
LANG_MAP = {
    'en': 'English', 'hi': 'Hindi', 'bn': 'Bengali', 'es': 'Spanish',
    'fr': 'French', 'de': 'German', 'ar': 'Arabic', 'ru': 'Russian',
    'ja': 'Japanese', 'ko': 'Korean', 'it': 'Italian', 'pt': 'Portuguese',
    'ur': 'Urdu', 'zh-cn': 'Chinese (Simplified)', 'zh-tw': 'Chinese (Traditional)'
}

# ----------------------------
# Page Config (must be first)
# ----------------------------
st.set_page_config(page_title="Language Detector & Translator", page_icon="🈶", layout="wide")



st.title("🌍 Language Detector & Translator")

translator = Translator()

# ----------------------------
# Input Options
# ----------------------------
st.write("### ✍️ Choose Input Type")
input_choice = st.radio("Select one:", ["Paste Text", "Upload File"])

text = ""

if input_choice == "Paste Text":
    text = st.text_area("Paste text here", "Bonjour tout le monde!", height=200)

elif input_choice == "Upload File":
    uploaded_file = st.file_uploader("📂 Upload a document", type=["txt", "pdf", "docx"])
    if uploaded_file is not None:
        try:
            if uploaded_file.type == "text/plain":
                text = uploaded_file.read().decode("utf-8")
            elif uploaded_file.type == "application/pdf":
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                chunks = []
                for page in pdf_reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        chunks.append(extracted)
                text = "\n".join(chunks).strip()
            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                doc = docx.Document(uploaded_file)
                text = "\n".join([para.text for para in doc.paragraphs]).strip()
        except Exception as e:
            st.error(f"❌ Failed to read file: {e}")

# ----------------------------
# Detection & Translation Settings
# ----------------------------
col1, col2, col3 = st.columns(3)

with col1:
    detector_choice = st.selectbox("🕵️ Detection Method", ["Auto Detect", "langdetect (fast)", "langid (robust)"])

with col2:
    # Avoid relying on max_selections (not available in older Streamlit)
    target_langs = st.multiselect("🌐 Translate to (pick up to 3)", list(LANG_MAP.values()), default=["English"])
    if len(target_langs) > 3:
        st.warning("⚠️ You selected more than 3 languages. Only the first 3 will be used.")
        target_langs = target_langs[:3]

with col3:
    show_audio = st.checkbox("🔊 Speak Translation", value=True)

# Precompute gTTS supported codes (for audio)
gtts_supported = tts_langs()  # dict like {'en': 'English', 'hi': 'Hindi', ...}

# ----------------------------
# Action Button
# ----------------------------
if st.button("🚀 Detect & Translate"):
    if not text or not text.strip():
        st.warning("⚠️ Please enter or upload some text.")
    else:
        detected_code = None

        # ------- Language Detection -------
        try:
            if detector_choice == "langdetect (fast)":
                candidates = detect_langs(text)
                top = candidates[0]
                detected_code = top.lang
                confidence = top.prob if top.prob is not None else 0.0
                st.subheader("🕵️ Detected Language")
                st.info(f"**{LANG_MAP.get(top.lang, top.lang)}** — confidence: **{confidence:.2f}**")

            elif detector_choice == "langid (robust)":
                code, score = langid.classify(text)
                detected_code = code
                # score is a float from langid; still guard just in case
                try:
                    score_fmt = f"{float(score):.2f}"
                except Exception:
                    score_fmt = "unknown"
                st.subheader("🕵️ Detected Language")
                st.info(f"**{LANG_MAP.get(code, code)}** — score: **{score_fmt}**")

            else:  # Auto Detect via googletrans
                detection = translator.detect(text)
                detected_code = getattr(detection, "lang", None)
                raw_conf = getattr(detection, "confidence", None)
                confidence = float(raw_conf) if raw_conf is not None else 0.0
                shown_name = LANG_MAP.get(detected_code, detected_code or "unknown")
                st.subheader("🕵️ Detected Language (Auto)")
                st.info(f"**{shown_name}** — confidence: **{confidence:.2f}**")

        except Exception as e:
            st.error(f"❌ Language detection failed: {e}")
            detected_code = None

        # ------- Translation -------
        if detected_code:
            for lang_name in target_langs:
                target_code = next((k for k, v in LANG_MAP.items() if v == lang_name), None)
                if not target_code:
                    st.error(f"❌ Could not map target language '{lang_name}'.")
                    continue

                try:
                    with st.spinner(f"Translating to {lang_name}..."):
                        translation = translator.translate(text, src=detected_code, dest=target_code)

                    st.subheader(f"➡️ Translation to {lang_name}")
                    st.success(translation.text)

                    # ---- Speak Translation (only if supported by gTTS) ----
                    if show_audio:
                        if target_code in gtts_supported:
                            try:
                                tts = gTTS(translation.text, lang=target_code)
                                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                                    tts.save(tmp.name)
                                    st.audio(tmp.name, format="audio/mp3")
                            except Exception as tts_err:
                                st.info(f"🔈 Unable to generate audio for {lang_name}: {tts_err}")
                        else:
                            st.info(f"🔈 Audio not available for {lang_name} (unsupported by gTTS).")

                except Exception as e:
                    st.error("❌ Translation error: " + str(e))
        else:
            st.warning("⚠️ Could not determine the source language. Try a different detection method or longer text.")
