@echo off
echo Installing AI Interview System with RAG capabilities...
echo.

echo Upgrading pip...
python -m pip install --upgrade pip

echo Activating virtual environment...
call env\Scripts\activate

echo Installing packages one by one to avoid conflicts...
pip install requests==2.31.0
pip install flask==3.0.0
pip install pytesseract==0.3.10
pip install Pillow==10.0.0
pip install pymupdf==1.24.0
pip install python-docx==1.1.0
pip install numpy==1.24.3
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install transformers==4.30.0
pip install sentence-transformers==2.2.2
pip install chromadb==0.4.15

echo.
echo Installation complete!
echo.
echo To run the application:
echo 1. Make sure you have your Groq API key in key.txt
echo 2. Run: python llm.py
echo 3. Open http://localhost:5000 in your browser
echo.
echo New Features:
echo - Role and Company specific interviews
echo - DuckDuckGo API integration for job data
echo - Vector database for RAG-based contextual questions
echo - Enhanced interview experience with job market insights
echo.
pause