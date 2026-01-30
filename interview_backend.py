from flask import Flask, request, jsonify, session
from flask_cors import CORS
import requests
import os
import uuid
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
import fitz  
from docx import Document

app = Flask(__name__)
CORS(app)
app.secret_key = 'your-secret-key-for-interview-bot'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

if not os.path.exists('uploads'):
    os.makedirs('uploads')

# Store active sessions
active_sessions = {}

def load_api_key():
    try:
        with open('AIGNITE/key.txt', 'r') as f:
            return f.read().strip().replace('API: ', '')
    except:
        return None

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
    
    if not api_key:
        return {'error': {'message': 'API key not found', 'type': 'api_key_error'}}
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "messages": messages,
        "model": "llama-3.1-8b-instant",
        "temperature": 0.7,
        "max_tokens": 150
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        return response.json()
    except requests.exceptions.Timeout:
        return {'error': {'message': 'Request timed out. Please try again.', 'type': 'timeout'}}
    except requests.exceptions.ConnectionError:
        return {'error': {'message': 'Connection failed. Please check your internet connection.', 'type': 'connection_error'}}

@app.route('/api/start-interview', methods=['POST'])
def start_interview():
    try:
        # Get form data
        company = request.form.get('company')
        role = request.form.get('role')
        interview_type = request.form.get('type', 'Technical')
        
        if 'resume' not in request.files:
            return jsonify({'error': 'No resume file uploaded'}), 400
        
        file = request.files['resume']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save and process resume
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        resume_content = extract_text_from_file(filepath)
        
        # Create session
        session_id = str(uuid.uuid4())
        
        # Initialize interview context
        if interview_type.lower() == 'hr':
            system_prompt = f"""You are an HR interviewer for {company}. You're interviewing for the {role} position. 
            Ask behavioral and situational questions. Keep responses under 50 words. 
            Resume: {resume_content[:800]}"""
        else:
            system_prompt = f"""You are a technical interviewer for {company}. You're interviewing for the {role} position. 
            Ask technical questions based on the resume and role requirements. Keep responses under 50 words.
            Resume: {resume_content[:800]}"""
        
        # Store session data
        active_sessions[session_id] = {
            'company': company,
            'role': role,
            'type': interview_type,
            'resume_content': resume_content,
            'messages': [{"role": "system", "content": system_prompt}],
            'question_count': 0
        }
        
        # Generate first question
        first_question_prompt = f"Start the {interview_type} interview with a greeting and first question. Be professional and concise."
        active_sessions[session_id]['messages'].append({"role": "user", "content": first_question_prompt})
        
        result = groq_chat(active_sessions[session_id]['messages'])
        
        if 'choices' in result and len(result['choices']) > 0:
            first_question = result['choices'][0]['message']['content']
            active_sessions[session_id]['messages'].append({"role": "assistant", "content": first_question})
            active_sessions[session_id]['question_count'] = 1
            
            return jsonify({
                'session_id': session_id,
                'message': first_question,
                'status': 'Interview started successfully'
            })
        else:
            return jsonify({'error': f'Failed to generate question: {result}'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        session_id = data.get('session_id')
        user_message = data.get('message', '').strip()
        
        if not session_id or session_id not in active_sessions:
            return jsonify({'error': 'Invalid or expired session'}), 400
        
        session_data = active_sessions[session_id]
        
        # Add user message
        session_data['messages'].append({"role": "user", "content": user_message})
        
        # Check if interview should end
        if session_data['question_count'] >= 5:
            return jsonify({
                'message': 'Thank you for your time. The interview is now complete. We will get back to you soon.',
                'interview_complete': True
            })
        
        # Generate follow-up or next question
        if session_data['question_count'] < 5:
            follow_up_prompt = f"Ask a relevant follow-up question or move to the next topic. Keep it concise and professional."
            session_data['messages'].append({"role": "system", "content": follow_up_prompt})
            
            result = groq_chat(session_data['messages'])
            
            if 'choices' in result and len(result['choices']) > 0:
                ai_response = result['choices'][0]['message']['content']
                session_data['messages'].append({"role": "assistant", "content": ai_response})
                session_data['question_count'] += 1
                
                return jsonify({
                    'message': ai_response,
                    'question_count': session_data['question_count'],
                    'total_questions': 5
                })
            else:
                return jsonify({'error': f'Failed to generate response: {result}'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/end-interview', methods=['POST'])
def end_interview():
    try:
        data = request.json
        session_id = data.get('session_id')
        
        if session_id and session_id in active_sessions:
            # Clean up session
            del active_sessions[session_id]
        
        return jsonify({'message': 'Interview ended successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/session-status/<session_id>', methods=['GET'])
def get_session_status(session_id):
    if session_id in active_sessions:
        session_data = active_sessions[session_id]
        return jsonify({
            'active': True,
            'company': session_data['company'],
            'role': session_data['role'],
            'type': session_data['type'],
            'question_count': session_data['question_count']
        })
    else:
        return jsonify({'active': False}), 404

if __name__ == '__main__':
    app.run(debug=True, port=8000)