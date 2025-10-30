import streamlit as st
import pdfplumber
import docx
import re
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# ---------------------------------------------------------
# ✅ Page configuration
# ---------------------------------------------------------
st.set_page_config(page_title="AI Resume Parser", layout="wide")

# ---------------------------------------------------------
# ✅ PWA: Manifest + Service Worker
# ---------------------------------------------------------
st.markdown("""
<link rel="manifest" href="static/manifest.json">
<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('static/service-worker.js')
      .then(() => console.log('✅ Service Worker registered'))
      .catch(err => console.error('❌ Service Worker failed:', err));
  });
}

// Show Install prompt if available
let deferredPrompt;
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  const installBtn = document.getElementById('install-app-btn');
  if (installBtn) installBtn.style.display = 'block';
});

function installPWA() {
  if (deferredPrompt) {
    deferredPrompt.prompt();
    deferredPrompt.userChoice.then(() => deferredPrompt = null);
  }
}
</script>
<meta name="theme-color" content="#0d6efd">
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# ✅ Load spaCy model
# ---------------------------------------------------------
nlp = spacy.load("en_core_web_sm")

# ---------------------------------------------------------
# ✅ Resume text extraction
# ---------------------------------------------------------
def extract_text(uploaded_file):
    """Extract text from PDF or DOCX resume"""
    if uploaded_file.name.endswith(".pdf"):
        text = ""
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    elif uploaded_file.name.endswith(".docx"):
        doc = docx.Document(uploaded_file)
        return "\n".join([para.text for para in doc.paragraphs])
    return ""

# ---------------------------------------------------------
# ✅ Resume parsing
# ---------------------------------------------------------
def parse_resume(text):
    """Extract name, email, phone, and skills"""
    doc = nlp(text)

    name = next((ent.text for ent in doc.ents if ent.label_ == "PERSON"), None)
    email_match = re.search(r"\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}\\b", text)
    phone_match = re.search(r"(\\+?\\d{1,3}[-.\\s]?)?\\d{7,12}", text)

    skills_db = ["python", "java", "sql", "machine learning", "nlp", "excel", "communication"]
    skills = [s for s in skills_db if s.lower() in text.lower()]

    return {
        "name": name,
        "email": email_match.group(0) if email_match else None,
        "phone": phone_match.group(0) if phone_match else None,
        "skills": skills
    }

# ---------------------------------------------------------
# ✅ Matching logic
# ---------------------------------------------------------
def match_resume(resume_texts, job_description):
    docs = resume_texts + [job_description]
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(docs)
    similarity = cosine_similarity(vectors[-1], vectors[:-1])
    return similarity.flatten()

# ---------------------------------------------------------
# ✅ Generate PDF report
# ---------------------------------------------------------
def create_pdf_report(report_text):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setFont("Helvetica", 12)
    width, height = A4
    y = height - 60

    for line in report_text.split("\\n"):
        if y < 60:
            pdf.showPage()
            pdf.setFont("Helvetica", 12)
            y = height - 60
        pdf.drawString(60, y, line)
        y -= 15

    pdf.save()
    buffer.seek(0)
    return buffer

# ---------------------------------------------------------
# ✅ Streamlit UI
# ---------------------------------------------------------
st.title("💬 AI Resume Parser")

# Sidebar
st.sidebar.title("🧭 Controls")

# Install App button (PWA)
st.sidebar.markdown("""
<button id="install-app-btn" onclick="installPWA()" 
style="display:none; background:#0d6efd; color:white; border:none;
padding:8px 16px; border-radius:8px; cursor:pointer;">
📦 Install AI Resume Parser
</button>
""", unsafe_allow_html=True)

# Session state setup
if "messages" not in st.session_state:
    st.session_state.messages = []
if "files" not in st.session_state:
    st.session_state.files = None
if "confirm_clear" not in st.session_state:
    st.session_state.confirm_clear = False

# Clear Chat
if st.sidebar.button("🗑️ Clear Chat"):
    st.session_state.confirm_clear = True

if st.session_state.confirm_clear:
    st.sidebar.warning("⚠️ Are you sure you want to clear all chat and files?")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("✅ Yes, clear all"):
            st.session_state.messages = []
            st.session_state.files = None
            st.session_state.confirm_clear = False
            st.experimental_rerun()
    with col2:
        if st.button("❌ Cancel"):
            st.session_state.confirm_clear = False

# Chat history
if st.sidebar.checkbox("📜 Show Chat History", value=False):
    for msg in st.session_state.messages:
        st.sidebar.markdown(f"**{msg['role'].capitalize()}:** {msg['content'][:80]}{'...' if len(msg['content']) > 80 else ''}")

# Download latest report
if st.sidebar.button("📥 Download Report"):
    last_reply = next((m["content"] for m in reversed(st.session_state.messages) if m["role"] == "assistant"), "")
    if last_reply:
        pdf_file = create_pdf_report(last_reply)
        st.sidebar.download_button(
            label="⬇️ Click to Download PDF Report",
            data=pdf_file,
            file_name="resume_analysis_report.pdf",
            mime="application/pdf"
        )
    else:
        st.sidebar.warning("⚠️ No analysis found yet.")

# File uploader
uploaded_files = st.file_uploader("📎 Upload resumes", type=["pdf", "docx"], accept_multiple_files=True)
if uploaded_files:
    st.session_state.files = uploaded_files
    st.success(f"{len(uploaded_files)} file(s) uploaded successfully!")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Main chat input
if user_input := st.chat_input("Type a job description or request..."):
    st.session_state.messages.append({"role": "user", "content": user_input})

    if st.session_state.files:
        resume_texts, parsed_data = [], []
        for file in st.session_state.files:
            text = extract_text(file)
            resume_texts.append(text)
            parsed_data.append(parse_resume(text))

        scores = match_resume(resume_texts, user_input)
        for i, parsed in enumerate(parsed_data):
            parsed["score"] = scores[i]
        ranked = sorted(parsed_data, key=lambda x: x["score"], reverse=True)

        reply = "📊 **Candidate Ranking (Best → Worst):**\\n\\n"
        for rank, parsed in enumerate(ranked, start=1):
            reply += f"**{rank}. {parsed['name'] or 'Unknown'}**\\n"
            reply += f"- 📧 {parsed['email'] or 'N/A'}\\n"
            reply += f"- 📱 {parsed['phone'] or 'N/A'}\\n"
            reply += f"- 🛠 Skills: {', '.join(parsed['skills']) if parsed['skills'] else 'N/A'}\\n"
            reply += f"- ✅ Match Score: {parsed['score']:.2f}\\n\\n"
    else:
        reply = "⚠️ Please upload at least one resume before analysis."

    st.session_state.messages.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.markdown(reply)
