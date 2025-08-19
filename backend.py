from flask import Flask, request, jsonify, session
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import json
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = 'your-secret-key'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# In-memory storage for demo purposes
users = {
    'admin@aica.com': {'password': 'admin123', 'role': 'admin', 'name': 'Admin'},
    'agent@aica.com': {'password': 'agent123', 'role': 'agent', 'name': 'Agent'},
    'customer@aica.com': {'password': 'customer123', 'role': 'customer', 'name': 'Customer'}
}

claims = []
claim_id_counter = 1

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if email in users and users[email]['password'] == password:
        session['user'] = {
            'email': email,
            'role': users[email]['role'],
            'name': users[email]['name']
        }
        return jsonify({'success': True, 'user': session['user']})
    
    return jsonify({'success': False, 'message': 'Invalid credentials'})

@app.route('/api/claims', methods=['GET', 'POST'])
def handle_claims():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if request.method == 'GET':
        return jsonify(claims)
    
    if request.method == 'POST':
        global claim_id_counter
        data = request.get_json()
        
        new_claim = {
            'id': f"CLM-{datetime.now().year}-{str(claim_id_counter).zfill(3)}",
            'type': data.get('type'),
            'customer': data.get('customer'),
            'amount': data.get('amount'),
            'date': datetime.now().isoformat(),
            'status': 'processing',
            'description': data.get('description'),
            'fraudScore': calculate_fraud_score(data),
            'progress': 10
        }
        
        claims.insert(0, new_claim)
        claim_id_counter += 1
        
        # Notify all clients about the new claim
        socketio.emit('new_claim', new_claim)
        
        return jsonify({'success': True, 'claim': new_claim})

@app.route('/api/claims/<claim_id>', methods=['PUT'])
def update_claim(claim_id):
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    
    for claim in claims:
        if claim['id'] == claim_id:
            if 'status' in data:
                claim['status'] = data['status']
            if 'progress' in data:
                claim['progress'] = data['progress']
            
            # Notify all clients about the update
            socketio.emit('claim_updated', claim)
            
            return jsonify({'success': True, 'claim': claim})
    
    return jsonify({'success': False, 'message': 'Claim not found'})

def calculate_fraud_score(claim_data):
    # Implement your fraud detection algorithm here
    # This is a simplified version
    score = 0
    
    # Amount-based risk
    amount = float(claim_data.get('amount', 0))
    if amount > 50000:
        score += 0.3
    elif amount > 20000:
        score += 0.2
    elif amount > 10000:
        score += 0.1
    
    # Add some randomness for demo
    score += np.random.random() * 0.3
    
    return min(score, 1)

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('connected', {'data': 'Connected to AICA backend'})

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)