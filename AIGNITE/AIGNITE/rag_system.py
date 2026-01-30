from vector_db import VectorDB
from search_engine import DuckDuckGoSearch
import json

class RAGSystem:
    def __init__(self):
        self.vector_db = VectorDB()
        self.search_engine = DuckDuckGoSearch()
        self.interview_structure = {
            'resume': {'main_count': 0, 'max_main': 2, 'sub_count': 0, 'max_sub': 2},
            'company': {'main_count': 0, 'max_main': 2, 'sub_count': 0, 'max_sub': 2},
            'role': {'main_count': 0, 'max_main': 2, 'sub_count': 0, 'max_sub': 2}
        }
        self.current_topic = 'resume'
        self.in_sub_questions = False
    
    def process_resume_and_job(self, resume_text, role, company, location=""):
        resume_metadata = {
            'type': 'resume',
            'role': role,
            'company': company,
            'location': location
        }
        resume_id = self.vector_db.add_resume(resume_text, resume_metadata)
        
        job_results = self.search_engine.search_job_info(role, company, location)
        company_results = self.search_engine.search_company_info(company)
        role_results = self.search_engine.get_role_requirements(role)
        
        all_job_data = job_results + company_results + role_results
        job_ids = []
        
        for result in all_job_data:
            job_metadata = {
                'type': result['type'],
                'role': role,
                'company': company,
                'source': result['source']
            }
            job_id = self.vector_db.add_job_data(result['content'], job_metadata)
            job_ids.append(job_id)
        
        return {
            'resume_id': resume_id,
            'job_ids': job_ids,
            'job_data_count': len(all_job_data)
        }
    
    def get_contextual_info(self, query, role, company):
        resume_results = self.vector_db.search_similar_resume(query, n_results=2)
        job_query = f"{query} {role} {company}"
        job_results = self.vector_db.search_similar_jobs(job_query, n_results=3)
        
        context = {
            'resume_context': [],
            'job_context': []
        }
        
        if resume_results['documents']:
            for i, doc in enumerate(resume_results['documents'][0]):
                context['resume_context'].append({
                    'content': doc[:500] + "..." if len(doc) > 500 else doc,
                    'metadata': resume_results['metadatas'][0][i] if resume_results['metadatas'] else {}
                })
        
        if job_results['documents']:
            for i, doc in enumerate(job_results['documents'][0]):
                context['job_context'].append({
                    'content': doc,
                    'metadata': job_results['metadatas'][0][i] if job_results['metadatas'] else {}
                })
        
        return context
    
    def should_change_topic(self, user_message):
        skip_words = ['skip', "don't know", "dont know", "i don't know", "no idea", "not sure"]
        return any(word in user_message.lower() for word in skip_words)
    
    def get_next_topic(self):
        topics = ['resume', 'company', 'role']
        
        for topic in topics:
            if self.interview_structure[topic]['main_count'] < self.interview_structure[topic]['max_main']:
                return topic
        
        return 'complete'
    
    def is_interview_complete(self):
        """Check if all questions have been asked"""
        return all(
            self.interview_structure[topic]['main_count'] >= self.interview_structure[topic]['max_main']
            for topic in ['resume', 'company', 'role']
        )
    
    def generate_enhanced_prompt(self, user_message, role, company, question_count):
        # Debug: Print current state
        print(f"Current topic: {self.current_topic}, Main count: {self.interview_structure[self.current_topic]['main_count']}, Sub count: {self.interview_structure[self.current_topic]['sub_count']}, In sub: {self.in_sub_questions}")
        
        # Check if user wants to skip
        if self.should_change_topic(user_message):
            if self.in_sub_questions:
                # Skip current main question entirely, move to next main
                self.interview_structure[self.current_topic]['main_count'] += 1
                self.interview_structure[self.current_topic]['sub_count'] = 0
                self.in_sub_questions = False
                self.current_topic = self.get_next_topic()
            else:
                # Skip main question, move to next main
                self.interview_structure[self.current_topic]['main_count'] += 1
                self.current_topic = self.get_next_topic()
        
        # If answered and not in sub-questions, move to sub-questions
        elif not self.in_sub_questions and not self.should_change_topic(user_message):
            self.in_sub_questions = True
            self.interview_structure[self.current_topic]['sub_count'] = 1
        
        # If in sub-questions and answered
        elif self.in_sub_questions:
            self.interview_structure[self.current_topic]['sub_count'] += 1
            
            # If max sub-questions reached, move to next main
            if self.interview_structure[self.current_topic]['sub_count'] > self.interview_structure[self.current_topic]['max_sub']:
                self.interview_structure[self.current_topic]['main_count'] += 1
                self.interview_structure[self.current_topic]['sub_count'] = 0
                self.in_sub_questions = False
                self.current_topic = self.get_next_topic()
        
        if self.current_topic == 'complete':
            return "The interview is complete. Thank you for your time. We will get back to you soon."
        
        context = self.get_contextual_info(user_message, role, company)
        
        # Build context string
        context_parts = []
        if context['resume_context']:
            context_parts.append("RESUME CONTEXT:")
            for item in context['resume_context']:
                context_parts.append(f"- {item['content']}")
        
        if context['job_context']:
            context_parts.append("\nJOB CONTEXT:")
            for item in context['job_context']:
                context_parts.append(f"- {item['content']}")
        
        context_string = "\n".join(context_parts)
        
        # Generate prompts based on current state
        if not self.in_sub_questions:
            # Main question
            if self.current_topic == 'resume':
                prompt = f"Ask ONE technical question about a skill or technology actually mentioned in the candidate's resume. Use ONLY what is explicitly written in their resume. Do NOT invent project names. Only ask the question (max 25 words).\n\n{context_string}"
            elif self.current_topic == 'company':
                prompt = f"Ask ONE short technical question about tools or processes. Do NOT mention company name or transitions. Only ask the question (max 20 words).\n\n{context_string}"
            elif self.current_topic == 'role':
                prompt = f"Ask ONE short technical question about {role} methodology or concept. Do NOT mention role or transitions. Only ask the question (max 20 words).\n\n{context_string}"
        else:
            # Sub question based on answer
            prompt = f"Ask ONE follow-up question based on their answer. Use ONLY information from their actual resume. Do NOT invent details (max 20 words).\n\nUser said: {user_message}\n\nResume context: {context_string[:200]}"
        
        return prompt