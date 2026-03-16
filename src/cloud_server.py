"""
Cloud Storage Server Module
File: cloud_server.py
Purpose: Implements cloud storage server for storing and responding to integrity verification challenges
"""

import json
import hashlib
from typing import Dict, List
from datetime import datetime


class CloudStorageServer:
    """
    Cloud Storage Server
    
    Responsibilities:
    - Store file blocks received from clients
    - Store file metadata and Merkle tree information
    - Respond to integrity verification challenges
    - Optionally simulate attacks (tampering) for testing
    """
    
    def __init__(self, server_name: str = "DefaultCloudServer"):
        """
        Initialize the cloud storage server
        
        Args:
            server_name: Name of the server
        """
        self.server_name = server_name
        self.stored_files = {}  # file_id -> file_data
        self.file_metadata = {}  # file_id -> metadata
        self.tampered_blocks = set()  # For attack simulation
        self.operation_log = []  # Log of all operations
    
    def store_file(self, file_id: str, metadata: Dict, blocks: List[bytes]) -> bool:
        """
        Store a file on the cloud server
        
        Args:
            file_id: Unique identifier for the file
            metadata: File metadata
            blocks: List of data blocks
            
        Returns:
            True if storage successful
        """
        if file_id in self.stored_files:
            raise ValueError(f"File already exists: {file_id}")
        
        # Store blocks
        self.stored_files[file_id] = blocks
        
        # Store metadata
        metadata_copy = metadata.copy()
        metadata_copy["stored_at"] = datetime.now().isoformat()
        self.file_metadata[file_id] = metadata_copy
        
        # Log operation
        self._log_operation("STORE", file_id, f"Stored {len(blocks)} blocks")
        
        return True
    
    def retrieve_blocks(self, file_id: str, block_indices: List[int]) -> List[Dict]:
        """
        Retrieve specific blocks for verification
        
        Args:
            file_id: ID of the file
            block_indices: Indices of blocks to retrieve
            
        Returns:
            List of block data
        """
        if file_id not in self.stored_files:
            raise ValueError(f"File not found: {file_id}")
        
        blocks = self.stored_files[file_id]
        retrieved = []
        
        for idx in block_indices:
            if idx < 0 or idx >= len(blocks):
                raise ValueError(f"Invalid block index: {idx}")
            
            block_data = blocks[idx]
            block_hash = hashlib.sha256(block_data).hexdigest()
            
            # Check if this block has been tampered (for attack simulation)
            if (file_id, idx) in self.tampered_blocks:
                # Return tampered data
                tampered_data = bytearray(block_data)
                if len(tampered_data) > 0:
                    # Flip a bit in the first byte
                    tampered_data[0] ^= 0x01
                block_data = bytes(tampered_data)
                block_hash = hashlib.sha256(block_data).hexdigest()
            
            retrieved.append({
                "block_index": idx,
                "block_size": len(block_data),
                "block_hash": block_hash,
                "block_content": block_data.hex()
            })
        
        # Log operation
        self._log_operation("RETRIEVE", file_id, f"Retrieved {len(retrieved)} blocks")
        
        return retrieved
    
    def respond_to_challenge(self, challenge: Dict) -> Dict:
        """
        Respond to an integrity verification challenge
        
        Args:
            challenge: Challenge from client
            
        Returns:
            Response with requested block data
        """
        file_id = challenge["file_id"]
        block_indices = challenge["block_indices"]
        
        if file_id not in self.stored_files:
            return {
                "status": "ERROR",
                "error": f"File not found: {file_id}"
            }
        
        # Retrieve blocks
        try:
            verified_blocks = self.retrieve_blocks(file_id, block_indices)
        except ValueError as e:
            return {
                "status": "ERROR",
                "error": str(e)
            }
        
        # Prepare response
        response = {
            "status": "SUCCESS",
            "challenge_id": challenge.get("challenge_id"),
            "file_id": file_id,
            "verified_blocks": verified_blocks,
            "timestamp": datetime.now().isoformat()
        }
        
        return response
    
    def tamper_block(self, file_id: str, block_index: int):
        """
        Simulate an attack by marking a block as tampered
        
        Args:
            file_id: ID of the file
            block_index: Index of block to tamper
        """
        if file_id not in self.stored_files:
            raise ValueError(f"File not found: {file_id}")
        
        blocks = self.stored_files[file_id]
        if block_index < 0 or block_index >= len(blocks):
            raise ValueError(f"Invalid block index: {block_index}")
        
        self.tampered_blocks.add((file_id, block_index))
        self._log_operation("TAMPER", file_id, f"Block {block_index} marked as tampered")
    
    def repair_block(self, file_id: str, block_index: int):
        """
        Repair a previously tampered block
        
        Args:
            file_id: ID of the file
            block_index: Index of block to repair
        """
        self.tampered_blocks.discard((file_id, block_index))
        self._log_operation("REPAIR", file_id, f"Block {block_index} repaired")
    
    def get_file_info(self, file_id: str) -> Dict:
        """
        Get information about a stored file
        
        Args:
            file_id: ID of the file
            
        Returns:
            File information
        """
        if file_id not in self.file_metadata:
            raise ValueError(f"File not found: {file_id}")
        
        metadata = self.file_metadata[file_id].copy()
        blocks = self.stored_files[file_id]
        
        # Count tampered blocks
        tampered_count = sum(
            1 for (fid, idx) in self.tampered_blocks 
            if fid == file_id
        )
        
        metadata["blocks_stored"] = len(blocks)
        metadata["tampered_blocks"] = tampered_count
        metadata["integrity_status"] = "COMPROMISED" if tampered_count > 0 else "OK"
        
        return metadata
    
    def list_files(self) -> List[Dict]:
        """List all files stored on this server"""
        files = []
        for file_id in self.stored_files:
            files.append(self.get_file_info(file_id))
        return files
    
    def delete_file(self, file_id: str) -> bool:
        """
        Delete a file from storage
        
        Args:
            file_id: ID of the file to delete
            
        Returns:
            True if deletion successful
        """
        if file_id not in self.stored_files:
            raise ValueError(f"File not found: {file_id}")
        
        # Remove file data and metadata
        del self.stored_files[file_id]
        del self.file_metadata[file_id]
        
        # Remove any tampered block entries
        self.tampered_blocks = {
            (fid, idx) for (fid, idx) in self.tampered_blocks 
            if fid != file_id
        }
        
        self._log_operation("DELETE", file_id, "File deleted")
        
        return True
    
    def get_storage_statistics(self) -> Dict:
        """
        Get storage statistics
        
        Returns:
            Statistics dictionary
        """
        total_files = len(self.stored_files)
        total_blocks = sum(len(blocks) for blocks in self.stored_files.values())
        total_size = sum(
            sum(len(block) for block in blocks) 
            for blocks in self.stored_files.values()
        )
        
        # Convert to MB
        total_size_mb = total_size / (1024 * 1024)
        
        return {
            "total_files": total_files,
            "total_blocks": total_blocks,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size_mb, 2),
            "tampered_blocks": len(self.tampered_blocks)
        }
    
    def _log_operation(self, operation: str, file_id: str, details: str):
        """Log an operation"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "file_id": file_id,
            "details": details
        }
        self.operation_log.append(log_entry)
    
    def get_operation_log(self) -> List[Dict]:
        """Get the operation log"""
        return self.operation_log.copy()
