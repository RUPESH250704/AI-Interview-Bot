from flask import Flask, render_template, request, jsonify, session
import requests
import os
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
import fitz  
from docx import Document
from search_engine import DuckDuckGoSearch

app = Flask(__name__)
app.secret_key = 'your-secret-key-hr'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

if not os.path.exists('uploads'):
    os.makedirs('uploads')

def load_api_key():
    with open('key.txt', 'r') as f:
        return f.read().strip().replace('API: ', '')

def extract_name_from_resume(resume_text):
    """Extract candidate name from resume text"""
    lines = resume_text.split('\n')
    for line in lines[:5]:
        line = line.strip()
        if len(line) > 2 and len(line) < 50 and not any(char.isdigit() for char in line):
            if not any(word in line.lower() for word in ['resume', 'cv', 'curriculum', 'profile', 'objective']):
                return line
    return 'Candidate'

def extract_text_from_file(filepath):
    filename = os.path.basename(filepath).lower()
    
    if filename.endswith('.txt'):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    
    elif filename.endswith('.pdf'):
        doc = fitz.open(filepath)
        text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text()
            blocks = page.get_text("dict")
            for block in blocks["blocks"]:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text += span["text"] + " "
        doc.close()
        return text.strip()
    
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
        if response.headers.get('content-type', '').startswith('application/json'):
            return response.json()
        else:
            return {'error': {'message': 'Invalid response format', 'type': 'format_error'}}
    except requests.exceptions.Timeout:
        return {'error': {'message': 'Request timed out. Please try again.', 'type': 'timeout'}}
    except requests.exceptions.ConnectionError:
        return {'error': {'message': 'Connection failed. Please check your internet connection.', 'type': 'connection_error'}}
    except Exception as e:
        return {'error': {'message': str(e), 'type': 'unknown_error'}}

@app.route('/')
def index():
    return render_template('hr_chat.html')

@app.route('/set_difficulty', methods=['POST'])
def set_difficulty():
    difficulty = request.json.get('difficulty')
    session['difficulty'] = difficulty
    return jsonify({'status': 'difficulty set', 'level': difficulty})

@app.route('/upload', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['resume']
    role = request.form.get('role', 'Software Engineer')
    company = request.form.get('company', 'TCS')
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    resume_content = extract_text_from_file(filepath)
    candidate_name = extract_name_from_resume(resume_content)
    
    # Initialize search engine for HR context
    search_engine = DuckDuckGoSearch()
    company_data = search_engine.search_company_info(company)
    
    session['candidate_name'] = candidate_name
    session['resume_content'] = resume_content
    session['role'] = role
    session['company'] = company
    session['company_data'] = company_data
    session['question_count'] = 0
    session['sub_question_count'] = 0
    session['current_category'] = 'resume'
    
    difficulty = session.get('difficulty', 'medium')
    
    if difficulty == 'easy':
        tone = f"Ask ONE basic HR question about experience or projects mentioned in your resume. Be friendly and encouraging. 10-12 words. Resume: {resume_content[:500]}"
    elif difficulty == 'hard':
        tone = f"Ask ONE challenging HR question about leadership or problem-solving from your resume experience. Be thorough and probing. 10-12 words. Resume: {resume_content[:500]}"
    else:
        tone = f"Ask ONE HR question about teamwork or achievements mentioned in your resume. Be professional and direct. 10-12 words. Resume: {resume_content[:500]}"
    
    session['messages'] = [{"role": "system", "content": tone}]
    
    result = groq_chat(session['messages'])
    if 'choices' in result and len(result['choices']) > 0:
        first_question = result['choices'][0]['message']['content']
        session['messages'].append({"role": "assistant", "content": first_question})
        return jsonify({
            'message': 'Resume uploaded successfully', 
            'first_question': first_question,
            'question_info': 'Resume Question 1/2'
        })
    else:
        return jsonify({'error': f'API Error: {result}'}), 500

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    user_message = request.json.get('message', '').lower().strip()
    
    if 'messages' not in session:
        return jsonify({'error': 'No session found'}), 400
    
    # Handle skip or don't know
    if user_message in ['skip', "don't know", 'dont know', 'idk']:
        return handle_skip()
    
    session['messages'].append({"role": "user", "content": user_message})
    
    # Check if we need sub-question or next main question
    if session['sub_question_count'] < 2:
        # Ask sub-question
        session['sub_question_count'] += 1
        prompt = f"Ask an HR follow-up question about: '{user_message}'. Focus on behavioral aspects. 10-12 words."
    else:
        # Move to next main question
        return get_next_main_question()
    
    session['messages'].append({"role": "system", "content": prompt})
    
    result = groq_chat(session['messages'])
    if 'choices' in result and len(result['choices']) > 0:
        assistant_message = result['choices'][0]['message']['content']
        session['messages'].append({"role": "assistant", "content": assistant_message})
        
        category = session['current_category'].title()
        main_q = (session['question_count'] % 2) + 1
        sub_q = session['sub_question_count']
        
        return jsonify({
            'response': assistant_message,
            'question_info': f'{category} Question {main_q}/2 - Sub {sub_q}/2'
        })
    else:
        return jsonify({'error': f'API Error: {result}'}), 500

def handle_skip():
    return get_next_main_question()

def get_next_main_question():
    session['question_count'] += 1
    session['sub_question_count'] = 0
    
    if session['question_count'] >= 6:
        return jsonify({
            'response': 'HR Interview complete. Thank you for your time!',
            'interview_complete': True
        })
    
    difficulty = session.get('difficulty', 'medium')
    
    # Determine category and question type
    if session['question_count'] < 2:
        session['current_category'] = 'resume'
        if difficulty == 'easy':
            prompt = f"Ask a different basic HR question about career goals or motivation from your resume. Be supportive. 10-12 words. Resume: {session['resume_content'][:500]}"
        elif difficulty == 'hard':
            prompt = f"Ask a challenging HR question about conflicts or failures mentioned in your resume experience. Be probing. 10-12 words. Resume: {session['resume_content'][:500]}"
        else:
            prompt = f"Ask an HR question about communication or collaboration from your resume projects. Be professional. 10-12 words. Resume: {session['resume_content'][:500]}"
    elif session['question_count'] < 4:
        session['current_category'] = 'company'
        company_context = ' '.join([item['content'][:100] for item in session.get('company_data', [])[:2]])
        if difficulty == 'easy':
            prompt = f"Ask basic HR question about {session['company']} culture. Context: {company_context}. 10-12 words."
        elif difficulty == 'hard':
            prompt = f"Ask challenging HR question about {session['company']} values fit. Context: {company_context}. 10-12 words."
        else:
            prompt = f"Ask HR question about {session['company']} growth opportunities. Context: {company_context}. 10-12 words."
    else:
        session['current_category'] = 'role'
        if difficulty == 'easy':
            prompt = f"Ask basic HR question about {session['role']} role interest or daily responsibilities understanding. 10-12 words."
        elif difficulty == 'hard':
            prompt = f"Ask challenging HR question about {session['role']} role challenges or performance under pressure. 10-12 words."
        else:
            prompt = f"Ask HR question about {session['role']} role strengths or professional development plans. 10-12 words."
    
    session['messages'] = [{"role": "system", "content": prompt}]
    
    result = groq_chat(session['messages'])
    if 'choices' in result and len(result['choices']) > 0:
        assistant_message = result['choices'][0]['message']['content']
        session['messages'].append({"role": "assistant", "content": assistant_message})
        
        category = session['current_category'].title()
        main_q = (session['question_count'] % 2) + 1
        
        return jsonify({
            'response': assistant_message,
            'question_info': f'{category} Question {main_q}/2'
        })
    else:
        return jsonify({'error': 'Failed to generate question'}), 500

@app.route('/clear', methods=['POST'])
def clear_chat():
    session.clear()
    return jsonify({'status': 'cleared'})

if __name__ == "__main__":
    app.run(debug=True, port=5001)
        return jsonify({'error': 'Failed to generate question'}), 500

@app.route('/clear', methods=['POST'])
def clear_chat():
    session.clear()
    return jsonify({'status': 'cleared'})

if __name__ == "__main__":
    app.run(debug=True, port=5001)