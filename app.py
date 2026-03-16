"""
Flask Web Application for Cloud Data Integrity Verification
File: app.py
Purpose: Web interface for the data integrity verification system
"""

import os
import json
import sys
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from merkle_tree import MerkleTree
from client import Client
from cloud_server import CloudStorageServer
from integrity_verifier import IntegrityVerifier


# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'dat', 'bin', 'log'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Global instances
client = Client(client_id="client_001", block_size=4096)
cloud_server = CloudStorageServer(server_name="Cloud Storage Server")
verifier = IntegrityVerifier()
current_file_id = None
current_metadata = None


def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')


@app.route('/concepts')
def concepts():
    """Concepts explanation page"""
    return render_template('concepts.html')


@app.route('/architecture')
def architecture():
    """System architecture page"""
    return render_template('architecture.html')


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """
    Handle file upload
    
    Process:
    1. Receive file from client
    2. Split into blocks
    3. Build Merkle tree
    4. Store on cloud server
    5. Return file ID and metadata
    """
    global current_file_id, current_metadata
    
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                "error": "File type not allowed. Allowed: " + ', '.join(ALLOWED_EXTENSIONS)
            }), 400
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_path)
        
        # Process file
        file_data = client.process_file(temp_path)
        metadata = file_data['metadata']
        blocks = file_data['blocks']
        
        file_id = metadata['file_id']
        current_file_id = file_id
        current_metadata = metadata
        
        # Store on cloud server
        cloud_server.store_file(file_id, metadata, blocks)
        
        # Prepare response
        response = {
            "success": True,
            "file_id": file_id,
            "file_name": metadata['file_name'],
            "file_size": metadata['file_size'],
            "num_blocks": metadata['num_blocks'],
            "block_size": metadata['block_size'],
            "root_hash": metadata['root_hash'],
            "message": f"File uploaded successfully! File ID: {file_id}"
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/challenge', methods=['POST'])
def generate_challenge():
    """
    Generate an integrity verification challenge
    
    Request body:
    {
        "file_id": "...",
        "block_count": 5
    }
    """
    try:
        data = request.json
        file_id = data.get('file_id')
        block_count = int(data.get('block_count', 5))
        
        if not file_id:
            return jsonify({"error": "File ID required"}), 400
        
        # Get file metadata
        metadata = client.get_file_metadata(file_id)
        num_blocks = metadata['num_blocks']
        
        # Select random blocks
        import random
        if block_count > num_blocks:
            block_count = num_blocks
        
        block_indices = random.sample(range(num_blocks), block_count)
        
        # Generate challenge
        challenge = client.generate_challenge(file_id, block_indices)
        
        return jsonify({
            "success": True,
            "challenge": challenge,
            "block_count": block_count
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/verify', methods=['POST'])
def verify_challenge():
    """
    Verify file integrity by responding to a challenge
    
    Steps:
    1. Get challenge from request
    2. Retrieve blocks from cloud server
    3. Verify block hashes
    4. Return verification result
    """
    try:
        data = request.json
        challenge = data.get('challenge')
        
        if not challenge:
            return jsonify({"error": "Challenge data required"}), 400
        
        file_id = challenge['file_id']
        
        # Get cloud server response
        server_response = cloud_server.respond_to_challenge(challenge)
        
        if server_response['status'] != 'SUCCESS':
            return jsonify({
                "success": False,
                "error": server_response.get('error', 'Unknown error'),
                "tampered": True
            })
        
        # Verify blocks
        verified_blocks = server_response['verified_blocks']
        metadata = current_metadata or client.get_file_metadata(file_id)
        root_hash = metadata['root_hash']
        
        all_verified = True
        tampered_blocks = []
        
        for block_data in verified_blocks:
            block_idx = block_data['block_index']
            expected_hash = metadata['block_hashes'][block_idx]
            calculated_hash = block_data['block_hash']
            
            if expected_hash != calculated_hash:
                all_verified = False
                tampered_blocks.append(block_idx)
        
        # Generate report
        verification_result = {
            "success": all_verified,
            "file_id": file_id,
            "total_challenged": len(verified_blocks),
            "verified_blocks": len(verified_blocks) - len(tampered_blocks),
            "tampered_blocks": tampered_blocks,
            "root_hash": root_hash,
            "integrity_status": "OK" if all_verified else "COMPROMISED",
            "message": "All blocks verified successfully!" if all_verified else f"Tampering detected in blocks: {tampered_blocks}"
        }
        
        return jsonify(verification_result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/tamper', methods=['POST'])
def simulate_tamper():
    """
    Simulate an attack by tampering with a block
    
    For demonstration purposes only
    """
    try:
        data = request.json
        file_id = data.get('file_id')
        block_index = int(data.get('block_index', 0))
        
        if not file_id:
            return jsonify({"error": "File ID required"}), 400
        
        # Mark block as tampered
        cloud_server.tamper_block(file_id, block_index)
        
        return jsonify({
            "success": True,
            "message": f"Block {block_index} has been tampered (simulated attack)",
            "file_id": file_id,
            "block_index": block_index
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/repair', methods=['POST'])
def repair_block():
    """
    Repair a tampered block
    """
    try:
        data = request.json
        file_id = data.get('file_id')
        block_index = int(data.get('block_index', 0))
        
        if not file_id:
            return jsonify({"error": "File ID required"}), 400
        
        # Repair block
        cloud_server.repair_block(file_id, block_index)
        
        return jsonify({
            "success": True,
            "message": f"Block {block_index} has been repaired",
            "file_id": file_id,
            "block_index": block_index
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/file-info', methods=['GET'])
def get_file_info():
    """Get information about stored files"""
    try:
        file_id = request.args.get('file_id')
        
        if file_id:
            # Get specific file info
            info = cloud_server.get_file_info(file_id)
        else:
            # Get all files
            files = cloud_server.list_files()
            return jsonify({
                "success": True,
                "files": files,
                "total_files": len(files)
            })
        
        return jsonify({
            "success": True,
            "file": info
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get storage statistics"""
    try:
        stats = cloud_server.get_storage_statistics()
        
        return jsonify({
            "success": True,
            "statistics": stats
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/audit', methods=['POST'])
def perform_audit():
    """
    Perform a comprehensive file audit
    """
    try:
        data = request.json
        file_id = data.get('file_id')
        
        if not file_id:
            return jsonify({"error": "File ID required"}), 400
        
        # Get file blocks from server
        file_blocks = cloud_server.stored_files.get(file_id)
        if not file_blocks:
            return jsonify({"error": "File not found"}), 404
        
        metadata = cloud_server.file_metadata[file_id]
        root_hash = metadata['root_hash']
        
        # Perform audit
        audit_report = verifier.audit_file(
            file_id=file_id,
            file_blocks=file_blocks,
            expected_root_hash=root_hash,
            challenge_count=5
        )
        
        return jsonify({
            "success": True,
            "audit_report": audit_report
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║  Cloud Data Integrity Verification System                      ║
    ║  Flask Web Application                                         ║
    ║                                                                ║
    ║  Server starting on http://127.0.0.1:5000                     ║
    ║  Open your browser and navigate to that address                ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    app.run(debug=True, host='127.0.0.1', port=5000)
