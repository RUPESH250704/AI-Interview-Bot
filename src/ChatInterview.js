import React, { useState, useRef, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import StaggeredMenu from './StaggeredMenu';
import Squares from './Squares';
import FaceDetector from './FaceDetector';
import './ChatInterview.css';

const ChatInterview = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { interviewData } = location.state || {};
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [interviewEnded, setInterviewEnded] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [currentQuestionInfo, setCurrentQuestionInfo] = useState('');
  const [summary, setSummary] = useState(null);
  const messagesEndRef = useRef(null);

  const menuItems = [
    { label: 'Technical Interview', ariaLabel: 'Start mock interview', link: '/technical' },
    { label: 'HR interview', ariaLabel: 'HR interview', link: '/hr' },
    { label: 'Analysis', ariaLabel: 'View results', link: '/analysis' },
  ];

  useEffect(() => {
    if (!interviewData) {
      navigate('/technical');
      return;
    }

    // Start interview session
    startInterviewSession();

    // Enter fullscreen with error handling
    const enterFullscreen = async () => {
      try {
        await document.documentElement.requestFullscreen();
      } catch (error) {
        console.log('Fullscreen not supported or denied');
      }
    };
    
    enterFullscreen();

    // Handle fullscreen change
    const handleFullscreenChange = () => {
      if (!document.fullscreenElement) {
        endInterview();
      }
    };

    // Handle tab visibility change
    const handleVisibilityChange = () => {
      if (document.hidden) {
        endInterview();
      }
    };

    // Disable copy/paste
    const handleKeyDown = (e) => {
      if (e.ctrlKey && (e.key === 'c' || e.key === 'v' || e.key === 'x')) {
        e.preventDefault();
      }
    };

    const handleContextMenu = (e) => {
      e.preventDefault();
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    document.addEventListener('visibilitychange', handleVisibilityChange);
    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('contextmenu', handleContextMenu);

    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('contextmenu', handleContextMenu);
    };
  }, [interviewData, navigate]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const startInterviewSession = async () => {
    try {
      const formData = new FormData();
      formData.append('company', interviewData.company);
      formData.append('role', interviewData.role);
      formData.append('resume', interviewData.resume);
      formData.append('difficulty', interviewData.difficulty || 'medium');

      const response = await fetch('http://localhost:5000/api/start-interview', {
        method: 'POST',
        body: formData
      });

      const result = await response.json();
      
      if (response.ok) {
        setSessionId(result.session_id);
        
        // Add welcome message
        const welcomeMessage = {
          id: 1,
          text: `Welcome to your ${interviewData.type} interview for ${interviewData.company} as a ${interviewData.role}. Let's begin!`,
          sender: 'ai',
          timestamp: new Date()
        };
        
        // Add first question
        const firstQuestion = {
          id: 2,
          text: result.first_question?.question || result.first_question?.text || "Let's start with your first question...",
          sender: 'ai',
          timestamp: new Date(),
          questionInfo: result.first_question?.category ? 
            `${result.first_question.category} Question 1/2` : 'Question 1/2'
        };
        
        setMessages([welcomeMessage, firstQuestion]);
        setCurrentQuestionInfo(firstQuestion.questionInfo);
      } else {
        console.error('Failed to start interview:', result.error);
        alert('Failed to start interview. Please try again.');
        navigate('/technical');
      }
    } catch (error) {
      console.error('Error starting interview:', error);
      alert('Failed to connect to interview service.');
      navigate('/technical');
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !sessionId || isLoading) return;

    const userMessage = {
      id: messages.length + 1,
      text: inputMessage,
      sender: 'user',
      timestamp: new Date()
    };

    const updatedMessagesBeforeAI = [...messages, userMessage];
    setMessages(updatedMessagesBeforeAI);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await fetch(`http://localhost:5000/api/submit-answer/${sessionId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ answer: inputMessage })
      });

      const result = await response.json();
      
      if (response.ok) {
        if (result.completed) {
          // Interview completed
          setInterviewEnded(true);
          if (result.summary) {
            setSummary(result.summary);
            
            // Add summary message
            const summaryMessage = {
              id: updatedMessagesBeforeAI.length + 1,
              text: `🎉 Interview Completed!\n\nOverall Score: ${result.summary.overall_score}/10\nRating: ${result.summary.rating}\n\n${result.summary.feedback}`,
              sender: 'ai',
              timestamp: new Date(),
              isSummary: true
            };
            
            const finalMessages = [...updatedMessagesBeforeAI, summaryMessage];
            setMessages(finalMessages);
            
            // Auto-navigate after delay - PASS ALL MESSAGES
            setTimeout(() => {
              navigate('/analysis', { 
                state: { 
                  interviewData,
                  messages: finalMessages, // CHANGED: Pass all messages including AI responses
                  summary: result.summary
                }
              });
            }, 5000);
          }
        } else if (result.next_question) {
          // Next question
          const aiResponse = {
            id: updatedMessagesBeforeAI.length + 1,
            text: result.next_question,
            sender: 'ai',
            timestamp: new Date(),
            questionInfo: result.question_info
          };
          
          const finalMessages = [...updatedMessagesBeforeAI, aiResponse];
          setMessages(finalMessages);
          setCurrentQuestionInfo(result.question_info);
        }
      } else {
        console.error('Chat error:', result.error);
      }
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSkipQuestion = async () => {
    if (!sessionId || isLoading) return;

    setIsLoading(true);

    try {
      const response = await fetch(`http://localhost:5000/api/skip-question/${sessionId}`, {
        method: 'POST'
      });

      const result = await response.json();
      
      if (response.ok) {
        if (result.completed) {
          setInterviewEnded(true);
          if (result.summary) {
            setSummary(result.summary);
            
            // Add summary message for skip
            const summaryMessage = {
              id: messages.length + 1,
              text: `🎉 Interview Completed!\n\nOverall Score: ${result.summary.overall_score}/10\nRating: ${result.summary.rating}\n\n${result.summary.feedback}`,
              sender: 'ai',
              timestamp: new Date(),
              isSummary: true
            };
            
            const finalMessages = [...messages, summaryMessage];
            setMessages(finalMessages);
            
            // Navigate with all messages
            setTimeout(() => {
              navigate('/analysis', { 
                state: { 
                  interviewData,
                  messages: finalMessages,
                  summary: result.summary,
                  terminated: false
                }
              });
            }, 3000);
          }
        } else if (result.next_question) {
          const aiResponse = {
            id: messages.length + 1,
            text: result.next_question,
            sender: 'ai',
            timestamp: new Date(),
            questionInfo: result.question_info
          };
          
          const updatedMessages = [...messages, aiResponse];
          setMessages(updatedMessages);
          setCurrentQuestionInfo(result.question_info);
        }
      }
    } catch (error) {
      console.error('Error skipping question:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleFaceViolation = () => {
    if (interviewEnded) return;
    endInterview('Face detection violation detected. Interview terminated.');
  };

  const endInterview = async (reason = 'Interview ended by user.') => {
    if (interviewEnded) return;
    setInterviewEnded(true);
    
    try {
      // Get summary before ending
      if (sessionId) {
        const summaryResponse = await fetch(`http://localhost:5000/api/get-summary/${sessionId}`);
        const summaryData = await summaryResponse.json();
        
        if (summaryResponse.ok) {
          setSummary(summaryData);
          
          // Add termination message
          const terminationMessage = {
            id: messages.length + 1,
            text: `⚠️ ${reason}\n\nFinal Score: ${summaryData.overall_score || 'N/A'}/10`,
            sender: 'ai',
            timestamp: new Date(),
            isTerminated: true
          };
          
          const finalMessages = [...messages, terminationMessage];
          setMessages(finalMessages);
          
          // Navigate after delay - PASS ALL MESSAGES
          setTimeout(() => {
            navigate('/analysis', { 
              state: { 
                interviewData,
                messages: finalMessages, // CHANGED: Pass all messages including termination
                summary: summaryData,
                terminated: true
              }
            });
          }, 3000);
        }
      }
      
      if (document.fullscreenElement) {
        document.exitFullscreen();
      }
    } catch (error) {
      console.log('Error ending interview:', error);
    }
  };

  if (!interviewData) {
    return null;
  }

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
        
        <div className="chat-container">
          <FaceDetector onViolation={handleFaceViolation} />
          <div className="chat-header">
            <h2>{interviewData.type} Interview - {interviewData.company}</h2>
            <div className="interview-info">
              <p><strong>Role:</strong> {interviewData.role}</p>
              <p><strong>Difficulty:</strong> {interviewData.difficulty || 'Medium'}</p>
              {currentQuestionInfo && (
                <p className="question-info">{currentQuestionInfo}</p>
              )}
              {sessionId && (
                <p className="session-id">Session: {sessionId.substring(0, 8)}...</p>
              )}
            </div>
            <button onClick={() => endInterview('Interview ended by user.')} className="end-interview-btn">
              End Interview
            </button>
          </div>
          
          <div className="chat-messages">
            {messages.map((message) => (
              <div key={message.id} className={`message ${message.sender} ${message.isSummary ? 'summary-message' : ''} ${message.isTerminated ? 'terminated-message' : ''}`}>
                <div className="message-content">
                  <div className="message-sender">
                    {message.sender === 'user' ? 'You' : 'Interviewer'}
                  </div>
                  <p style={{ 
                    color: message.sender === 'ai' ? '#ffffff' : '#333333',
                    margin: '0 0 10px 0',
                    lineHeight: '1.6',
                    whiteSpace: 'pre-wrap'
                  }}>
                    {message.text}
                  </p>
                  {message.questionInfo && (
                    <div className="question-info-badge">{message.questionInfo}</div>
                  )}
                  <span className="timestamp">
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="message ai">
                <div className="message-content">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          
          <div className="chat-input-area">
            {interviewEnded ? (
              <div className="interview-ended">
                <h3>Interview Ended</h3>
                {summary && (
                  <div className="summary-preview">
                    <p><strong>Score:</strong> {summary.overall_score || 'N/A'}/10</p>
                    <p><strong>Rating:</strong> {summary.rating || 'N/A'}</p>
                    <p className="redirect-message">Redirecting to analysis page...</p>
                  </div>
                )}
              </div>
            ) : (
              <>
                <div className="chat-input">
                  <textarea 
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    onCopy={(e) => e.preventDefault()}
                    onPaste={(e) => e.preventDefault()}
                    onCut={(e) => e.preventDefault()}
                    placeholder="Type your response..."
                    disabled={isLoading}
                    rows="3"
                    style={{ color: '#000000' }}
                  />
                  <button 
                    onClick={handleSendMessage} 
                    disabled={!inputMessage.trim() || isLoading}
                    className="send-btn"
                  >
                    Send
                  </button>
                </div>
                <div className="action-buttons">
                  <button 
                    onClick={handleSkipQuestion}
                    disabled={isLoading}
                    className="skip-btn"
                  >
                    Skip / Don't Know
                  </button>
                  <div className="shortcut-hint">
                    Press <kbd>Enter</kbd> to send • Press <kbd>Shift + Enter</kbd> for new line
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </>
  );
};

export default ChatInterview;