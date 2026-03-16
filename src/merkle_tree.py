"""
Merkle Tree Implementation for Data Integrity Verification
File: merkle_tree.py
Purpose: Implements a binary Merkle hash tree for efficient data integrity verification
"""

import hashlib
from typing import List, Tuple, Optional


class MerkleNode:
    """Represents a single node in the Merkle Tree"""
    
    def __init__(self, hash_value: str, is_leaf: bool = False, left=None, right=None):
        """
        Initialize a Merkle Tree node
        
        Args:
            hash_value: The hash value of this node
            is_leaf: Whether this is a leaf node
            left: Left child node
            right: Right child node
        """
        self.hash = hash_value
        self.is_leaf = is_leaf
        self.left = left
        self.right = right


class MerkleTree:
    """
    Merkle Hash Tree Implementation
    
    A Merkle tree is a binary tree where:
    - Leaf nodes contain hashes of data blocks
    - Internal nodes contain hashes of concatenated child hashes
    - The root hash represents the integrity of all data blocks
    
    Properties:
    - Efficient verification: O(log n) to verify a single block
    - Tamper detection: Changes in any block change the root hash
    - Proof of retrievability: Can prove specific block integrity
    """
    
    def __init__(self):
        """Initialize an empty Merkle Tree"""
        self.tree = None
        self.leaf_nodes = []
        self.block_proofs = {}  # Store proof paths for each block
    
    @staticmethod
    def hash_data(data: bytes) -> str:
        """
        SHA-256 hash of data
        
        Args:
            data: Raw bytes to hash
            
        Returns:
            Hexadecimal hash string
        """
        return hashlib.sha256(data).hexdigest()
    
    @staticmethod
    def hash_pair(hash1: str, hash2: str) -> str:
        """
        Hash the concatenation of two hashes
        
        Args:
            hash1: First hash value
            hash2: Second hash value
            
        Returns:
            Hash of concatenated values
        """
        combined = hash1 + hash2
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def build_tree(self, data_blocks: List[bytes]) -> str:
        """
        Build a Merkle tree from data blocks
        
        Algorithm:
        1. Hash each data block to create leaf nodes
        2. Iteratively combine adjacent hashes moving up the tree
        3. Return the root hash
        
        Args:
            data_blocks: List of data blocks (bytes)
            
        Returns:
            Root hash of the Merkle tree
        """
        if not data_blocks:
            raise ValueError("Cannot build tree with empty data blocks")
        
        # Step 1: Create leaf nodes with hashes of data blocks
        self.leaf_nodes = [
            MerkleNode(self.hash_data(block), is_leaf=True) 
            for block in data_blocks
        ]
        
        # If odd number of blocks, duplicate the last one
        if len(self.leaf_nodes) % 2 != 0:
            last_block = self.leaf_nodes[-1]
            self.leaf_nodes.append(
                MerkleNode(last_block.hash, is_leaf=True)
            )
        
        # Step 2: Build tree bottom-up
        current_level = self.leaf_nodes[:]
        
        while len(current_level) > 1:
            next_level = []
            
            # Combine adjacent pairs
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1]
                
                # Create parent node with combined hash
                parent_hash = self.hash_pair(left.hash, right.hash)
                parent = MerkleNode(parent_hash, is_leaf=False, left=left, right=right)
                next_level.append(parent)
            
            current_level = next_level
        
        # Step 3: Store root
        self.tree = current_level[0]
        
        # Generate proof paths for each block
        self._generate_block_proofs()
        
        return self.tree.hash
    
    def _generate_block_proofs(self):
        """Generate proof paths for each block (path to root)"""
        for i, leaf in enumerate(self.leaf_nodes):
            proof = []
            self._collect_proof(self.tree, leaf, proof)
            self.block_proofs[i] = proof
    
    def _collect_proof(self, node: MerkleNode, target: MerkleNode, proof: List) -> bool:
        """
        Collect proof path from node to target leaf
        
        Args:
            node: Current node
            target: Target leaf node
            proof: List to store proof hashes
            
        Returns:
            True if target found in subtree
        """
        if node is None:
            return False
        
        if node == target:
            return True
        
        # Check left subtree
        if node.left:
            if self._collect_proof(node.left, target, proof):
                # Add sibling hash to proof
                if node.right:
                    proof.append(("right", node.right.hash))
                return True
        
        # Check right subtree
        if node.right:
            if self._collect_proof(node.right, target, proof):
                # Add sibling hash to proof
                if node.left:
                    proof.append(("left", node.left.hash))
                return True
        
        return False
    
    def get_block_proof(self, block_index: int) -> List[Tuple[str, str]]:
        """
        Get the proof path for a specific block
        
        Args:
            block_index: Index of the block
            
        Returns:
            List of (direction, hash) tuples
        """
        if block_index not in self.block_proofs:
            raise ValueError(f"Invalid block index: {block_index}")
        
        return self.block_proofs[block_index]
    
    def get_root_hash(self) -> str:
        """
        Get the root hash of the tree
        
        Returns:
            Root hash value
        """
        if self.tree is None:
            raise ValueError("Tree has not been built yet")
        
        return self.tree.hash
    
    def verify_block(self, block_index: int, block_data: bytes, root_hash: str) -> bool:
        """
        Verify the integrity of a specific block
        
        Algorithm:
        1. Hash the block
        2. Combine with sibling hashes along the proof path
        3. Compare result with root hash
        
        Args:
            block_index: Index of the block to verify
            block_data: The block data to verify
            root_hash: The stored root hash to verify against
            
        Returns:
            True if block is valid, False if tampered
        """
        block_hash = self.hash_data(block_data)
        proof = self.get_block_proof(block_index)
        
        # Start with the block hash
        current_hash = block_hash
        
        # Walk up the tree using proof
        for direction, sibling_hash in reversed(proof):
            if direction == "left":
                current_hash = self.hash_pair(sibling_hash, current_hash)
            else:  # direction == "right"
                current_hash = self.hash_pair(current_hash, sibling_hash)
        
        # Compare with root hash
        return current_hash == root_hash
    
    def get_tree_depth(self) -> int:
        """Get the depth of the tree"""
        if self.tree is None:
            return 0
        
        return self._calculate_depth(self.tree)
    
    def _calculate_depth(self, node: MerkleNode) -> int:
        """Calculate depth of a subtree"""
        if node is None:
            return 0
        
        left_depth = self._calculate_depth(node.left)
        right_depth = self._calculate_depth(node.right)
        
        return 1 + max(left_depth, right_depth)
    
    def print_tree_structure(self) -> str:
        """
        Get a string representation of the tree structure
        
        Returns:
            Formatted tree structure
        """
        if self.tree is None:
            return "Tree is empty"
        
        result = []
        self._print_node(self.tree, 0, result)
        return "\n".join(result)
    
    def _print_node(self, node: MerkleNode, level: int, result: List):
        """Recursively print tree structure"""
        if node is None:
            return
        
        indent = "  " * level
        node_type = "LEAF" if node.is_leaf else "NODE"
        node_hash = node.hash[:16] + "..."  # Show first 16 chars
        result.append(f"{indent}[{node_type}] {node_hash}")
        
        if node.left:
            self._print_node(node.left, level + 1, result)
        if node.right:
            self._print_node(node.right, level + 1, result)
