from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import numpy as np
import base64

app = Flask(__name__)
CORS(app)

# Use OpenCV's built-in face detector as fallback
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
consecutive_multiple_faces = 0

@app.route('/api/detect-faces', methods=['POST'])
def detect_faces():
    global consecutive_multiple_faces
    try:
        # Get image from request
        data = request.json
        image_data = data['image'].split(',')[1]  # Remove data:image/jpeg;base64,
        
        # Decode base64 image
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        face_count = len(faces)
        
        # Check for violations
        if face_count > 1:
            consecutive_multiple_faces += 1
        else:
            consecutive_multiple_faces = 0
            
        violation = consecutive_multiple_faces >= 5
        
        # Format face coordinates for frontend
        face_list = []
        for (x, y, w, h) in faces:
            face_list.append({
                'x': int(x), 'y': int(y), 
                'width': int(w), 'height': int(h)
            })
        
        return jsonify({
            'face_count': face_count,
            'faces': face_list,
            'consecutive_count': consecutive_multiple_faces,
            'violation': violation,
            'reason': 'Multiple faces detected' if violation else 'OK'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)