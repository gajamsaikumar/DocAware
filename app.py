import streamlit as st
import os
import fitz
from pathlib import Path



from services.ai_assistant import AIAssistant
from services.risk_analyzer import RiskAnalyzer
from services.document_processor import DocumentProcessor
from services.scanner_service import run_openclaw_scan
from dotenv import load_dotenv
from data.suggested_questions import SUGGESTED_QUESTIONS

load_dotenv()

# INITIALISE SERVICES

ai = AIAssistant()
risk_analyzer = RiskAnalyzer()
document_processor = DocumentProcessor()




# PAGE CONFIG & STYLING

st.set_page_config(page_title="DocAware", page_icon="🦞", layout="wide")

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none !important;}

    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background: #f4f7fb;
        color: #111827;
    }

    /* ---------- APP HEADER ---------- */
.app-header {
    background: white;
    border-radius: 20px;
    padding: 1.2rem 1.8rem;
    margin-bottom: 1.5rem;
    border: 1px solid #e5e7eb;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
}

.brand-section {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.brand-logo {
    width: 54px;
    height: 54px;
    border-radius: 16px;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    color: white;
    box-shadow: 0 8px 20px rgba(99, 102, 241, 0.25);
}

.brand-title {
    font-size: 1.35rem;
    font-weight: 700;
    color: #111827;
}

.brand-subtitle {
    font-size: 0.9rem;
    color: #6b7280;
}

    /* ---------- METRIC CARDS ---------- */
    .metric-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        transition: all 0.2s ease;
    }
    .metric-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
    .metric-value { font-size: 2rem; font-weight: 700; }
    .metric-label { font-size: 0.85rem; color: #6b7280; margin-top: 0.25rem; }
    .metric-trend { font-size: 0.8rem; margin-top: 0.25rem; font-weight: 600; }

    /* ---------- SECTION TITLES ---------- */
    .section-title {
        font-size: 0.85rem; font-weight: 600; color: #6b7280;
        text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;
    }

    /* ---------- FLAG CARDS ---------- */
    .flag-item {
        background: white; border: 1px solid #e5e7eb; border-radius: 12px;
        padding: 1rem; margin-bottom: 0.75rem; border-left: 4px solid #ef4444;
        transition: all 0.2s ease;
    }
    .flag-item:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0,0,0,0.06); }
    .flag-label { font-weight: 600; font-size: 0.9rem; color: #111827; }
    .flag-snippet { font-size: 0.8rem; color: #6b7280; margin-top: 0.15rem; font-style: italic; }
    .flag-location { font-size: 0.75rem; color: #9ca3af; margin-top: 0.1rem; }

    /* ---------- STICKY INPUT ---------- */
    .stChatInput { position: sticky; bottom: 0; background: white; padding: 1rem 0; z-index: 100; }

    /* ---------- ANIMATIONS ---------- */
    .stApp { animation: fadeIn 0.6s ease-in-out; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    .metric-card { animation: scaleIn 0.4s ease-out; }
    @keyframes scaleIn { from { transform: scale(0.95); opacity: 0; } to { transform: scale(1); opacity: 1; } }

</style>
<script>
    var chatContainer = document.querySelector('.chat-container');
    if (chatContainer) { chatContainer.scrollTop = chatContainer.scrollHeight; }
</script>
""", unsafe_allow_html=True)


# HEADER

header_html = """
<div class="app-header">
    <div class="brand-section">
        <div class="brand-logo">🦞</div>
        <div>
            <div class="brand-title">DocAware</div>
            <div class="brand-subtitle">AI-powered document intelligence</div>
        </div>
    </div>
</div>
"""

st.markdown(header_html, unsafe_allow_html=True)

#  FILE UPLOAD FLOW


if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
if "scan_completed" not in st.session_state:
    st.session_state.scan_completed = False

if st.session_state.uploaded_file is None:
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("#### 📄 Upload your document")

        uploaded_file = st.file_uploader(
            "PDF, DOCX, or TXT",
            type=["pdf", "docx", "txt"],
            label_visibility="visible",
            key="main_uploader"
        )

        if uploaded_file is not None:
            st.session_state.uploaded_file = uploaded_file
            st.session_state.scan_completed = False
            st.session_state.messages = []
            st.session_state.visible_pages = 10
            st.rerun()


# DOCUMENT ANALYSIS

else:
    uploaded_file = st.session_state.uploaded_file

    if st.button("⬅️ Upload a different document", type="secondary"):
        st.session_state.uploaded_file = None
        st.session_state.messages = []
        st.session_state.visible_pages = 10
        st.rerun()

    # --- One-time analysis ---
    if not st.session_state.scan_completed:
        temp_dir = Path("data/temp")
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_path = temp_dir / uploaded_file.name
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        with st.spinner("🔍 Analysing your document..."):
            try:
                clean_page_texts, clean_text = document_processor.process_document(temp_path)
            except Exception as e:
                st.error(f"Could not read file: {e}")
                st.stop()
            # --- OpenClaw orchestration ---
            flags = run_openclaw_scan(str(temp_path))
            if not flags:
                regex_flags = risk_analyzer.scan(clean_page_texts)
                semantic_flags = risk_analyzer.semantic_scan(clean_text, clean_page_texts)

                flags = regex_flags + semantic_flags
                flags = risk_analyzer.merge_similar(flags)

                for flag in flags:
                    if not flag.get("explanation"):
                        snippet = flag.get("matched_text", "")

                        flag["explanation"] = ai.ask(
                            (
                                f"Explain this specific contract clause in simple plain English "
                                f"in exactly 2 short sentences only: {snippet}"
                            ),
                            document_text=clean_text
                        )

            # --- Risk score & memory ---
            risk = risk_analyzer.score(flags)
            st.session_state.risk = risk
            st.session_state.last_scan_context = "\n".join(
                [f"{i}. {f['flag']}: {f.get('matched_text','')}" for i, f in enumerate(flags, 1)]
            )

            st.session_state.last_scan = flags
            st.session_state.document_text = clean_text
            st.session_state.scan_completed = True

        os.remove(temp_path)

   # ---------- METRIC CARDS ----------
    flags = st.session_state.get("last_scan", [])

  
    if flags:
        risk = st.session_state.get("risk", {})
        score = risk.get("score", 0)
        level = risk.get("level", "Low")
        breakdown = risk.get("breakdown", {})

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color:#6366f1;">{score}/10</div>
                <div class="metric-label">Overall Score</div>
                <div class="metric-trend" style="color:#ef4444;">{level} Risk</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{breakdown.get('High',0)}</div>
                <div class="metric-label">High Risks</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{breakdown.get('Medium',0)}</div>
                <div class="metric-label">Medium Risks</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{len(flags)}</div>
                <div class="metric-label">Total Clauses</div>
            </div>
            """, unsafe_allow_html=True)
# --- Display results ---

if st.session_state.get("scan_completed"):
    risk = st.session_state.get("risk", {})
    flags = st.session_state.get("last_scan", [])

    # ---------- THREE PANEL DASHBOARD ----------
    doc_col, risk_col, ai_col = st.columns([1.2, 1, 1.35])


    # DOCUMENT VIEWER

    with doc_col:
        st.markdown(
            '<p class="section-title">📄 Document Viewer</p>',
            unsafe_allow_html=True
        )
   
        if uploaded_file and uploaded_file.name.lower().endswith(".pdf"):
            temp_dir = Path("data/temp")
            temp_dir.mkdir(parents=True, exist_ok=True)

            pdf_path = temp_dir / uploaded_file.name

            with open(pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            doc = fitz.open(str(pdf_path))
            total_pages = len(doc)

            if "visible_pages" not in st.session_state:
                st.session_state.visible_pages = 10

            max_pages = min(total_pages, st.session_state.visible_pages)

            with st.container(height=900):
                for page_num in range(max_pages):
                    page = doc.load_page(page_num)

                    page_rect = page.rect

                    cropped_rect = fitz.Rect(
                        page_rect.x0 + 20,
                        page_rect.y0 + 20,
                        page_rect.x1 - 20,
                        page_rect.y1 - 20
                    )

                    pix = page.get_pixmap(
                        matrix=fitz.Matrix(1.1, 1.1),
                        clip=cropped_rect,
                        alpha=False
                    )

                    img_bytes = pix.tobytes("png")

                    st.caption(f"Page {page_num + 1}")
                    st.image(img_bytes, use_container_width=True)

            if max_pages < total_pages:
                if st.button("Load 10 more pages", use_container_width=True):
                    st.session_state.visible_pages += 10
                    st.rerun()

            
            doc.close()

        else:
            st.info("Upload a PDF contract to preview it here.")
   
    # RISK PANEL
 
    with risk_col:
        st.markdown(
            '<p class="section-title">⚠️ Key Risks Identified</p>',
            unsafe_allow_html=True
        )

        if flags:
            for i, f in enumerate(flags, 1):

                sev = risk_analyzer.get_severity(f)

                badge_color = "#ef4444" if sev == "High" else "#f59e0b"

                snippet = f.get("matched_text", "")
                pages = f.get("pages", set())

                if pages:
                    sorted_pages = sorted([p for p in pages if p])

                    if len(sorted_pages) == 1:
                        location = f"Page {sorted_pages[0]}"
                    else:
                        location = "Pages " + ", ".join(map(str, sorted_pages))

                else:
                    page = f.get("page")
                    line = f.get("line")

                    if page and line:
                        location = f"Page {page}, Line {line}"
                    elif page:
                        location = f"Page {page}"
                    else:
                        location = ""

                explanation = f.get("explanation", "This clause may need closer review.")
                with st.container(border=True):
                    
                    st.markdown(
                        f"""
                        **{i}. {f.get('flag', 'Risk')}**
                        <span style="
                            background:{badge_color}20;
                            color:{badge_color};
                            padding:4px 10px;
                            border-radius:20px;
                            font-size:12px;
                            font-weight:600;
                        ">
                            {sev}
                        </span>
                        """,
                        unsafe_allow_html=True
                    )

                    if location:
                        st.caption(location)

                    

                    with st.expander("What this means"):

                        st.markdown("**Simple explanation**")
                        st.markdown(explanation)
                    

                        category = f.get("category", "")
                        
                        questions =  SUGGESTED_QUESTIONS.get(category, [])

                        if questions:
                            st.markdown("**What you might ask**")

                            for idx, q in enumerate(questions):
                                if st.button(
                                    q,
                                    key=f"question_{i}_{idx}",
                                    use_container_width=True
                                ):
                                    st.session_state.messages.append({
                                        "role": "user",
                                        "content": q
                                    })

                                    
                                    response = ai.ask(
                                        q,
                                        document_text=st.session_state.get("document_text", "")
                                    )

                                    st.session_state.messages.append({
                                        "role": "assistant",
                                        "content": response
                                    })

                                    st.rerun() 

    # AI ASSISTANT
   
    with ai_col:
        st.markdown(
            '<p class="section-title">🤖 AI Assistant</p>',
            unsafe_allow_html=True
        )

        if "messages" not in st.session_state:
            st.session_state.messages = []
            st.session_state.visible_pages = 10

        chat_container = st.container(height=520)

        with chat_container:
            with st.chat_message("assistant"):
                st.write(
                    "I’ve analysed your contract. Ask me about risks, clauses, penalties, or negotiation suggestions."
                )

            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])

        user_prompt = st.chat_input(
            "Ask anything about the document...",
            key="doc_chat_input"
        )

        if user_prompt:
            st.session_state.messages.append({
                "role": "user",
                "content": user_prompt
            })

            with st.spinner("Thinking..."):
                response = ai.ask(
                    user_prompt,
                    document_text=st.session_state.get("document_text", "")
                )

            st.session_state.messages.append({
                "role": "assistant",
                "content": response
            })

            st.rerun()

        