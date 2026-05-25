import os
import requests
import streamlit as st


class AIAssistant:
    """Handles AI-powered document explanations and conversational Q&A."""
    def __init__(self):
        self.api_key = os.getenv("MISTRAL_API_KEY")
        self.url = "https://api.mistral.ai/v1/chat/completions"

        if not self.api_key:
            raise ValueError("MISTRAL_API_KEY environment variable is not set.")

    def ask(self, user_message: str, document_text: str = "", local_answer=None) -> str:
        """Send document-aware prompts to Mistral AI and return a response."""
        if not document_text:
            if local_answer:
                return local_answer(user_message)
            return "No document context available."

        memory_context = ""

        if "last_scan_context" in st.session_state:
            if st.session_state.last_scan_context:
                memory_context = (
                    f"Previous scan results:\n"
                    f"{st.session_state.last_scan_context}\n\n"
                )

        snippet = document_text[:6000]

        prompt = (
            "You are DocAware, a document analysis assistant.\n\n"
            "IMPORTANT RULES:\n"
            "- Respond ONLY in plain text.\n"
            "- NEVER return HTML.\n"
            "- Never give legal advice.\n"
            "- Answer questions only if they relate to the uploaded document or its clauses.\n"
            "- You may explain, summarise, or infer based on the uploaded document content.\n"
            "- Do NOT answer unrelated general knowledge questions.\n"
            "- If a question is unrelated to the uploaded document, reply exactly: "
            "'I can only answer questions related to the uploaded document.'\n\n"
            f"{memory_context}"
            "Relevant document text:\n{snippet}\n\n"
            f"User question: {user_message}"
        )

        try:
            response = requests.post(
                self.url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "mistral-small-latest",
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]

            return "I'm having trouble reaching the AI assistant."

        except Exception:
            return "Connection issue. Please try again."