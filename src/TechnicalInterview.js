import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import StaggeredMenu from './StaggeredMenu';
import Squares from './Squares';
import './App.css';

const TechnicalInterview = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    company: '',
    role: '',
    resume: null,
    difficulty: 'medium'
  });

  const menuItems = [
    { label: 'Technical Interview', ariaLabel: 'Start mock interview', link: '/technical' },
    { label: 'HR interview', ariaLabel: 'HR interview', link: '/hr' },
    { label: 'Analysis', ariaLabel: 'View results', link: '/analysis' },
  ];

  const roles = [
    'GET - Graduate Engineer Trainee',
    'Software Engineer',
    'Data Analyst',
    'AI Engineer'
  ];

  const companies = [
    'Google', 'Microsoft', 'Amazon', 'Apple', 'Meta', 'Netflix', 'Tesla', 'Uber'
  ];

  const difficulties = [
    { value: 'easy', label: 'Easy - Basic questions' },
    { value: 'medium', label: 'Medium - Standard difficulty' },
    { value: 'hard', label: 'Hard - Challenging questions' }
  ];

  const handleCompanyChange = (e) => {
    setFormData({ ...formData, company: e.target.value, role: '' });
  };

  const handleRoleChange = (e) => {
    setFormData({ ...formData, role: e.target.value });
  };

  const handleResumeChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Check if file is PDF
      if (file.type === 'application/pdf') {
        setFormData({ ...formData, resume: file });
      } else {
        alert('Please select a PDF file only.');
        e.target.value = '';
      }
    }
  };

  const handleDifficultyChange = (e) => {
    setFormData({ ...formData, difficulty: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (formData.company && formData.role && formData.resume) {
      navigate('/chat', {
        state: {
          interviewData: {
            type: 'Technical',
            company: formData.company,
            role: formData.role,
            resume: formData.resume,
            difficulty: formData.difficulty
          }
        }
      });
    }
  };

  const isFormValid = formData.company && formData.role && formData.resume;

  return (
    <>
      <StaggeredMenu
        position="left"
        items={menuItems}
        displayItemNumbering={false}
        menuButtonColor="#ffffff"
        openMenuButtonColor="#000"
        changeMenuColorOnOpen={true}
        colors={['#B19EEF', '#5227FF']}
        logoUrl="/logo.svg"
        accentColor="#5227FF"
      />
      
      <div className="app">
        <Squares 
          className="background-squares"
          speed={0.5}
          direction="diagonal"
          borderColor="#271E37"
          hoverFillColor="#222222"
          squareSize={40}
        />
        
        <div className="main-content">
          <div className="container">
            <h1>Technical Interview</h1>
            <p className="form-description">
              Start your technical interview practice. Select a company, role, and upload your resume.
            </p>
            
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label htmlFor="company">Select Company:</label>
                <select 
                  id="company" 
                  value={formData.company} 
                  onChange={handleCompanyChange} 
                  required
                  className="form-select"
                >
                  <option value="">Choose a company...</option>
                  {companies.map(company => (
                    <option key={company} value={company}>{company}</option>
                  ))}
                </select>
              </div>
              
              <div className="form-group">
                <label htmlFor="role">Select Role:</label>
                <select 
                  id="role" 
                  value={formData.role} 
                  onChange={handleRoleChange} 
                  disabled={!formData.company}
                  required
                  className="form-select"
                >
                  <option value="">{formData.company ? 'Choose a role...' : 'First select a company...'}</option>
                  {formData.company && roles.map(role => (
                    <option key={role} value={role}>{role}</option>
                  ))}
                </select>
              </div>
              
              <div className="form-group">
                <label htmlFor="difficulty">Select Difficulty:</label>
                <select 
                  id="difficulty" 
                  value={formData.difficulty} 
                  onChange={handleDifficultyChange}
                  required
                  className="form-select"
                >
                  {difficulties.map(diff => (
                    <option key={diff.value} value={diff.value}>{diff.label}</option>
                  ))}
                </select>
              </div>
              
              <div className="form-group">
                <label htmlFor="resume">Upload Resume (PDF only):</label>
                <div className="file-upload-area">
                  <input 
                    type="file" 
                    id="resume" 
                    accept=".pdf" 
                    onChange={handleResumeChange}
                    required
                    className="file-input"
                  />
                  <label htmlFor="resume" className="file-label">
                    <span className="file-icon">📄</span>
                    <span>Click to upload PDF resume</span>
                  </label>
                  {formData.resume && (
                    <div className="file-info">
                      <div className="file-name">
                        <span className="file-icon-small">📄</span>
                        {formData.resume.name}
                      </div>
                      <div className="file-size">
                        {(formData.resume.size / 1024 / 1024).toFixed(2)} MB
                      </div>
                    </div>
                  )}
                </div>
                <p className="file-hint">Only PDF files are accepted. Max size: 16MB</p>
              </div>
              
              <button 
                type="submit" 
                className="btn" 
                disabled={!isFormValid}
              >
                {isFormValid ? (
                  <>
                    <span className="btn-icon">🚀</span>
                    Start Technical Interview
                  </>
                ) : (
                  'Fill all fields to continue'
                )}
              </button>
            </form>
          </div>
        </div>
      </div>
    </>
  );
};

export default TechnicalInterview;