import React, { useRef, useEffect, useState } from 'react';

const FaceDetector = ({ onViolation }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [faceCount, setFaceCount] = useState(0);
  const [violation, setViolation] = useState(false);
  const [consecutiveCount, setConsecutiveCount] = useState(0);
  const [violationTriggered, setViolationTriggered] = useState(false);

  useEffect(() => {
    startCamera();
    const interval = setInterval(detectFaces, 100); // 10 FPS
    return () => {
      clearInterval(interval);
      // Stop camera when component unmounts
      if (videoRef.current && videoRef.current.srcObject) {
        const tracks = videoRef.current.srcObject.getTracks();
        tracks.forEach(track => track.stop());
      }
    };
  }, [violationTriggered]);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          width: 320, 
          height: 240,
          facingMode: 'user'
        } 
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
          videoRef.current.play();
        };
      }
    } catch (error) {
      console.error('Camera access denied:', error);
    }
  };

  const detectFaces = async () => {
    if (!videoRef.current || videoRef.current.readyState !== 4 || violationTriggered) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    // Clear canvas first
    ctx.clearRect(0, 0, 320, 240);
    
    // Draw video frame
    ctx.drawImage(videoRef.current, 0, 0, 320, 240);
    
    // Convert to base64 and send to Python API
    const imageData = canvas.toDataURL('image/jpeg', 0.8);
    
    try {
      const response = await fetch('http://localhost:5000/api/detect-faces', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: imageData })
      });
      
      const result = await response.json();
      setFaceCount(result.face_count);
      setConsecutiveCount(result.consecutive_count);
      setViolation(result.violation);
      
      // Trigger violation callback only once
      if (result.violation && onViolation && !violationTriggered) {
        setViolationTriggered(true);
        onViolation();
        return; // Stop further processing
      }
      
      // Draw face boxes
      if (result.faces) {
        ctx.strokeStyle = result.face_count > 1 ? 'red' : 'green';
        ctx.lineWidth = 2;
        result.faces.forEach(face => {
          ctx.strokeRect(face.x, face.y, face.width, face.height);
        });
      }
      
    } catch (error) {
      console.error('Detection failed:', error);
    }
  };

  return (
    <div className="face-detector">
      <video 
        ref={videoRef} 
        autoPlay 
        muted 
        playsInline
        style={{
          width: '320px',
          height: '240px',
          position: 'absolute',
          opacity: 0.1
        }} 
      />
      <canvas ref={canvasRef} width={320} height={240} className="face-canvas" />
      <div className="face-status">
        <span className={`face-count ${faceCount > 1 ? 'violation' : ''}`}>
          Faces: {faceCount}
        </span>
        <span className="consecutive-count">
          {consecutiveCount}/5
        </span>
        {violation && <span className="violation-text">VIOLATION DETECTED!</span>}
      </div>
    </div>
  );
};

export default FaceDetector;