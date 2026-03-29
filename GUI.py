import streamlit as st
import requests
import uuid
from typing import Optional

st.set_page_config(page_title="Entropy AI Controller", layout="wide")
st.title("🌍 Entropy AI — Supervisory Controller Demo")
st.caption("Local Ollama + Full Entropy Controller (v2)")

# ====================== SIDEBAR ======================
with st.sidebar:
    st.header("🔧 Connection")
    api_url = st.text_input("API URL", value="http://127.0.0.1:8000")
    api_key = st.text_input("API Key", value="testkey", type="password")
    
    st.divider()
    st.header("⚡ Controller Settings")
    energy_budget = st.slider("Energy Budget", 10.0, 200.0, 100.0, step=5.0)
    max_tokens = st.slider("Max Tokens", 100, 1500, 1000, step=50)      # ← Bumped up
    temperature = st.slider("Temperature", 0.0, 1.0, 0.7, step=0.05)
    
    new_conv = st.button("🆕 New Conversation", use_container_width=True)
    
    st.divider()
    st.info("💡 Controller state persists via conversation_id")

# ====================== SESSION STATE ======================
if "conversation_id" not in st.session_state or new_conv:
    st.session_state.conversation_id = str(uuid.uuid4())
    st.session_state.messages = []

# ====================== CHAT ======================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "control" in msg:
            with st.expander("📊 Controller Telemetry", expanded=False):
                c = msg["control"]
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Mode", c.get("mode_used", "—"))
                    st.metric("Entropy", f"{c.get('entropy_observed', 0):.2f}")
                with col2:
                    st.metric("Energy Remaining", f"{c.get('energy_remaining', 0):.2f}")
                    st.metric("Energy Consumed", f"{c.get('energy_consumed', 0):.2f}")
                with col3:
                    st.metric("Error Debt", f"{c.get('error_debt', 0):.2f}")
                    st.metric("Failure Detected", "✅" if c.get("failure_detected") else "❌")
                if "scores" in c:
                    st.caption("Mode Scores")
                    st.json(c["scores"])

# ====================== USER INPUT ======================
if prompt := st.chat_input("Ask anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    payload = {
        "model": "qwen2.5:3b",
        "messages": [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
        "conversation_id": st.session_state.conversation_id,
        "energy_budget": energy_budget,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    with st.spinner("Thinking (with controller active)..."):
        try:
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
            resp = requests.post(f"{api_url}/v1/chat/completions", json=payload, headers=headers, timeout=180)
            resp.raise_for_status()
            data = resp.json()

            assistant_text = data["choices"][0]["message"]["content"]
            control = data.get("control", {})

            st.session_state.messages.append({"role": "assistant", "content": assistant_text, "control": control})

            with st.chat_message("assistant"):
                st.markdown(assistant_text)
                with st.expander("📊 Controller Telemetry", expanded=True):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Mode", control.get("mode_used", "—"))
                        st.metric("Entropy", f"{control.get('entropy_observed', 0):.2f}")
                    with col2:
                        st.metric("Energy Remaining", f"{control.get('energy_remaining', 0):.2f}")
                        st.metric("Energy Consumed", f"{control.get('energy_consumed', 0):.2f}")
                    with col3:
                        st.metric("Error Debt", f"{control.get('error_debt', 0):.2f}")
                        st.metric("Failure Detected", "✅" if control.get("failure_detected") else "❌")
                    if "scores" in control:
                        st.caption("Mode Scores")
                        st.json(control["scores"])

        except Exception as e:
            st.error(f"API error: {e}")

st.caption(f"Conversation ID: **{st.session_state.conversation_id}**")