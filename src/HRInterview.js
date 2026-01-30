import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import StaggeredMenu from './StaggeredMenu';
import Squares from './Squares';
import './App.css';

const HRInterview = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    company: '',
    role: '',
    resume: null
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

  const handleCompanyChange = (e) => {
    setFormData({ ...formData, company: e.target.value, role: '' });
  };

  const handleRoleChange = (e) => {
    setFormData({ ...formData, role: e.target.value });
  };

  const handleResumeChange = (e) => {
    const file = e.target.files[0];
    if (file && file.type === 'application/pdf') {
      setFormData({ ...formData, resume: file });
    } else {
      alert('Please select a PDF file only.');
      e.target.value = '';
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (formData.company && formData.role && formData.resume) {
      navigate('/chat', {
        state: {
          interviewData: {
            type: 'HR',
            company: formData.company,
            role: formData.role,
            resume: formData.resume
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
            <h1>HR Interview</h1>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label htmlFor="company">Select Company:</label>
                <select 
                  id="company" 
                  value={formData.company} 
                  onChange={handleCompanyChange} 
                  required
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
                >
                  <option value="">{formData.company ? 'Choose a role...' : 'First select a company...'}</option>
                  {formData.company && roles.map(role => (
                    <option key={role} value={role}>{role}</option>
                  ))}
                </select>
              </div>
              
              <div className="form-group">
                <label htmlFor="resume">Upload Resume (PDF only):</label>
                <input 
                  type="file" 
                  id="resume" 
                  accept=".pdf" 
                  onChange={handleResumeChange}
                  required
                />
                {formData.resume && (
                  <div className="file-info">
                    Selected: {formData.resume.name} ({(formData.resume.size / 1024 / 1024).toFixed(2)} MB)
                  </div>
                )}
              </div>
              
              <button type="submit" className="btn" disabled={!isFormValid}>
                Start HR Interview
              </button>
            </form>
          </div>
        </div>
      </div>
    </>
  );
};

export default HRInterview;