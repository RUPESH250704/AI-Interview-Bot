from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import requests
import os
import uuid
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
import fitz  
from docx import Document
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Enable CORS for frontend
CORS(app, origins=["http://localhost:3000", "http://localhost:5173"], supports_credentials=True)

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

# Store active interviews in memory (like your previous backend)
active_interviews = {}

class InterviewSession:
    def __init__(self, session_id, company, role, resume_content, difficulty="medium"):
        self.session_id = session_id
        self.company = company
        self.role = role
        self.resume_content = resume_content
        self.difficulty = difficulty
        
        # Initialize interview state
        self.question_count = 0
        self.sub_question_count = 0
        self.current_category = 'resume'
        self.total_questions = 6  # 2 questions per category
        self.questions_asked = 0
        self.interview_data = {
            "session_id": session_id,
            "company": company,
            "role": role,
            "resume_content": resume_content[:500],  # Store first 500 chars
            "difficulty": difficulty,
            "start_time": datetime.now().isoformat(),
            "questions": [],
            "status": "active"
        }
        
        # System messages based on difficulty
        self.difficulty_settings = {
            "easy": {
                "resume": "Ask ONE basic technical question about specific projects or skills mentioned in the resume. Reference actual project names or technologies. 10-12 words.",
                "company": "Ask basic technical question about {company} technology stack or development tools. 10-12 words.",
                "role": "Ask basic technical question about {role} tools or programming languages used. 10-12 words."
            },
            "medium": {
                "resume": "Ask ONE intermediate technical question about specific skills or projects mentioned in the resume. Reference actual experience. 10-12 words.",
                "company": "Ask intermediate technical question about {company} development practices or frameworks. 10-12 words.",
                "role": "Ask intermediate technical question about {role} data processing or analysis methods. 10-12 words."
            },
            "hard": {
                "resume": "Ask ONE advanced technical question about specific projects or technologies mentioned in the resume. Reference actual work experience. 10-12 words.",
                "company": "Ask advanced technical question about {company} system architecture or scalability solutions. 10-12 words.",
                "role": "Ask advanced technical question about {role} complex algorithms or system design. 10-12 words."
            }
        }
        
        # Initialize conversation
        self.messages = []
        self.generate_first_question()
    
    def generate_first_question(self):
        """Generate the first question based on resume"""
        category = 'resume'
        template = self.difficulty_settings[self.difficulty][category]
        
        if category == 'resume':
            prompt = f"{template} Resume: {self.resume_content[:500]}"
        else:
            prompt = template.format(company=self.company, role=self.role)
        
        self.messages = [{"role": "system", "content": prompt}]
        
        result = groq_chat(self.messages)
        if 'choices' in result and len(result['choices']) > 0:
            first_question = result['choices'][0]['message']['content']
            self.messages.append({"role": "assistant", "content": first_question})
            
            # Store question data
            question_data = {
                "question_number": 1,
                "category": category,
                "question_type": "main",
                "question_text": first_question,
                "timestamp": datetime.now().isoformat()
            }
            self.interview_data["questions"].append(question_data)
            
            self.questions_asked += 1
            self.current_category = category
            
            return first_question
        return None
    
    def get_next_question(self):
        """Get the next question in sequence"""
        if self.questions_asked >= self.total_questions:
            return None
        
        return {
            "question": self.messages[-1]["content"] if self.messages else "",
            "category": self.current_category,
            "question_number": self.questions_asked,
            "sub_question_number": self.sub_question_count
        }
    
    def submit_answer(self, answer):
        """Submit answer and get next question or evaluation"""
        if self.questions_asked >= self.total_questions:
            return {"completed": True}
        
        # Store the answer for current question
        if self.interview_data["questions"]:
            last_question = self.interview_data["questions"][-1]
            last_question["answer"] = answer
            last_question["answer_timestamp"] = datetime.now().isoformat()
        
        # Add user message to conversation
        self.messages.append({"role": "user", "content": answer})
        
        # Check if we need sub-question or next main question
        if self.sub_question_count < 1:  # Changed from 2 to 1 for less complexity
            # Ask sub-question
            self.sub_question_count += 1
            prompt = f"Ask a follow-up question about: '{answer}'. 10-12 words."
            
            self.messages.append({"role": "system", "content": prompt})
            
            result = groq_chat(self.messages)
            if 'choices' in result and len(result['choices']) > 0:
                assistant_message = result['choices'][0]['message']['content']
                self.messages.append({"role": "assistant", "content": assistant_message})
                
                # Store sub-question
                sub_question_data = {
                    "question_number": self.questions_asked,
                    "category": self.current_category,
                    "question_type": "sub",
                    "question_text": assistant_message,
                    "timestamp": datetime.now().isoformat()
                }
                self.interview_data["questions"].append(sub_question_data)
                
                return {
                    "next_question": assistant_message,
                    "category": self.current_category.title(),
                    "question_info": f"{self.current_category.title()} Question {(self.question_count % 2) + 1}/2 - Sub {self.sub_question_count}/1",
                    "completed": False
                }
        else:
            # Move to next main question
            return self.generate_next_main_question()
        
        return {"error": "Failed to generate question"}
    
    def generate_next_main_question(self):
        """Generate the next main question"""
        self.question_count += 1
        self.sub_question_count = 0
        
        if self.question_count >= self.total_questions // 2:  # 2 questions per category
            # Interview complete
            self.interview_data["status"] = "completed"
            self.interview_data["end_time"] = datetime.now().isoformat()
            
            # Generate final evaluation
            evaluation = self.get_final_evaluation()
            
            return {
                "completed": True,
                "summary": evaluation
            }
        
        # Determine next category
        if self.question_count < 2:
            self.current_category = 'resume'
        elif self.question_count < 4:
            self.current_category = 'company'
        else:
            self.current_category = 'role'
        
        # Generate question based on category and difficulty
        template = self.difficulty_settings[self.difficulty][self.current_category]
        
        if self.current_category == 'resume':
            prompt = f"{template} Resume: {self.resume_content[:500]}"
        else:
            prompt = template.format(company=self.company, role=self.role)
        
        self.messages = [{"role": "system", "content": prompt}]
        
        result = groq_chat(self.messages)
        if 'choices' in result and len(result['choices']) > 0:
            assistant_message = result['choices'][0]['message']['content']
            self.messages.append({"role": "assistant", "content": assistant_message})
            
            # Store main question
            question_data = {
                "question_number": self.questions_asked + 1,
                "category": self.current_category,
                "question_type": "main",
                "question_text": assistant_message,
                "timestamp": datetime.now().isoformat()
            }
            self.interview_data["questions"].append(question_data)
            
            self.questions_asked += 1
            
            return {
                "next_question": assistant_message,
                "category": self.current_category.title(),
                "question_info": f"{self.current_category.title()} Question {(self.question_count % 2) + 1}/2",
                "completed": False
            }
        
        return {"error": "Failed to generate question"}
    
    def get_final_evaluation(self):
        """Generate final evaluation of the interview"""
        # Evaluate all answers (simplified version)
        total_score = 0
        questions_with_answers = [q for q in self.interview_data["questions"] if "answer" in q]
        
        if not questions_with_answers:
            return {
                "overall_score": 0,
                "rating": "No answers provided",
                "feedback": "Please complete the interview to get evaluation.",
                "total_questions": self.questions_asked,
                "category_breakdown": {}
            }
        
        # Simple scoring based on answer length (you can enhance this with LLM evaluation)
        for q in questions_with_answers:
            answer_length = len(q.get("answer", "").split())
            if answer_length < 10:
                score = 4
            elif answer_length < 30:
                score = 6
            else:
                score = 8
            total_score += score
        
        avg_score = total_score / len(questions_with_answers)
        
        # Categorize performance
        if avg_score >= 7:
            rating = "Good"
            feedback = "You demonstrated good technical knowledge. Keep practicing specific examples."
        elif avg_score >= 5:
            rating = "Fair"
            feedback = "You have basic understanding. Focus on providing more detailed answers."
        else:
            rating = "Needs Improvement"
            feedback = "Practice more and prepare specific examples from your experience."
        
        # Category breakdown
        category_scores = {}
        for q in questions_with_answers:
            cat = q['category']
            if cat not in category_scores:
                category_scores[cat] = []
            answer_length = len(q.get("answer", "").split())
            category_scores[cat].append(min(10, answer_length / 5))  # Simple scoring
        
        category_breakdown = {}
        for cat, scores in category_scores.items():
            category_breakdown[cat] = round(sum(scores) / len(scores), 1)
        
        return {
            "overall_score": round(avg_score, 1),
            "rating": rating,
            "feedback": feedback,
            "total_questions": self.questions_asked,
            "questions_answered": len(questions_with_answers),
            "category_breakdown": category_breakdown,
            "interview_data": self.interview_data
        }
    
    def skip_question(self):
        """Handle skip/don't know"""
        return self.generate_next_main_question()

# API Routes similar to your original backend
@app.route('/api/start-interview', methods=['POST'])
def start_interview():
    """Start a new interview session with resume upload"""
    try:
        if 'resume' not in request.files:
            return jsonify({"error": "No resume file provided"}), 400
        
        file = request.files['resume']
        company = request.form.get('company', 'TCS')
        role = request.form.get('role', 'Data Analyst')
        difficulty = request.form.get('difficulty', 'medium')
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Extract text from resume
        resume_content = extract_text_from_file(filepath)
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Create interview session
        interview = InterviewSession(session_id, company, role, resume_content, difficulty)
        active_interviews[session_id] = interview
        
        # Get first question
        first_question = interview.get_next_question()
        
        return jsonify({
            "session_id": session_id,
            "company": company,
            "role": role,
            "first_question": first_question,
            "difficulty": difficulty,
            "message": "Interview session started successfully",
            "progress": {
                "current": interview.questions_asked,
                "total": interview.total_questions
            }
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/get-question/<session_id>', methods=['GET'])
def get_question(session_id):
    """Get current question for the session"""
    if session_id not in active_interviews:
        return jsonify({"error": "Session not found"}), 404
    
    interview = active_interviews[session_id]
    
    if interview.questions_asked >= interview.total_questions:
        return jsonify({"completed": True})
    
    question_info = interview.get_next_question()
    
    return jsonify({
        "question": question_info,
        "progress": {
            "current": interview.questions_asked,
            "total": interview.total_questions
        }
    })

@app.route('/api/submit-answer/<session_id>', methods=['POST'])
def submit_answer(session_id):
    """Submit answer for current question"""
    if session_id not in active_interviews:
        return jsonify({"error": "Session not found"}), 404
    
    data = request.json
    answer = data.get('answer', '')
    
    if not answer:
        return jsonify({"error": "Missing answer"}), 400
    
    interview = active_interviews[session_id]
    result = interview.submit_answer(answer)
    
    return jsonify(result)

@app.route('/api/skip-question/<session_id>', methods=['POST'])
def skip_question(session_id):
    """Skip current question"""
    if session_id not in active_interviews:
        return jsonify({"error": "Session not found"}), 404
    
    interview = active_interviews[session_id]
    result = interview.skip_question()
    
    return jsonify(result)

@app.route('/api/get-summary/<session_id>', methods=['GET'])
def get_summary(session_id):
    """Get interview summary"""
    if session_id not in active_interviews:
        return jsonify({"error": "Session not found"}), 404
    
    interview = active_interviews[session_id]
    summary = interview.get_final_evaluation()
    
    return jsonify(summary)

@app.route('/api/session-status/<session_id>', methods=['GET'])
def session_status(session_id):
    """Check session status"""
    if session_id not in active_interviews:
        return jsonify({"error": "Session not found"}), 404
    
    interview = active_interviews[session_id]
    
    return jsonify({
        "session_id": session_id,
        "company": interview.company,
        "role": interview.role,
        "difficulty": interview.difficulty,
        "questions_asked": interview.questions_asked,
        "total_questions": interview.total_questions,
        "current_category": interview.current_category,
        "status": interview.interview_data["status"]
    })

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(active_interviews)
    })

# Keep your original routes for backward compatibility
@app.route('/')
def index():
    return render_template('chat.html')

@app.route('/set_difficulty', methods=['POST'])
def set_difficulty():
    difficulty = request.json.get('difficulty')
    session['difficulty'] = difficulty
    return jsonify({'status': 'difficulty set', 'level': difficulty})

@app.route('/clear', methods=['POST'])
def clear_chat():
    session.clear()
    return jsonify({'status': 'cleared'})

if __name__ == "__main__":
    app.run(debug=True, port=5000)