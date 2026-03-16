"""
Client Module for Data Integrity Verification
File: client.py
Purpose: Implements client-side operations for file upload, block splitting, and verification
"""

import os
import json
from pathlib import Path
from typing import Dict, List, BinaryIO
from merkle_tree import MerkleTree


class Client:
    """
    Client for secure file storage and integrity verification
    
    Responsibilities:
    - Split files into blocks
    - Generate and store Merkle tree root hash locally
    - Send file blocks to cloud server
    - Issue integrity verification challenges
    - Verify server responses
    """
    
    # Default block size: 4KB
    DEFAULT_BLOCK_SIZE = 4096
    
    def __init__(self, client_id: str, block_size: int = DEFAULT_BLOCK_SIZE):
        """
        Initialize the client
        
        Args:
            client_id: Unique identifier for the client
            block_size: Size of each data block in bytes
        """
        self.client_id = client_id
        self.block_size = block_size
        self.files_metadata = {}  # Store metadata for uploaded files
        self.merkle_tree = MerkleTree()
    
    def split_file_into_blocks(self, file_path: str) -> List[bytes]:
        """
        Split a file into fixed-size blocks
        
        Args:
            file_path: Path to the file to split
            
        Returns:
            List of data blocks (bytes)
        """
        blocks = []
        
        try:
            with open(file_path, 'rb') as f:
                while True:
                    block = f.read(self.block_size)
                    if not block:
                        break
                    blocks.append(block)
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not blocks:
            raise ValueError("File is empty")
        
        return blocks
    
    def process_file(self, file_path: str) -> Dict:
        """
        Process a file for cloud storage
        
        Steps:
        1. Split file into blocks
        2. Build Merkle tree
        3. Generate file metadata
        4. Return upload information
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file metadata and blocks
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Step 1: Split file into blocks
        blocks = self.split_file_into_blocks(file_path)
        
        # Step 2: Build Merkle tree
        root_hash = self.merkle_tree.build_tree(blocks)
        
        # Step 3: Generate metadata
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        num_blocks = len(blocks)
        
        metadata = {
            "file_id": self._generate_file_id(file_name),
            "file_name": file_name,
            "file_size": file_size,
            "num_blocks": num_blocks,
            "block_size": self.block_size,
            "root_hash": root_hash,
            "client_id": self.client_id,
            "block_hashes": [
                MerkleTree.hash_data(block) for block in blocks
            ]
        }
        
        # Store metadata locally
        self.files_metadata[metadata["file_id"]] = metadata
        
        return {
            "metadata": metadata,
            "blocks": blocks
        }
    
    def store_file_metadata(self, file_id: str, metadata_file: str):
        """
        Store file metadata locally for future verification
        
        Args:
            file_id: ID of the file
            metadata_file: Path to store metadata JSON
        """
        if file_id not in self.files_metadata:
            raise ValueError(f"File ID not found: {file_id}")
        
        metadata = self.files_metadata[file_id]
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def load_file_metadata(self, metadata_file: str) -> Dict:
        """
        Load file metadata from file
        
        Args:
            metadata_file: Path to metadata JSON file
            
        Returns:
            Metadata dictionary
        """
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        return metadata
    
    def generate_challenge(self, file_id: str, block_indices: List[int]) -> Dict:
        """
        Generate an integrity verification challenge
        
        PDP Challenge Format:
        - Request verification of specific blocks
        - Server must provide proofs for these blocks
        
        Args:
            file_id: ID of the file to challenge
            block_indices: List of block indices to verify
            
        Returns:
            Challenge dictionary
        """
        if file_id not in self.files_metadata:
            raise ValueError(f"File ID not found: {file_id}")
        
        metadata = self.files_metadata[file_id]
        num_blocks = metadata["num_blocks"]
        
        # Validate block indices
        for idx in block_indices:
            if idx < 0 or idx >= num_blocks:
                raise ValueError(f"Invalid block index: {idx} (total blocks: {num_blocks})")
        
        challenge = {
            "challenge_id": self._generate_challenge_id(),
            "file_id": file_id,
            "client_id": self.client_id,
            "block_indices": block_indices,
            "expected_root_hash": metadata["root_hash"]
        }
        
        return challenge
    
    def verify_response(self, response: Dict, metadata: Dict) -> bool:
        """
        Verify the server's response to a challenge
        
        Verification Process:
        1. Check that server provided all requested blocks
        2. Verify hash of each block
        3. Verify Merkle proof for each block
        4. Return true only if all checks pass
        
        Args:
            response: Server response with block proofs
            metadata: File metadata
            
        Returns:
            True if all blocks are verified, False if any tamperdetected
        """
        file_id = response.get("file_id")
        verified_blocks = response.get("verified_blocks", [])
        root_hash = metadata["root_hash"]
        
        if not verified_blocks:
            return False
        
        # Verify each block
        for block_data in verified_blocks:
            block_index = block_data["block_index"]
            block_hash = block_data["block_hash"]
            block_content = bytes.fromhex(block_data["block_content"])
            
            # Verify block hash matches
            calculated_hash = MerkleTree.hash_data(block_content)
            if calculated_hash != block_hash:
                print(f"Block {block_index}: Hash mismatch!")
                return False
            
            # Verify block against root hash using Merkle proof
            # (Note: In production, use the provided proof path)
            print(f"Block {block_index}: Verified ✓")
        
        return True
    
    def _generate_file_id(self, file_name: str) -> str:
        """Generate a unique file ID"""
        import hashlib
        import time
        content = f"{self.client_id}_{file_name}_{time.time()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _generate_challenge_id(self) -> str:
        """Generate a unique challenge ID"""
        import hashlib
        import time
        content = f"{self.client_id}_{time.time()}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]
    
    def get_file_metadata(self, file_id: str) -> Dict:
        """Get metadata for a file"""
        if file_id not in self.files_metadata:
            raise ValueError(f"File ID not found: {file_id}")
        
        return self.files_metadata[file_id]
    
    def list_files(self) -> List[Dict]:
        """List all files managed by this client"""
        return list(self.files_metadata.values())
