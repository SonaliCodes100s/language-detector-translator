import streamlit as st
from langdetect import detect_langs
import langid
from googletrans import Translator

# Language codes to names
LANG_MAP = {
    'en': 'English', 'hi': 'Hindi', 'bn': 'Bengali', 'es': 'Spanish',
    'fr': 'French', 'de': 'German', 'ar': 'Arabic', 'ru': 'Russian',
    'ja': 'Japanese', 'ko': 'Korean', 'it': 'Italian', 'pt': 'Portuguese',
    'ur': 'Urdu', 'zh-cn': 'Chinese (Simplified)', 'zh-tw': 'Chinese (Traditional)'
}

st.set_page_config(page_title="Language Detector & Translator", page_icon="🈶")
st.title("Language Detector & Translator 🈶")

text = st.text_area("Paste text here", height=200)

col1, col2 = st.columns(2)
with col1:
    detector_choice = st.selectbox("Detection Method", ["langdetect (fast)", "langid (robust)"])
with col2:
    target_lang = st.selectbox("Translate to", list(LANG_MAP.values()))

translator = Translator()

if st.button("Detect & Translate"):
    if not text.strip():
        st.warning("Please enter some text.")
    else:
        detected_code = None
        if detector_choice.startswith("langdetect"):
            candidates = detect_langs(text)
            top = candidates[0]
            code = top.lang
            conf = top.prob
            detected_code = code
            st.subheader("Detected Language")
            st.write(f"**{LANG_MAP.get(code, code)}** — confidence: **{conf:.2f}**")
        else:
            code, score = langid.classify(text)
            detected_code = code
            st.subheader("Detected Language")
            st.write(f"**{LANG_MAP.get(code, code)}** — score: **{score:.2f}**")

        if detected_code:
            try:
                # find code for target language
                target_code = [k for k,v in LANG_MAP.items() if v == target_lang]
                if target_code:
                    target_code = target_code[0]
                else:
                    target_code = 'en'
                translation = translator.translate(text, src=detected_code, dest=target_code)
                st.subheader(f"Translation to {LANG_MAP.get(target_code, target_code)}")
                st.write(translation.text)
            except Exception as e:
                st.error("Translation error: " + str(e))
