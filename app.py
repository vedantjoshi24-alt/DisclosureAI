"""DisclosureAI: a deterministic, offline AI-use disclosure generator."""

from __future__ import annotations

import json

import streamlit as st
import streamlit.components.v1 as components

from disclosure import ASSISTANCE_OPTIONS, EXTENT_OPTIONS, generate_disclosure, validate_inputs
from document_review import DocumentReviewError, extent_from_scope, review_pdf


st.set_page_config(
    page_title="DisclosureAI | AI-use disclosures",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

DEFAULTS = {
    "project_name": "",
    "assistance_types": [],
    "other_assistance": "",
    "description": "",
    "extent": "Moderate",
    "generated_statement": "",
    "submission_errors": {},
    "document_scope": "Not sure - choose manually",
    "document_uploader_nonce": 0,
}

for state_key, default_value in DEFAULTS.items():
    st.session_state.setdefault(state_key, default_value)


def reset_form() -> None:
    """Return the app to a clean, predictable initial state."""
    next_uploader_nonce = st.session_state.document_uploader_nonce + 1
    for state_key, default_value in DEFAULTS.items():
        st.session_state[state_key] = default_value.copy() if isinstance(default_value, dict) else default_value
    st.session_state.document_uploader_nonce = next_uploader_nonce


def copy_button(text: str) -> None:
    """Render a dependency-free clipboard button with in-place feedback."""
    # Keep user-provided wording data, not executable HTML, when it is embedded
    # in the component's script block.
    text_json = (
        json.dumps(text)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )
    components.html(
        f"""
        <style>
          * {{ box-sizing: border-box; }}
          body {{ margin: 0; background: transparent; font-family: Inter, ui-sans-serif, system-ui, sans-serif; }}
          button {{
            width: 100%; height: 42px; border: 1px solid #c7d2fe; border-radius: 10px;
            background: #eef2ff; color: #3730a3; cursor: pointer; font-size: 14px;
            font-weight: 700; letter-spacing: .01em; transition: background .15s ease, transform .15s ease;
          }}
          button:hover {{ background: #e0e7ff; }}
          button:active {{ transform: translateY(1px); }}
          button.success {{ background: #ecfdf5; border-color: #a7f3d0; color: #047857; }}
        </style>
        <button id="copy-button" type="button" aria-label="Copy disclosure to clipboard">Copy disclosure</button>
        <script>
          const disclosure = {text_json};
          const button = document.getElementById('copy-button');
          async function copyDisclosure() {{
            let copied = false;
            try {{
              await navigator.clipboard.writeText(disclosure);
              copied = true;
            }} catch (error) {{
              const fallback = document.createElement('textarea');
              fallback.value = disclosure;
              fallback.setAttribute('readonly', '');
              fallback.style.position = 'fixed';
              fallback.style.opacity = '0';
              document.body.appendChild(fallback);
              fallback.select();
              copied = document.execCommand('copy');
              document.body.removeChild(fallback);
            }}
            if (copied) {{
              button.textContent = '✓ Copied to clipboard';
              button.classList.add('success');
              window.setTimeout(() => {{
                button.textContent = 'Copy disclosure';
                button.classList.remove('success');
              }}, 2200);
            }} else {{
              button.textContent = 'Copy unavailable — select text instead';
            }}
          }}
          button.addEventListener('click', copyDisclosure);
        </script>
        """,
        height=46,
    )


st.markdown(
    """
    <style>
      :root { --ink: #0f172a; --muted: #64748b; --indigo: #4f46e5; --line: #e2e8f0; }
      .stApp { background: #f8fafc; color: var(--ink); }
      [data-testid="stHeader"] { background: rgba(248, 250, 252, .92); }
      [data-testid="stMainBlockContainer"] { max-width: 1180px; padding-top: 3.5rem; padding-bottom: 3rem; }
      .hero-kicker { color: var(--indigo); font-size: .78rem; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; margin-bottom: .55rem; }
      .hero-title { font-size: clamp(2.2rem, 5vw, 3.75rem); letter-spacing: -.055em; line-height: 1; margin: 0; color: var(--ink); }
      .hero-copy { max-width: 610px; color: var(--muted); font-size: 1.05rem; line-height: 1.65; margin: 1rem 0 2.1rem; }
      .eyebrow { color: #475569; font-size: .8rem; font-weight: 800; text-transform: uppercase; letter-spacing: .09em; margin: 0 0 .35rem; }
      .panel-title { color: var(--ink); font-size: 1.38rem; font-weight: 750; letter-spacing: -.025em; margin: 0 0 .25rem; }
      .panel-copy { color: var(--muted); font-size: .91rem; line-height: 1.5; margin: 0 0 1.4rem; }
      [data-testid="stVerticalBlockBorderWrapper"] { border: 1px solid var(--line); border-radius: 18px; background: #fff !important; color: #000 !important; box-shadow: 0 10px 30px rgba(15, 23, 42, .045); }
      [data-testid="stVerticalBlockBorderWrapper"] > div { padding: 1.55rem; }
      .empty-state { border: 1px dashed #cbd5e1; border-radius: 12px; padding: 2rem 1.25rem; color: #000; background: #fff; text-align: center; line-height: 1.55; }
      .trust-note { display: flex; gap: .55rem; align-items: flex-start; padding: .85rem .95rem; border-radius: 10px; color: #000; background: #fff; border: 1px solid #e2e8f0; font-size: .84rem; line-height: 1.48; margin-top: 1rem; }
      .review-note { border-left: 3px solid #6366f1; padding: .85rem 1rem; background: #eef2ff; color: #1e1b4b; border-radius: 0 10px 10px 0; font-size: .88rem; line-height: 1.5; margin-bottom: .9rem; }
      .review-observation { color: #334155; font-size: .87rem; margin: .28rem 0; }
      .stTextInput input, .stTextArea textarea, [data-baseweb="select"] > div,
      [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea {
        border-radius: 10px !important; border-color: #cbd5e1 !important;
        background: #fff !important; color: #000 !important; caret-color: #000 !important;
        -webkit-text-fill-color: #000 !important;
      }
      [data-baseweb="select"] * { color: #000 !important; }
      [data-testid="stRadio"] label, [data-testid="stRadio"] label *,
      [data-testid="stRadio"] [role="radio"], [data-baseweb="radio"] label,
      [data-baseweb="radio"] label * {
        color: #000 !important; -webkit-text-fill-color: #000 !important; opacity: 1 !important;
      }
      .stTextInput input:focus, .stTextArea textarea:focus { border-color: var(--indigo) !important; box-shadow: 0 0 0 3px rgba(79, 70, 229, .12) !important; }
      .stButton > button, [data-testid="stFormSubmitButton"] > button { border-radius: 10px; min-height: 44px; font-weight: 750; }
      .stButton > button { background: #fff; border: 1px solid #cbd5e1; color: #475569; }
      .stButton > button:hover { border-color: #94a3b8; color: #0f172a; background: #f8fafc; }
      [data-testid="stFormSubmitButton"] > button { width: 100%; background: var(--indigo); color: #fff; }
      [data-testid="stFormSubmitButton"] > button:hover { background: #4338ca; color: #fff; }
      div[data-testid="stRadio"] > div { gap: .55rem; }
      @media (max-width: 700px) { [data-testid="stMainBlockContainer"] { padding-top: 2.25rem; } [data-testid="stVerticalBlockBorderWrapper"] > div { padding: 1.2rem; } }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="hero-kicker">Transparent academic AI use</div>', unsafe_allow_html=True)
st.markdown('<h1 class="hero-title">Say exactly how AI helped.</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="hero-copy">DisclosureAI turns your own description into clear, professional wording. It is deterministic, works offline, and never adds claims you did not provide.</p>',
    unsafe_allow_html=True,
)

form_column, result_column = st.columns((1.08, 0.92), gap="large")

with form_column:
    with st.container(border=True):
        st.markdown('<p class="eyebrow">Optional document review</p><p class="panel-title">Review an assignment PDF</p><p class="panel-copy">Get document facts and reflection prompts before completing your disclosure.</p>', unsafe_allow_html=True)
        st.markdown('<div class="review-note"><strong>Not an AI detector.</strong> This review finds document structure only. It cannot prove AI use, assess authorship, or choose your extent for you.</div>', unsafe_allow_html=True)
        uploaded_pdf = st.file_uploader(
            "Upload a text-based assignment PDF (optional)",
            type=["pdf"],
            key=f"assignment_pdf_{st.session_state.document_uploader_nonce}",
            help="Processed in memory for this session only. Password-protected and scanned PDFs are not supported.",
        )
        if uploaded_pdf is not None:
            try:
                document_insights = review_pdf(uploaded_pdf.getvalue(), uploaded_pdf.name)
            except DocumentReviewError as error:
                st.warning(str(error))
            else:
                if not document_insights.text_detected:
                    st.warning("No selectable text was found. Use a text-based PDF, or complete the reflection manually.")
                else:
                    page_metric, word_metric, cue_metric = st.columns(3)
                    page_metric.metric("Pages", document_insights.page_count)
                    word_metric.metric("Words", f"{document_insights.word_count:,}")
                    cue_metric.metric("Structural cues", len(document_insights.observations))
                    st.markdown("**Document observations**")
                    for observation in document_insights.observations:
                        st.markdown(f'<p class="review-observation">• {observation}</p>', unsafe_allow_html=True)
                    st.markdown("**Reflection prompts**")
                    for prompt in document_insights.reflection_prompts:
                        st.markdown(f'<p class="review-observation">• {prompt}</p>', unsafe_allow_html=True)

                    document_scope = st.radio(
                        "Based on your recollection, AI support covered:",
                        (
                            "Not sure - choose manually",
                            "One isolated supporting task or section",
                            "Several described tasks or sections",
                            "Major sections or repeated work",
                        ),
                        key="document_scope",
                        help="Your choice, not the document, creates an extent suggestion.",
                    )
                    suggested_extent = extent_from_scope(document_scope)
                    if suggested_extent:
                        st.info(
                            f"Your self-assessment suggests **{suggested_extent}** involvement. "
                            "You can use it as a starting point, then review the extent field below."
                        )
                        if st.button(f"Use {suggested_extent} as my starting extent", use_container_width=True):
                            st.session_state.extent = suggested_extent

        st.markdown('<hr style="border:0; border-top:1px solid #e2e8f0; margin:1.65rem 0 1.25rem;">', unsafe_allow_html=True)
        st.markdown('<p class="eyebrow">Step 1</p><p class="panel-title">Your information</p><p class="panel-copy">Describe the actual assistance received. Fields marked required are needed to generate wording.</p>', unsafe_allow_html=True)

        with st.form("disclosure_form", clear_on_submit=False):
            project_name = st.text_input(
                "Assignment or project name *",
                key="project_name",
                max_chars=100,
                placeholder="e.g., Machine Learning Assignment 3",
            )
            assistance_types = st.multiselect(
                "How did AI assist? *",
                options=ASSISTANCE_OPTIONS,
                key="assistance_types",
                placeholder="Select one or more types",
                help="Choose every type that applies to this work.",
            )
            other_assistance = ""
            if "Other" in assistance_types:
                other_assistance = st.text_input(
                    "Describe the other assistance *",
                    key="other_assistance",
                    max_chars=50,
                    placeholder="e.g., translation support",
                )
            description = st.text_area(
                "What did AI actually help with? *",
                key="description",
                max_chars=600,
                height=132,
                placeholder="e.g., I used it to outline possible approaches and improve the clarity of my draft.",
                help="Use concrete tasks. This text is preserved in the disclosure.",
            )
            extent = st.radio(
                "Extent of AI involvement *",
                EXTENT_OPTIONS,
                key="extent",
                horizontal=True,
                help="Choose the level that best reflects the work described above.",
            )
            submitted = st.form_submit_button("Generate disclosure")

            if submitted:
                errors = validate_inputs(project_name, assistance_types, description, extent, other_assistance)
                st.session_state.submission_errors = errors
                if errors:
                    for message in errors.values():
                        st.error(message)
                else:
                    st.session_state.generated_statement = generate_disclosure(
                        project_name, assistance_types, description, extent, other_assistance
                    )
                    st.success("Disclosure generated. Review and edit the wording before using it.")

        st.button("Reset form", on_click=reset_form, use_container_width=True)

with result_column:
    with st.container(border=True):
        st.markdown('<p class="eyebrow">Step 2</p><p class="panel-title">Generated wording</p><p class="panel-copy">This panel is editable. Make sure it accurately reflects your use before submitting it.</p>', unsafe_allow_html=True)

        statement = st.session_state.generated_statement
        if statement:
            editable_statement = st.text_area(
                "Disclosure statement",
                key="generated_statement",
                height=230,
                label_visibility="collapsed",
            )
            copy_button(editable_statement)
            st.markdown(
                '<div class="trust-note"><span>✦</span><span><strong>User-provided:</strong> project name, assistance types, description, and extent. <strong>Automatically generated:</strong> the surrounding disclosure wording.</span></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="empty-state"><strong>Your disclosure will appear here.</strong><br>Complete the form and select <em>Generate disclosure</em> to create wording you can review, edit, and copy.</div>',
                unsafe_allow_html=True,
            )

st.caption("DisclosureAI does not persist your form data or uploaded PDF, and it calls no external AI services.")
