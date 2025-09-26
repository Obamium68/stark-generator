"""
API routes for STARK proof generation
"""
from flask import Blueprint, request, jsonify, current_app
import json
from app.core.proof_generator import generate_proof

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/generate-proof', methods=['POST'])
def run_proof_generation():
    """
    Generate a STARK proof from input data
    
    Expected JSON payload:
    {
        "input": <input_data>,
        "queries": <number_of_queries>,
        "challenges": <challenges_data>
    }
    """
    try:
        # Validate request
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['input', 'queries', 'challenges']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # Extract and validate parameters
        input_data = data['input']
        queries = int(data['queries'])
        
        # Check queries limit
        max_queries = current_app.config.get('MAX_QUERIES', 100)
        if queries > max_queries:
            return jsonify({
                'error': f'Number of queries exceeds maximum allowed: {max_queries}'
            }), 400
        
        challenges = json.dumps(data['challenges'])
        
        # Generate proof
        proof_data = generate_proof(str(input_data), queries, challenges)
        
        return jsonify({
            'success': True,
            'proof': proof_data
        }), 200
        
    except ValueError as e:
        return jsonify({
            'error': f'Invalid input: {str(e)}'
        }), 400
    except Exception as e:
        current_app.logger.error(f'Error generating proof: {str(e)}')
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500


@api_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404


@api_bp.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return jsonify({'error': 'Method not allowed'}), 405


@api_bp.route('/verify-proof', methods=['POST'])
def run_proof_verification():
    """
    Verify a STARK proof
    
    Expected JSON payload:
    {
        "proof": <proof_data_object>
    }
    """
    try:
        # Validate request
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        
        # Validate required fields
        if 'proof' not in data:
            return jsonify({
                'error': 'Missing required field: proof'
            }), 400
        
        proof_data = data['proof']
        
        # Verify proof
        from app.core.proof_verifier import verify_proof
        is_valid, errors = verify_proof(proof_data)
        
        if is_valid:
            return jsonify({
                'valid': True,
                'message': 'Proof verified: accept claims',
                'errors': [],
                'verification_details': {
                    'total_queries': proof_data['fri_decommitments']['query_num'],
                    'total_layers': len(proof_data['fri_commitment']['folding_poly_coeffs']),
                    'domain_size': proof_data['dom_size']
                }
            }), 200
        else:
            return jsonify({
                'valid': False,
                'message': 'Proof not valid: reject claims',
                'errors': errors,
                'error_count': len(errors),
                'verification_details': {
                    'total_queries': proof_data['fri_decommitments']['query_num'],
                    'total_layers': len(proof_data['fri_commitment']['folding_poly_coeffs']),
                    'domain_size': proof_data['dom_size']
                }
            }), 200
        
    except KeyError as e:
        return jsonify({
            'error': f'Invalid proof format: missing field {str(e)}'
        }), 400
    except Exception as e:
        current_app.logger.error(f'Error verifying proof: {str(e)}')
        return jsonify({
            'valid': False,
            'error': 'Internal server error',
            'message': str(e)
        }), 500