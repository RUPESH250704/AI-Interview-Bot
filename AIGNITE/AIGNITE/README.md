# AI Interview System with RAG

An enhanced AI-powered interview system that uses Retrieval-Augmented Generation (RAG) to provide contextual, role-specific interview questions based on your resume and real-time job market data.

## New Features

### 🎯 Role & Company Specific Interviews
- Input specific job role and company name
- Tailored questions based on position requirements
- Company-specific interview preparation

### 🔍 DuckDuckGo API Integration
- Real-time job market data retrieval
- Company information and culture insights
- Role-specific skill requirements
- Industry trends and expectations

### 🧠 RAG (Retrieval-Augmented Generation)
- Vector database storage using ChromaDB
- Semantic search for relevant context
- Enhanced question generation using resume + job data
- Contextual follow-up questions

### 📊 Vector Database
- Stores resume content with embeddings
- Indexes job market data for quick retrieval
- Semantic similarity matching
- Persistent storage for session continuity

## Installation

1. **Clone and Setup**
   ```bash
   cd AIGNITE
   python -m venv env
   env\Scripts\activate  # Windows
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   Or run the installation script:
   ```bash
   install.bat
   ```

3. **Setup API Key**
   - Add your Groq API key to `key.txt`
   - Format: `API: your_api_key_here`

## Usage

1. **Start the Application**
   ```bash
   python llm.py
   ```

2. **Open Browser**
   - Navigate to `http://localhost:5000`

3. **Upload Resume with Job Details**
   - Enter job role (e.g., "Software Engineer")
   - Enter company name (e.g., "Google")
   - Add location (optional)
   - Upload your resume file

4. **Interview Process**
   - System fetches relevant job data using DuckDuckGo API
   - Creates vector embeddings for resume and job data
   - Generates contextual questions using RAG
   - Provides role-specific interview experience

## Technical Architecture

### Components

1. **llm.py** - Main Flask application with enhanced endpoints
2. **vector_db.py** - ChromaDB integration for vector storage
3. **search_engine.py** - DuckDuckGo API wrapper for job data
4. **rag_system.py** - RAG implementation combining resume + job data
5. **templates/chat.html** - Enhanced UI with role/company inputs

### Data Flow

1. **Resume Upload** → Text extraction → Vector embedding → Storage
2. **Job Data Fetch** → DuckDuckGo API → Content processing → Vector storage
3. **Question Generation** → RAG retrieval → Context enhancement → LLM prompt
4. **Interview Flow** → Contextual responses → Semantic search → Enhanced questions

### Dependencies

- **ChromaDB**: Vector database for embeddings
- **Sentence Transformers**: Text embedding generation
- **DuckDuckGo API**: Job market data retrieval
- **Flask**: Web framework
- **Groq API**: LLM for question generation

## File Support

- **Documents**: PDF, DOCX, TXT
- **Images**: PNG, JPG, JPEG, BMP, TIFF (OCR)

## Features in Detail

### RAG System
- Combines resume content with real-time job data
- Uses semantic search for relevant context retrieval
- Generates enhanced prompts for better question quality
- Maintains conversation context across interview session

### Vector Database
- Persistent storage using ChromaDB
- Separate collections for resumes and job data
- Semantic similarity search capabilities
- Metadata tracking for source attribution

### Search Integration
- DuckDuckGo Instant Answer API
- Job requirements and skills data
- Company culture and values information
- Role-specific responsibilities and qualifications

## API Endpoints

- `POST /upload` - Upload resume with role/company data
- `POST /chat` - Enhanced chat with RAG-powered responses
- `POST /clear` - Clear session and reset interview

## Configuration

- **Vector DB Path**: `./chroma_db` (auto-created)
- **Upload Folder**: `./uploads`
- **Max File Size**: 16MB
- **Embedding Model**: `all-MiniLM-L6-v2`

## Troubleshooting

1. **Installation Issues**
   - Ensure Python 3.8+ is installed
   - Use virtual environment
   - Check internet connection for package downloads

2. **API Errors**
   - Verify Groq API key in `key.txt`
   - Check API rate limits
   - Ensure stable internet connection

3. **Vector DB Issues**
   - ChromaDB creates `./chroma_db` automatically
   - Clear database by deleting the folder if needed
   - Check disk space for embeddings storage

## Performance Notes

- First run may take longer due to model downloads
- Vector embeddings are cached for better performance
- Job data is fetched once per session
- Resume processing is optimized for various file formats