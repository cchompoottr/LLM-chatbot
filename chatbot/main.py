import ollama 
import streamlit as st 

st.title("LLM Chatbot")

# history user chat
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# แสดงข้อความก่อนหน้า
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# รับข้อความใหม่
if prompt := st.chat_input("บอกอาการของคุณ?"):
    st.session_state["messages"].append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    # ส่งข้อความไปยัง LLM
    with st.chat_message("assistant"):
        response = ollama.chat(
            model="llama3.2",
            messages=st.session_state["messages"],
            stream=False
        )
        message = response["message"]["content"]
        st.markdown(message)
        st.session_state["messages"].append({"role": "assistant", "content": message})

