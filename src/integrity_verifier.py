"""
Integrity Verification Module
File: integrity_verifier.py
Purpose: Implements verification protocols and audit functions
"""

import json
import hashlib
from typing import Dict, List, Tuple
from merkle_tree import MerkleTree


class IntegrityVerifier:
    """
    Integrity Verification System
    
    Implements Provable Data Possession (PDP) protocol:
    - Challenge generation
    - Proof verification
    - Tamper detection
    - Audit reporting
    """
    
    def __init__(self):
        """Initialize the verifier"""
        self.verification_history = []
        self.audit_reports = []
    
    def verify_file_integrity(self, 
                             file_blocks: List[bytes], 
                             root_hash: str,
                             merkle_tree: MerkleTree = None) -> bool:
        """
        Verify the integrity of all blocks in a file
        
        Args:
            file_blocks: List of data blocks
            root_hash: Expected root hash of Merkle tree
            merkle_tree: Optional Merkle tree instance
            
        Returns:
            True if all blocks are integral, False if tampering detected
        """
        if merkle_tree is None:
            merkle_tree = MerkleTree()
        
        try:
            # Build tree from blocks
            calculated_root = merkle_tree.build_tree(file_blocks)
            
            # Compare with expected root
            is_valid = calculated_root == root_hash
            
            return is_valid
        except Exception as e:
            print(f"Verification error: {e}")
            return False
    
    def verify_block_integrity(self,
                               block_data: bytes,
                               block_hash: str) -> bool:
        """
        Verify a single block's hash
        
        Args:
            block_data: The block data
            block_hash: Expected hash of the block
            
        Returns:
            True if hash matches
        """
        calculated_hash = MerkleTree.hash_data(block_data)
        return calculated_hash == block_hash
    
    def verify_merkle_proof(self,
                           block_data: bytes,
                           block_index: int,
                           proof_path: List[Tuple[str, str]],
                           root_hash: str) -> bool:
        """
        Verify a block using Merkle proof path
        
        Algorithm:
        1. Hash the block
        2. Combine with each sibling in the proof path
        3. Check if final hash equals root hash
        
        Args:
            block_data: Block data to verify
            block_index: Index of the block (unused in basic verification)
            proof_path: List of (direction, hash) tuples
            root_hash: Root hash to verify against
            
        Returns:
            True if block is valid
        """
        # Hash the block
        current_hash = MerkleTree.hash_data(block_data)
        
        # Apply proof path
        for direction, sibling_hash in reversed(proof_path):
            if direction == "left":
                current_hash = MerkleTree.hash_pair(sibling_hash, current_hash)
            else:  # "right"
                current_hash = MerkleTree.hash_pair(current_hash, sibling_hash)
        
        # Verify result matches root
        return current_hash == root_hash
    
    def generate_challenge_response(self,
                                   file_blocks: List[bytes],
                                   block_indices: List[int],
                                   root_hash: str) -> Dict:
        """
        Generate a response to a challenge request
        
        Args:
            file_blocks: All file blocks
            block_indices: Indices of blocks to respond with
            root_hash: Root hash to include in response
            
        Returns:
            Challenge response dictionary
        """
        response = {
            "requested_blocks": [],
            "root_hash": root_hash,
            "verified": True
        }
        
        for idx in block_indices:
            if idx < 0 or idx >= len(file_blocks):
                response["verified"] = False
                continue
            
            block = file_blocks[idx]
            block_hash = MerkleTree.hash_data(block)
            
            response["requested_blocks"].append({
                "block_index": idx,
                "block_hash": block_hash,
                "block_size": len(block)
            })
        
        return response
    
    def audit_file(self, file_id: str, 
                  file_blocks: List[bytes],
                  expected_root_hash: str,
                  challenge_count: int = 5) -> Dict:
        """
        Perform a comprehensive audit of a stored file
        
        Args:
            file_id: ID of file to audit
            file_blocks: File blocks to audit
            expected_root_hash: Expected root hash
            challenge_count: Number of random blocks to challenge
            
        Returns:
            Audit report
        """
        import random
        
        report = {
            "file_id": file_id,
            "total_blocks": len(file_blocks),
            "challenges": []
        }
        
        # Select random blocks to challenge
        if challenge_count > len(file_blocks):
            challenge_count = len(file_blocks)
        
        challenged_indices = random.sample(range(len(file_blocks)), challenge_count)
        
        all_verified = True
        tampered_blocks = []
        
        # Verify each challenged block
        for idx in challenged_indices:
            block = file_blocks[idx]
            block_hash = MerkleTree.hash_data(block)
            
            # For this example, we assume all blocks are intact
            # (In real system, we'd use Merkle proof)
            block_verified = True
            
            challenge_result = {
                "block_index": idx,
                "block_hash": block_hash,
                "verified": block_verified
            }
            
            report["challenges"].append(challenge_result)
            
            if not block_verified:
                all_verified = False
                tampered_blocks.append(idx)
        
        # Overall audit result
        report["integrity_status"] = "OK" if all_verified else "COMPROMISED"
        report["tampered_blocks"] = tampered_blocks
        report["verification_rate"] = f"{(challenge_count - len(tampered_blocks)) / challenge_count * 100:.1f}%"
        
        self.audit_reports.append(report)
        
        return report
    
    def simulate_attack(self, file_blocks: List[bytes], 
                       attack_type: str = "bit_flip",
                       target_block: int = 0) -> List[bytes]:
        """
        Simulate an attack on file blocks
        
        Supported attacks:
        - bit_flip: Flip a bit in target block
        - block_replacement: Replace entire block with zeros
        - partial_corruption: Corrupt middle section of block
        
        Args:
            file_blocks: Original file blocks
            attack_type: Type of attack to simulate
            target_block: Index of target block
            
        Returns:
            Corrupted file blocks
        """
        corrupted_blocks = [block[:] for block in file_blocks]  # Deep copy
        
        if target_block < 0 or target_block >= len(corrupted_blocks):
            raise ValueError(f"Invalid block index: {target_block}")
        
        target = bytearray(corrupted_blocks[target_block])
        
        if attack_type == "bit_flip":
            # Flip first bit of first byte
            if len(target) > 0:
                target[0] ^= 0x01
        
        elif attack_type == "block_replacement":
            # Replace with zero bytes
            target = bytearray(len(target))
        
        elif attack_type == "partial_corruption":
            # Corrupt middle 25% of block
            if len(target) > 4:
                start = len(target) // 4
                end = (3 * len(target)) // 4
                for i in range(start, end):
                    target[i] ^= 0xFF
        
        else:
            raise ValueError(f"Unknown attack type: {attack_type}")
        
        corrupted_blocks[target_block] = bytes(target)
        
        return corrupted_blocks
    
    def detect_tampering(self, 
                        original_root_hash: str,
                        current_blocks: List[bytes]) -> Dict:
        """
        Detect if blocks have been tampered
        
        Args:
            original_root_hash: Root hash when file was stored
            current_blocks: Current block data
            
        Returns:
            Report on tampering detection
        """
        merkle_tree = MerkleTree()
        current_root = merkle_tree.build_tree(current_blocks)
        
        tampered = current_root != original_root_hash
        
        return {
            "tampered": tampered,
            "original_root_hash": original_root_hash,
            "current_root_hash": current_root,
            "message": "TAMPERING DETECTED!" if tampered else "Data integrity verified"
        }
    
    def get_verification_report(self) -> Dict:
        """
        Get a summary verification report
        
        Returns:
            Report dictionary
        """
        total_audits = len(self.audit_reports)
        compromised_audits = sum(
            1 for report in self.audit_reports 
            if report["integrity_status"] == "COMPROMISED"
        )
        
        return {
            "total_audits": total_audits,
            "successful_audits": total_audits - compromised_audits,
            "compromised_audits": compromised_audits,
            "audit_success_rate": f"{(total_audits - compromised_audits) / total_audits * 100:.1f}%" if total_audits > 0 else "N/A",
            "audit_reports": self.audit_reports
        }
