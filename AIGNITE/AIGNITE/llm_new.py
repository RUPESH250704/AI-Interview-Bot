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

@app.route('/upload', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    resume_content = extract_text_from_file(filepath)
    resume_summary = resume_content[:1000] + "..." if len(resume_content) > 1000 else resume_content
    
    session['messages'] = [{
        "role": "system", 
        "content": f"You are an AI interviewer conducting a professional interview. The candidate's resume: {resume_summary}. Ask ONE question at a time based on their background. Start with a brief greeting and ask the first relevant question. Keep responses concise and focused."
    }]
    session['question_count'] = 0
    
    result = groq_chat(session['messages'])
    if 'choices' in result and len(result['choices']) > 0:
        first_question = result['choices'][0]['message']['content']
        session['messages'].append({"role": "assistant", "content": first_question})
        return jsonify({'message': 'Resume uploaded successfully', 'first_question': first_question})
    else:
        return jsonify({'error': f'API Error: {result}'}), 500

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    user_message = request.json.get('message')
    
    if 'messages' not in session:
        session['messages'] = []
    
    session['messages'].append({"role": "user", "content": user_message})
    session['question_count'] = session.get('question_count', 0) + 1
    
    # Check if technical interview is complete (6 questions)
    if session['question_count'] >= 6:
        return jsonify({
            'response': 'Technical interview complete. Click here to start HR round.',
            'redirect_to_hr': True
        })
    
    if session['question_count'] % 3 == 0:  
        follow_up_prompt = f"Move to a different topic from the resume. Ask ONE short question (max 15 words)."
    else:
        follow_up_prompt = f"Based on '{user_message}', ask ONE short follow-up question (max 15 words). Be direct."
    session['messages'].append({"role": "system", "content": follow_up_prompt})
    
    try:
        result = groq_chat(session['messages'])
        if 'choices' in result and len(result['choices']) > 0:
            assistant_message = result['choices'][0]['message']['content']
            session['messages'].append({"role": "assistant", "content": assistant_message})
            return jsonify({'response': assistant_message, 'question_number': session['question_count']})
        else:
            return jsonify({'error': f'API Error: {result}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/hr_interview')
def hr_interview():
    return render_template('hr_chat.html')

@app.route('/start_hr', methods=['POST'])
def start_hr():
    session['hr_question_count'] = 0
    return jsonify({'first_question': 'Why do you want to join our company?'})

@app.route('/hr_chat', methods=['POST'])
def hr_chat():
    user_message = request.json.get('message')
    session['hr_question_count'] = session.get('hr_question_count', 0) + 1
    
    if session['hr_question_count'] >= 4:
        return jsonify({
            'response': 'HR interview complete. Thank you!',
            'interview_complete': True
        })
    
    hr_questions = [
        'Tell me about a challenging project you worked on.',
        'How do you handle working in a team?',
        'What are your career goals for the next 5 years?'
    ]
    
    if session['hr_question_count'] <= len(hr_questions):
        response = hr_questions[session['hr_question_count'] - 1]
    else:
        response = 'Thank you for your responses.'
    
    return jsonify({'response': response, 'question_number': session['hr_question_count']})

@app.route('/clear', methods=['POST'])
def clear_chat():
    session.clear()
    return jsonify({'status': 'cleared'})

if __name__ == "__main__":
    app.run(debug=True)