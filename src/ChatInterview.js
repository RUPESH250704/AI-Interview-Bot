import React, { useState, useRef, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import StaggeredMenu from './StaggeredMenu';
import Squares from './Squares';
import './ChatInterview.css';

const ChatInterview = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { interviewData } = location.state || {};
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
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

    // Enter fullscreen with error handling
    const enterFullscreen = async () => {
      try {
        await document.documentElement.requestFullscreen();
      } catch (error) {
        console.log('Fullscreen not supported or denied');
      }
    };
    
    enterFullscreen();

    // Initial greeting message
    const greeting = `Hello! I'm your AI interviewer for the ${interviewData.type} interview at ${interviewData.company} for the ${interviewData.role} position. I've reviewed your resume. Let's begin! Please introduce yourself.`;
    
    setMessages([{
      id: 1,
      text: greeting,
      sender: 'ai',
      timestamp: new Date()
    }]);

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

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = {
      id: messages.length + 1,
      text: inputMessage,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    // Simulate AI response (replace with actual LLM integration)
    setTimeout(() => {
      const aiResponse = {
        id: messages.length + 2,
        text: generateAIResponse(inputMessage, interviewData),
        sender: 'ai',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, aiResponse]);
      setIsLoading(false);
    }, 1500);
  };

  const generateAIResponse = (userInput, data) => {
    // Placeholder responses - replace with actual LLM integration
    const responses = [
      "That's interesting. Can you tell me more about your experience with that technology?",
      "Great! Now, let me ask you about a challenging project you've worked on.",
      "How would you handle a situation where you disagree with your team lead?",
      "Can you walk me through your problem-solving approach?",
      "What motivates you in your professional career?",
      "How do you stay updated with the latest technologies in your field?"
    ];
    
    return responses[Math.floor(Math.random() * responses.length)];
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const endInterview = () => {
    try {
      if (document.fullscreenElement) {
        document.exitFullscreen();
      }
    } catch (error) {
      console.log('Exit fullscreen failed');
    }
    alert('Your interview has ended!');
    navigate('/analysis', { 
      state: { 
        interviewData,
        messages: messages.filter(msg => msg.sender === 'user')
      }
    });
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
          <div className="chat-header">
            <h2>{interviewData.type} Interview - {interviewData.company}</h2>
            <p>Role: {interviewData.role}</p>
            <button onClick={endInterview} className="end-interview-btn">
              End Interview
            </button>
          </div>
          
          <div className="chat-messages">
            {messages.map((message) => (
              <div key={message.id} className={`message ${message.sender}`}>
                <div className="message-content">
                  <p>{message.text}</p>
                  <span className="timestamp">
                    {message.timestamp.toLocaleTimeString()}
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
            />
            <button 
              onClick={handleSendMessage} 
              disabled={!inputMessage.trim() || isLoading}
              className="send-btn"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </>
  );
};

export default ChatInterview;