"""
Core STARK proof generation logic
"""
from app.core.proof_generator import generate_proof
from app.core.proof_verifier import verify_proof

__all__ = ['generate_proof', 'verify_proof']