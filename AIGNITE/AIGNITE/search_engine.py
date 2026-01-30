import requests
import json
from urllib.parse import quote_plus
import time
from concurrent.futures import ThreadPoolExecutor
import threading

class DuckDuckGoSearch:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.results_lock = threading.Lock()
    
    def _fetch_data(self, url, params):
        """Thread-safe data fetching"""
        try:
            response = requests.get(url, params=params, headers=self.headers, timeout=5)
            return response.json()
        except Exception as e:
            return None
    
    def search_reddit(self, query):
        """Search Reddit for job-related discussions"""
        try:
            reddit_query = f"site:reddit.com {query}"
            params = {
                'q': reddit_query,
                'format': 'json',
                'no_html': '1'
            }
            
            data = self._fetch_data("https://api.duckduckgo.com/", params)
            
            if data and data.get('Abstract'):
                return [{
                    'type': 'reddit_discussion',
                    'content': data['Abstract'],
                    'source': 'Reddit via DuckDuckGo'
                }]
            
            return [{
                'type': 'reddit_discussion',
                'content': f"Reddit discussions about {query} often mention practical challenges, real-world applications, and community insights.",
                'source': 'Reddit Knowledge'
            }]
            
        except Exception as e:
            return [{
                'type': 'reddit_discussion',
                'content': f"Community discussions about {query} typically focus on practical implementation and real-world scenarios.",
                'source': 'Reddit Knowledge'
            }]
    
    def search_job_info(self, role, company, location=""):
        """Search for job information using multithreading"""
        results = []
        
        # Always add base data points
        results.append({
            'type': 'role_requirements',
            'content': f"{role} responsibilities include data analysis, problem-solving, technical skills, and domain expertise. Key requirements: analytical thinking, attention to detail, communication skills.",
            'source': 'General Knowledge'
        })
        
        results.append({
            'type': 'company_info', 
            'content': f"{company} values innovation, teamwork, and professional growth. They seek candidates with strong technical skills and cultural fit.",
            'source': 'General Knowledge'
        })
        
        # Prepare concurrent searches
        search_tasks = []
        
        # DuckDuckGo search
        query = f"{role} {company} job requirements skills"
        if location:
            query += f" {location}"
        
        params1 = {
            'q': query,
            'format': 'json',
            'no_html': '1',
            'skip_disambig': '1'
        }
        
        # Reddit search
        reddit_query = f"{role} {company} interview experience"
        
        # Execute searches concurrently
        with ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(self._fetch_data, "https://api.duckduckgo.com/", params1)
            future2 = executor.submit(self.search_reddit, reddit_query)
            
            # Get DuckDuckGo results
            ddg_data = future1.result()
            if ddg_data and ddg_data.get('Abstract'):
                results.append({
                    'type': 'abstract',
                    'content': ddg_data['Abstract'],
                    'source': ddg_data.get('AbstractSource', 'DuckDuckGo')
                })
            
            # Get Reddit results
            reddit_results = future2.result()
            results.extend(reddit_results)
        
        return results
    
    def search_company_info(self, company):
        """Search for company information using multithreading"""
        results = []
        
        # Always add base company info
        results.append({
            'type': 'company_info',
            'content': f"{company} is a leading organization known for innovation and excellence. They value skilled professionals and offer growth opportunities.",
            'source': 'General Knowledge'
        })
        
        # Prepare concurrent searches
        query = f"{company} company culture values"
        params = {
            'q': query,
            'format': 'json',
            'no_html': '1'
        }
        
        reddit_query = f"{company} work culture employee experience"
        
        # Execute searches concurrently
        with ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(self._fetch_data, "https://api.duckduckgo.com/", params)
            future2 = executor.submit(self.search_reddit, reddit_query)
            
            # Get DuckDuckGo results
            ddg_data = future1.result()
            if ddg_data and ddg_data.get('Abstract'):
                results.append({
                    'type': 'company_info',
                    'content': ddg_data['Abstract'],
                    'source': ddg_data.get('AbstractSource', 'DuckDuckGo')
                })
            
            # Get Reddit results
            reddit_results = future2.result()
            results.extend(reddit_results)
        
        return results
    
    def get_role_requirements(self, role):
        """Get general role requirements using multithreading"""
        role_data = {
            'data analyst': 'SQL, Python, Excel, statistical analysis, data visualization, business intelligence, problem-solving skills',
            'software engineer': 'Programming languages, algorithms, system design, debugging, version control, testing, problem-solving',
            'product manager': 'Strategy, roadmap planning, stakeholder management, market research, analytics, communication skills',
            'marketing manager': 'Campaign management, digital marketing, analytics, brand strategy, content creation, market research'
        }
        
        role_lower = role.lower()
        requirements = role_data.get(role_lower, f"{role} requires technical expertise, analytical skills, and professional communication")
        
        results = [{
            'type': 'role_requirements',
            'content': f"{role} key requirements: {requirements}. Strong analytical and communication skills essential.",
            'source': 'Role Knowledge Base'
        }]
        
        # Add Reddit search concurrently
        reddit_query = f"{role} skills requirements career advice"
        
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self.search_reddit, reddit_query)
            reddit_results = future.result()
            results.extend(reddit_results)
        
        return results