from flask import Flask, render_template, request, jsonify, session
import requests
import os
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
import fitz  
from docx import Document
from rag_system import RAGSystem
import time

app = Flask(__name__)
app.secret_key = 'your-secret-key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Initialize RAG system
rag_system = RAGSystem()

if not os.path.exists('uploads'):
    os.makedirs('uploads')

def load_api_key():
    with open('key.txt', 'r') as f:
        return f.read().strip().replace('API: ', '')

def extract_text_from_file(filepath):
    filename = os.path.basename(filepath).lower()
    
    if filename.endswith('.txt'):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    
    elif filename.endswith('.pdf'):
        doc = fitz.open(filepath)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    
    elif filename.endswith('.docx'):
        doc = Document(filepath)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    
    elif filename.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
        image = Image.open(filepath)
        return pytesseract.image_to_string(image)
    
    else:
        return f"Unsupported file format: {filename}"

def groq_chat(messages, api_key=None):
    if not api_key:
        api_key = load_api_key()
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "messages": messages,
        "model": "llama-3.1-8b-instant",
        "temperature": 0.7
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        return response.json()
    except requests.exceptions.Timeout:
        return {'error': {'message': 'Request timed out. Please try again.', 'type': 'timeout'}}
    except requests.exceptions.ConnectionError:
        return {'error': {'message': 'Connection failed. Please check your internet connection.', 'type': 'connection_error'}}

@app.route('/')
def index():
    return render_template('chat.html')

@app.route('/upload', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['resume']
    role = request.form.get('role', '')
    company = request.form.get('company', '')
    location = request.form.get('location', '')
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not role or not company:
        return jsonify({'error': 'Role and company are required'}), 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    resume_content = extract_text_from_file(filepath)
    
    # Reset RAG system for new interview
    global rag_system
    rag_system = RAGSystem()
    
    # Process resume and job data with RAG
    rag_result = rag_system.process_resume_and_job(resume_content, role, company, location)
    
    resume_summary = resume_content[:1000] + "..." if len(resume_content) > 1000 else resume_content
    
    session['messages'] = [{
        "role": "system", 
        "content": f"You are conducting a technical interview for {role} at {company}. IMPORTANT: Ask questions ONLY about skills, technologies, and experiences explicitly mentioned in the candidate's resume. Do NOT invent project names or details. Use only what is actually written in their resume. Ask personalized, direct questions based on their real background."
    }]
    session['question_count'] = 0
    session['role'] = role
    session['company'] = company
    session['location'] = location
    
    result = groq_chat(session['messages'])
    if 'choices' in result and len(result['choices']) > 0:
        first_question = result['choices'][0]['message']['content']
        session['messages'].append({"role": "assistant", "content": first_question})
        return jsonify({
            'message': 'Resume uploaded successfully', 
            'first_question': first_question,
            'job_data_processed': rag_result['job_data_count']
        })
    else:
        return jsonify({'error': f'API Error: {result}'}), 500

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    user_message = request.json.get('message')
    
    if 'messages' not in session:
        session['messages'] = []
    
    role = session.get('role', '')
    company = session.get('company', '')
    
    if not role or not company:
        return jsonify({'error': 'Role and company information missing. Please upload resume again.'}), 400
    
    session['messages'].append({"role": "user", "content": user_message})
    session['question_count'] = session.get('question_count', 0) + 1
    
    # Generate enhanced prompt using RAG
    enhanced_prompt = rag_system.generate_enhanced_prompt(
        user_message, role, company, session['question_count']
    )
    
    session['messages'].append({"role": "system", "content": enhanced_prompt})
    
    try:
        result = groq_chat(session['messages'])
        if 'choices' in result and len(result['choices']) > 0:
            assistant_message = result['choices'][0]['message']['content']
            session['messages'].append({"role": "assistant", "content": assistant_message})
            return jsonify({
                'response': assistant_message, 
                'question_number': session['question_count'],
                'role': role,
                'company': company,
                'interview_complete': rag_system.is_interview_complete()
            })
        else:
            return jsonify({'error': f'API Error: {result}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/clear', methods=['POST'])
def clear_chat():
    global rag_system
    rag_system = RAGSystem()  # Reset RAG system
    session['messages'] = []
    session['question_count'] = 0
    return jsonify({'status': 'cleared'})

if __name__ == "__main__":
    app.run(debug=True)