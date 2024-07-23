import streamlit as st
import requests

# FastAPI server URL
FASTAPI_URL = "http://localhost:8000"

def upload_pdf(file):
    files = {"file": file}
    response = requests.post(f"{FASTAPI_URL}/upload", files=files)
    return response.json()

def ask_query(query):
    payload = {"Query": query}
    headers = {"Content-Type": "application/json"}
    response = requests.post(f"{FASTAPI_URL}/askLLM", json=payload, headers=headers)
    return response.json()

st.title("PDF Document Question Answering")

# Initialize session state for upload status
if 'uploaded' not in st.session_state:
    st.session_state.uploaded = False

# File uploader
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None and not st.session_state.uploaded:
    # Upload the PDF file to FastAPI server
    with st.spinner('Uploading and processing file...'):
        upload_response = upload_pdf(uploaded_file)
    
    if "error" in upload_response:
        st.error(f"Error: {upload_response['error']}")
    else:
        st.success("File uploaded and processed successfully! You can now ask questions about your PDF.")
        st.session_state.uploaded = True

# Text input for user queries
query = st.text_input("Ask a question about the document:", disabled=not st.session_state.uploaded)

if query and st.session_state.uploaded:
    with st.spinner('Getting answer...'):
        answer_response = ask_query(query)
    
    if "error" in answer_response:
        st.error(f"Error: {answer_response['error']}")
    else:
        #st.write("Response:")
        st.write(answer_response['response'])
