import pytest
import requests_mock
from main import upload_file, ask, clear

FASTAPI_URL = "http://localhost:8000"

@pytest.fixture
def real_pdf_file():
    file_path = 'attention.pdf'
    with open(file_path, 'rb') as f:
        file_content = f.read()
    return {'name': file_path, 'content': file_content}

def test_upload_pdf(real_pdf_file, requests_mock):
    mock_response = {"status": "success"}
    requests_mock.post(f"{FASTAPI_URL}/upload", json=mock_response)
    
    # Simulate the file upload
    files = {'file': (real_pdf_file['name'], real_pdf_file['content'], 'application/pdf')}
    response = upload_file(files)
    assert response == mock_response

def test_ask_query(requests_mock):
    mock_response = {"response": "This is a test response"}
    requests_mock.post(f"{FASTAPI_URL}/qna", json=mock_response)
    
    query = "Test query"
    response = ask(query)
    assert response == mock_response
    
    # Test handling of error response
    requests_mock.post(f"{FASTAPI_URL}/qna", status_code=500)
    response = ask(query)
    assert "error" in response

def test_clear_all(requests_mock):
    mock_response = {"status": "cleared"}
    requests_mock.get(f"{FASTAPI_URL}/clear", json=mock_response)
    
    response = clear()
    assert response == mock_response