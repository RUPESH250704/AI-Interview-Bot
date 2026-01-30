import React, { useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import StaggeredMenu from './StaggeredMenu';
import Squares from './Squares';
import './App.css';

const Analysis = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { 
    interviewData, 
    messages = [], 
    summary = null, 
    terminated = false 
  } = location.state || {};

  const menuItems = [
    { label: 'Technical Interview', ariaLabel: 'Start mock interview', link: '/technical' },
    { label: 'HR interview', ariaLabel: 'HR interview', link: '/hr' },
    { label: 'Analysis', ariaLabel: 'View results', link: '/analysis' },
  ];

  // Scroll to top when component mounts
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  const handleNewInterview = () => {
    navigate('/technical');
  };

  // If no interview data, show empty state
  if (!interviewData) {
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
              <h1>Interview Analysis</h1>
              <div className="empty-analysis">
                <div className="empty-icon">📊</div>
                <h2>No Interview Data Available</h2>
                <p>Complete an interview to view detailed analysis and feedback.</p>
                <button onClick={handleNewInterview} className="btn">
                  Start New Interview
                </button>
              </div>
            </div>
          </div>
        </div>
      </>
    );
  }

  // Calculate additional metrics
  const userMessages = messages.filter(msg => msg.sender === 'user');
  const aiMessages = messages.filter(msg => msg.sender === 'ai');
  const totalQuestions = aiMessages.length - 1; // Subtract welcome message
  
  const answeredQuestions = userMessages.length;
  const completionRate = totalQuestions > 0 ? Math.min(100, (answeredQuestions / totalQuestions * 100)).toFixed(0) : 0;
  
  // Get category breakdown from summary
  const categoryBreakdown = summary?.category_breakdown || {};
  
  // Get improvements from summary
  const improvements = summary?.improvements || [];

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
          <div className="container analysis-container">
            <h1>Interview Analysis</h1>
            
            {terminated && (
              <div className="termination-alert">
                ⚠️ Interview was terminated early. Results are based on completed questions.
              </div>
            )}
            
            {/* Interview Info Card */}
            <div className="analysis-card info-card">
              <h2>Interview Details</h2>
              <div className="info-grid">
                <div className="info-item">
                  <span className="info-label">Company:</span>
                  <span className="info-value">{interviewData.company}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Role:</span>
                  <span className="info-value">{interviewData.role}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Type:</span>
                  <span className="info-value">{interviewData.type}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Difficulty:</span>
                  <span className="info-value">{interviewData.difficulty || 'Medium'}</span>
                </div>
              </div>
            </div>
            
            {/* Overall Score Card */}
            <div className="analysis-card score-card">
              <h2>Overall Performance</h2>
              <div className="score-main">
                <div className="score-circle">
                  <span className="score-number">{summary?.overall_score || '0'}</span>
                  <span className="score-out-of">/10</span>
                </div>
                <div className="score-details">
                  <h3 className="rating">{summary?.rating || 'No Rating'}</h3>
                  <p className="feedback">{summary?.feedback || 'Complete more questions for detailed feedback.'}</p>
                  <div className="completion-stats">
                    <span>Completion: {completionRate}%</span>
                    <span>Questions Answered: {answeredQuestions}</span>
                    <span>Total Questions: {totalQuestions}</span>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Category Breakdown */}
            {Object.keys(categoryBreakdown).length > 0 && (
              <div className="analysis-card category-card">
                <h2>Performance by Category</h2>
                <div className="category-grid">
                  {Object.entries(categoryBreakdown).map(([category, score]) => (
                    <div key={category} className="category-item">
                      <div className="category-header">
                        <span className="category-name">{category.charAt(0).toUpperCase() + category.slice(1)}</span>
                        <span className="category-score">{score}/10</span>
                      </div>
                      <div className="category-bar">
                        <div 
                          className="category-fill" 
                          style={{ width: `${score * 10}%` }}
                        ></div>
                      </div>
                      <div className="category-rating">
                        {score >= 8 ? 'Excellent' : 
                         score >= 6 ? 'Good' : 
                         score >= 4 ? 'Average' : 'Needs Improvement'}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Strengths and Improvements */}
            <div className="analysis-card improvements-card">
              <h2>Detailed Feedback</h2>
              <div className="feedback-grid">
                {summary?.strengths && summary.strengths.length > 0 && (
                  <div className="strengths-section">
                    <h3>✅ Strengths</h3>
                    <ul className="strengths-list">
                      {summary.strengths.map((strength, index) => (
                        <li key={index}>{strength}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {(improvements.length > 0 || summary?.improvements) && (
                  <div className="improvements-section">
                    <h3>📈 Areas for Improvement</h3>
                    <ul className="improvements-list">
                      {improvements.length > 0 ? (
                        improvements.map((improvement, index) => (
                          <li key={index}>{improvement}</li>
                        ))
                      ) : summary?.improvements ? (
                        summary.improvements.map((improvement, index) => (
                          <li key={index}>{improvement}</li>
                        ))
                      ) : (
                        <>
                          <li>Practice answering common technical questions in your field</li>
                          <li>Structure your answers using the STAR method</li>
                          <li>Provide specific examples from your experience</li>
                        </>
                      )}
                    </ul>
                  </div>
                )}
              </div>
            </div>
            
            {/* Interview Transcript */}
            <div className="analysis-card transcript-card">
              <h2>Interview Transcript</h2>
              <div className="transcript-container">
                {messages.length > 0 ? (
                  <div className="transcript-messages">
                    {messages.map((message, index) => (
                      <div key={index} className={`transcript-message ${message.sender}`}>
                        <div className="transcript-sender">
                          {message.sender === 'user' ? 'You' : 'Interviewer'}
                          <span className="transcript-time">
                            {message.timestamp?.toLocaleTimeString([], { 
                              hour: '2-digit', 
                              minute: '2-digit' 
                            }) || '--:--'}
                          </span>
                        </div>
                        <div className="transcript-text">{message.text}</div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="no-transcript">No transcript available.</p>
                )}
              </div>
            </div>
            
            {/* Recommendations */}
            <div className="analysis-card recommendations-card">
              <h2>Recommended Next Steps</h2>
              <div className="recommendations-content">
                <div className="recommendation-item">
                  <div className="recommendation-icon">📚</div>
                  <div className="recommendation-text">
                    <h3>Study Resources</h3>
                    <p>Review technical concepts related to {interviewData.role} role at {interviewData.company}</p>
                  </div>
                </div>
                <div className="recommendation-item">
                  <div className="recommendation-icon">🎯</div>
                  <div className="recommendation-text">
                    <h3>Practice More</h3>
                    <p>Try another interview with different difficulty settings to improve your skills</p>
                  </div>
                </div>
                <div className="recommendation-item">
                  <div className="recommendation-icon">💼</div>
                  <div className="recommendation-text">
                    <h3>Real Interview Prep</h3>
                    <p>Research {interviewData.company}'s interview process and company culture</p>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Action Buttons */}
            <div className="action-buttons">
              <button onClick={handleNewInterview} className="btn primary-btn">
                Start New Interview
              </button>
              <button 
                onClick={() => window.print()} 
                className="btn secondary-btn"
              >
                Print Report
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Analysis;