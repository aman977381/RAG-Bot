import os
import uvicorn
import shutil
from pydantic import BaseModel
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from langchain_groq import ChatGroq
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

class QueryModel(BaseModel):
    query: str

# Load the Groq model
groq_api_key = "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"
llm = ChatGroq(groq_api_key=groq_api_key, model_name='llama3-70b-8192')

# Load HuggingFaceEmbeddings
embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-en-v1.5",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)

prompt = ChatPromptTemplate.from_template(
    """
    Based on the context provided, give a detailed and accurate answer to the question below.
    Make sure your response is strictly derived from the context.

    Context:
    {context}

    Question:
    {input}

    Answer:
    """
)

# Ensure the files directory exists
os.makedirs('files', exist_ok=True)

app = FastAPI()

# API endpoint for file upload
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        file_path = f'files/{file.filename}'
        with open(file_path, 'wb') as gf:
            gf.write(contents)
    except Exception as err:
        return {"error": f"Error occurred during file upload: {str(err)}"}

    # Document processing and FAISS indexing
    try:
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=20)
        chunks = text_splitter.split_documents(documents)

        faiss_db = FAISS.from_documents(chunks, embeddings)
        faiss_db.save_local(f"faiss_db/faiss_index")
        os.remove(file_path)
        return {"filename": f"File uploaded successfully: {file.filename}"}
    except Exception as err:
        return JSONResponse(status_code=400, content={"error": f"Error occurred during file processing: {str(err)}"})

@app.post("/qna")
async def ask(query: QueryModel):
    try:
        document_chain = create_stuff_documents_chain(llm, prompt)
        new_db = FAISS.load_local(f"faiss_db/faiss_index", embeddings, allow_dangerous_deserialization=True)

        # Initialize the RAG Chain
        retriever = new_db.as_retriever()
        retrieval_chain = create_retrieval_chain(retriever, document_chain)

        response = retrieval_chain.invoke({"input": query.query})

        return {"response": response['answer']}
    except Exception as err:
        return {"error": f"Error occurred during handling user query: {str(err)}"}

@app.get("/clear")
async def clear():
    try:
        shutil.rmtree("faiss_db")
        os.makedirs("faiss_db", exist_ok=True)
        return {"message": "Cleared successfully"}
    except Exception as err:
        return {"error": f"Error occurred during clearing: {str(err)}"}

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
