import React from 'react';
import StaggeredMenu from './StaggeredMenu';
import Squares from './Squares';
import './App.css';

const Analysis = () => {
  const menuItems = [
    { label: 'Technical Interview', ariaLabel: 'Start mock interview', link: '/technical' },
    { label: 'HR interview', ariaLabel: 'HR interview', link: '/hr' },
    { label: 'Analysis', ariaLabel: 'View results', link: '/analysis' },
  ];

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
            <h1>Analysis</h1>
            <div style={{ textAlign: 'center', padding: '2rem' }}>
              <p>Your interview analysis will appear here.</p>
              <p>Complete an interview to view detailed results and feedback.</p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Analysis;