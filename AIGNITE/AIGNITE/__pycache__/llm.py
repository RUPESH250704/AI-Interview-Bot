from flask import Flask, render_template, request, jsonify, session
import requests
import os
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
import fitz  
from docx import Document

app = Flask(__name__)
app.secret_key = 'your-secret-key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

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
    role = request.form.get('role', 'Data Analyst')
    company = request.form.get('company', 'TCS')
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    resume_content = extract_text_from_file(filepath)
    
    session['resume_content'] = resume_content
    session['role'] = role
    session['company'] = company
    session['question_count'] = 0
    session['sub_question_count'] = 0
    session['current_category'] = 'resume'
    
    difficulty = session.get('difficulty', 'medium')
    
    if difficulty == 'easy':
        tone = f"Ask ONE basic technical question about specific projects or skills mentioned in your resume. Reference actual project names or technologies. 10-12 words. Resume: {resume_content[:500]}"
    elif difficulty == 'hard':
        tone = f"Ask ONE advanced technical question about specific projects or technologies mentioned in your resume. Reference actual work experience. 10-12 words. Resume: {resume_content[:500]}"
    else:
        tone = f"Ask ONE intermediate technical question about specific skills or projects mentioned in your resume. Reference actual experience. 10-12 words. Resume: {resume_content[:500]}"
    
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
        prompt = f"Ask a follow-up question about: '{user_message}'. 10-12 words."
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
            'response': 'Interview complete. Thank you!',
            'interview_complete': True
        })
    
    difficulty = session.get('difficulty', 'medium')
    
    # Determine category and question type
    if session['question_count'] < 2:
        session['current_category'] = 'resume'
        if difficulty == 'easy':
            prompt = f"Ask a different basic technical question about specific projects, internships, or technologies mentioned in your resume. Reference actual names. 10-12 words. Resume: {session['resume_content'][:500]}"
        elif difficulty == 'hard':
            prompt = f"Ask an advanced technical question about specific projects or work experience mentioned in your resume. Reference actual achievements. 10-12 words. Resume: {session['resume_content'][:500]}"
        else:
            prompt = f"Ask an intermediate technical question about specific skills or projects mentioned in your resume. Reference actual work done. 10-12 words. Resume: {session['resume_content'][:500]}"
    elif session['question_count'] < 4:
        session['current_category'] = 'company'
        if difficulty == 'easy':
            prompt = f"Ask basic technical question about {session['company']} technology stack or development tools. 10-12 words."
        elif difficulty == 'hard':
            prompt = f"Ask advanced technical question about {session['company']} system architecture or scalability solutions. 10-12 words."
        else:
            prompt = f"Ask intermediate technical question about {session['company']} development practices or frameworks. 10-12 words."
    else:
        session['current_category'] = 'role'
        if difficulty == 'easy':
            prompt = f"Ask basic technical question about {session['role']} tools or programming languages used. 10-12 words."
        elif difficulty == 'hard':
            prompt = f"Ask advanced technical question about {session['role']} complex algorithms or system design. 10-12 words."
        else:
            prompt = f"Ask intermediate technical question about {session['role']} data processing or analysis methods. 10-12 words."
    
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
    app.run(debug=True)