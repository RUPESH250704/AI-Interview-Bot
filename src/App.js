import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import TechnicalInterview from './TechnicalInterview';
import HRInterview from './HRInterview';
import Analysis from './Analysis';
import ChatInterview from './ChatInterview';

const App = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Navigate to="/technical" replace />} />
        <Route path="/technical" element={<TechnicalInterview />} />
        <Route path="/hr" element={<HRInterview />} />
        <Route path="/chat" element={<ChatInterview />} />
        <Route path="/analysis" element={<Analysis />} />
      </Routes>
    </Router>
  );
};

export default App;