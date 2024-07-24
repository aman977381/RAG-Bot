import streamlit as st
import requests
import re
import html

# FastAPI server URL
FASTAPI_URL = "http://localhost:8000"

def upload_pdf(file):
    files = {"file": file}
    response = requests.post(f"{FASTAPI_URL}/upload", files=files)
    return response.json()

def ask_query(query):
    payload = {"query": query}
    headers = {"Content-Type": "application/json"}
    response = requests.post(f"{FASTAPI_URL}/qna", json=payload, headers=headers)
    return response.json()

def clear_all():
    response = requests.get(f"{FASTAPI_URL}/clear")
    return response.json()

def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "Welcome! Upload a PDF to ask questions about its content."}]
    st.session_state.uploaded = False
    st.session_state.query = ""
    st.session_state.answer_response = None
    st.session_state.chat_history = []

def format_message(text):
    text_blocks = re.split(r"```[\s\S]*?```", text)
    code_blocks = re.findall(r"```([\s\S]*?)```", text)
    text_blocks = [html.escape(block) for block in text_blocks]

    formatted_text = ""
    for i in range(len(text_blocks)):
        formatted_text += text_blocks[i].replace("\n", "<br>")
        if i < len(code_blocks):
            formatted_text += f'<pre style="white-space: pre-wrap; word-wrap: break-word;"><code>{html.escape(code_blocks[i])}</code></pre>'

    return formatted_text

def message_func(text, is_user=False):
    message_alignment = "flex-end" if is_user else "flex-start"
    message_bg_color = "linear-gradient(135deg, #00B2FF 0%, #006AFF 100%)" if is_user else "#71797E"
    if not is_user:
        text = format_message(text)

    st.write(
        f"""
        <div style="display: flex; align-items: center; margin-bottom: 10px; justify-content: {message_alignment};">
            <div style="background: {message_bg_color}; color: white; border-radius: 20px; padding: 10px; margin-right: 5px; max-width: 75%; font-size: 14px;">
                {text}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def initialize_session_state():
    if 'uploaded' not in st.session_state:
        st.session_state.uploaded = False
    if 'query' not in st.session_state:
        st.session_state.query = ""
    if 'answer_response' not in st.session_state:
        st.session_state.answer_response = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if "messages" not in st.session_state.keys():
        st.session_state.messages = [{"role": "assistant", "content": "Welcome! Upload a PDF to ask questions about its content."}]

# Set page configuration
st.set_page_config(page_title="🤖💬 PDF ChatBot")

# Apply gradient text style
gradient_text_html = """
<style>
.gradient-text {
    font-weight: bold;
    background: -webkit-linear-gradient(left, blue, purple);
    background: linear-gradient(to right, blue, purple);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    display: inline;
    font-size: 3em;
}
</style>
<div class="gradient-text">PDF ChatBot</div>
"""
st.markdown(gradient_text_html, unsafe_allow_html=True)

# Sidebar layout
with st.sidebar:
    st.title('🤖💬 PDF ChatBot')
    st.subheader('Functions')
    st.button('Clear Chat History', on_click=clear_chat_history)

    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    if st.button("Upload"):
        if uploaded_file is not None:
            with st.spinner('Uploading and processing file...'):
                upload_response = upload_pdf(uploaded_file)
            if "error" in upload_response:
                st.error(f"Error: {upload_response['error']}")
            else:
                st.success("File uploaded and processed successfully! You can now ask questions about your PDF.")
                st.session_state.uploaded = True
                st.session_state.query = ""
                st.session_state.answer_response = None
                st.session_state.chat_history = []

    if st.button("Clear All"):
        clear_response = clear_all()
        if "error" in clear_response:
            st.error(f"Error: {clear_response['error']}")
        else:
            st.success("Cleared successfully!")
            clear_chat_history()

# Initialize session state
initialize_session_state()

# Display initial messages
for message in st.session_state.messages:
    message_func(message["content"], is_user=(message["role"] == "user"))

# Text input for user queries
if prompt := st.chat_input("Your message:"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    message_func(prompt, is_user=True)

    # Fetch and display assistant response
    with st.spinner('Getting answer...'):
        response = ask_query(prompt)
    if "response" in response:
        st.session_state.messages.append({"role": "assistant", "content": response["response"]})
        message_func(response["response"], is_user=False)
    else:
        error_message = "Failed to get a response from the server." if st.session_state.uploaded else "Please upload a document to proceed with queries."
        st.session_state.messages.append({"role": "assistant", "content": error_message})
        message_func(error_message, is_user=False)
