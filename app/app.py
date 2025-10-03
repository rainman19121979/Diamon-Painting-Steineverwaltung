"""
Diamond Painting Stone Inventory Management System
Flask Backend with JSON Database
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from dmc_colors_de import get_color_name, get_hex_code, get_color_info, search_colors, get_all_colors

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Configuration
DATABASE_FILE = 'data/stones.json'
DATA_DIR = 'data'

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)


class DatabaseError(Exception):
    """Custom exception for database operations"""
    pass


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


def load_database() -> List[Dict]:
    """
    Load stones data from JSON database file.

    Returns:
        List[Dict]: List of stone dictionaries

    Raises:
        DatabaseError: If file cannot be read or parsed
    """
    try:
        if not os.path.exists(DATABASE_FILE):
            # Initialize with empty database
            save_database([])
            return []

        with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except json.JSONDecodeError as e:
        raise DatabaseError(f"Invalid JSON format in database: {str(e)}")
    except Exception as e:
        raise DatabaseError(f"Error reading database: {str(e)}")


def save_database(stones: List[Dict]) -> None:
    """
    Save stones data to JSON database file.

    Args:
        stones: List of stone dictionaries to save

    Raises:
        DatabaseError: If file cannot be written
    """
    try:
        with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
            json.dump(stones, f, indent=2, ensure_ascii=False)
    except Exception as e:
        raise DatabaseError(f"Error writing to database: {str(e)}")


def validate_stone_data(data: Dict) -> None:
    """
    Validate stone data before adding to database.

    Args:
        data: Stone data dictionary

    Raises:
        ValidationError: If validation fails
    """
    # Required fields
    if 'dmc_number' not in data or not data['dmc_number']:
        raise ValidationError("DMC number is required")

    # Validate DMC number format (should be numeric string)
    dmc = str(data['dmc_number']).strip()
    if not dmc.isdigit():
        raise ValidationError("DMC number must be numeric")

    # Either quantity ("viele"/"wenige") OR pieces (integer) must be provided
    quantity = str(data.get('quantity', '')).strip() if data.get('quantity') else ''
    pieces = data.get('pieces') if data.get('pieces') else ''

    if not quantity and not pieces:
        raise ValidationError("Either quantity (viele/wenige) or pieces count is required")

    # Validate quantity if provided (should be "viele" or "wenige")
    if quantity:
        if quantity not in ['viele', 'wenige']:
            raise ValidationError("Quantity must be 'viele' or 'wenige'")

    # Validate pieces if provided
    if pieces:
        try:
            pieces_int = int(pieces)
            if pieces_int < 1:
                raise ValidationError("Pieces must be at least 1")
        except (ValueError, TypeError):
            raise ValidationError("Pieces must be a valid number")


def generate_id(stones: List[Dict]) -> int:
    """
    Generate next available ID for new stone.

    Args:
        stones: Current list of stones

    Returns:
        int: Next available ID
    """
    if not stones:
        return 1
    return max(stone.get('id', 0) for stone in stones) + 1


@app.route('/')
def index():
    """Render the main application page"""
    return render_template('index.html')


@app.route('/api/stones', methods=['GET'])
def get_stones():
    """
    GET /api/stones - Retrieve all stones from inventory

    Returns:
        JSON response with list of stones or error message
    """
    try:
        stones = load_database()
        return jsonify({
            'success': True,
            'data': stones,
            'count': len(stones)
        }), 200
    except DatabaseError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stones', methods=['POST'])
def add_stone():
    """
    POST /api/stones - Add new stone to inventory

    Request Body:
        {
            "dmc_number": "310",
            "color_name": "Black",
            "quantity": 5000,
            "notes": "Optional notes"
        }

    Returns:
        JSON response with created stone or error message
    """
    try:
        # Parse request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400

        # Validate stone data
        validate_stone_data(data)

        # Load existing stones
        stones = load_database()

        # Check for duplicate DMC number
        dmc_number = str(data['dmc_number']).strip()
        if any(str(stone.get('dmc_number')) == dmc_number for stone in stones):
            return jsonify({
                'success': False,
                'error': f'Stone with DMC number {dmc_number} already exists'
            }), 409

        # Create new stone entry
        quantity = str(data.get('quantity', '')).strip() if data.get('quantity') else ''
        pieces = data.get('pieces') if data.get('pieces') else ''

        new_stone = {
            'id': generate_id(stones),
            'dmc_number': dmc_number,
            'color_name': str(data.get('color_name', '')).strip(),
            'quantity': quantity,  # "viele", "wenige", or empty string
            'pieces': int(pieces) if pieces else None,  # integer or None
            'location': str(data.get('location', '')).strip(),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        # Add to database
        stones.append(new_stone)
        save_database(stones)

        return jsonify({
            'success': True,
            'data': new_stone,
            'message': 'Stone added successfully'
        }), 201

    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except DatabaseError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }), 500


@app.route('/api/stones/<int:stone_id>', methods=['DELETE'])
def delete_stone(stone_id: int):
    """
    DELETE /api/stones/<id> - Delete stone from inventory

    Args:
        stone_id: ID of stone to delete

    Returns:
        JSON response with success message or error
    """
    try:
        # Load stones
        stones = load_database()

        # Find stone by ID
        stone_index = None
        for idx, stone in enumerate(stones):
            if stone.get('id') == stone_id:
                stone_index = idx
                break

        if stone_index is None:
            return jsonify({
                'success': False,
                'error': f'Stone with ID {stone_id} not found'
            }), 404

        # Remove stone
        deleted_stone = stones.pop(stone_index)
        save_database(stones)

        return jsonify({
            'success': True,
            'data': deleted_stone,
            'message': 'Stone deleted successfully'
        }), 200

    except DatabaseError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }), 500


@app.route('/api/stones/search', methods=['GET'])
def search_stones():
    """
    GET /api/stones/search?dmc=<number> - Search stones by DMC number

    Query Parameters:
        dmc: DMC number to search for (partial match supported)

    Returns:
        JSON response with matching stones or error message
    """
    try:
        # Get search parameter
        dmc_query = request.args.get('dmc', '').strip()

        if not dmc_query:
            return jsonify({
                'success': False,
                'error': 'DMC number parameter is required'
            }), 400

        # Load stones
        stones = load_database()

        # Search for matching stones (case-insensitive partial match)
        matching_stones = [
            stone for stone in stones
            if dmc_query.lower() in str(stone.get('dmc_number', '')).lower()
        ]

        return jsonify({
            'success': True,
            'data': matching_stones,
            'count': len(matching_stones),
            'query': dmc_query
        }), 200

    except DatabaseError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }), 500


@app.route('/api/stones/<int:stone_id>', methods=['PUT'])
def update_stone(stone_id: int):
    """
    PUT /api/stones/<id> - Update existing stone

    Args:
        stone_id: ID of stone to update

    Request Body:
        {
            "color_name": "Updated color",
            "quantity": 3000,
            "notes": "Updated notes"
        }

    Returns:
        JSON response with updated stone or error message
    """
    try:
        # Parse request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400

        # Load stones
        stones = load_database()

        # Find stone by ID
        stone_index = None
        for idx, stone in enumerate(stones):
            if stone.get('id') == stone_id:
                stone_index = idx
                break

        if stone_index is None:
            return jsonify({
                'success': False,
                'error': f'Stone with ID {stone_id} not found'
            }), 404

        # Update stone fields
        stone = stones[stone_index]

        if 'color_name' in data:
            stone['color_name'] = str(data.get('color_name', '')).strip()

        if 'quantity' in data:
            quantity = str(data.get('quantity', '')).strip() if data.get('quantity') else ''
            if quantity:
                if quantity not in ['viele', 'wenige']:
                    raise ValidationError("Quantity must be 'viele' or 'wenige'")
                stone['quantity'] = quantity
            else:
                stone['quantity'] = ''

        if 'pieces' in data:
            pieces = data.get('pieces') if data.get('pieces') else ''
            if pieces:
                try:
                    pieces_int = int(pieces)
                    if pieces_int < 1:
                        raise ValidationError("Pieces must be at least 1")
                    stone['pieces'] = pieces_int
                except (ValueError, TypeError):
                    raise ValidationError("Pieces must be a valid number")
            else:
                stone['pieces'] = None

        if 'location' in data:
            stone['location'] = str(data.get('location', '')).strip()

        stone['updated_at'] = datetime.now().isoformat()

        # Save updated database
        save_database(stones)

        return jsonify({
            'success': True,
            'data': stone,
            'message': 'Stone updated successfully'
        }), 200

    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except DatabaseError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }), 500


@app.route('/api/dmc/<dmc_number>', methods=['GET'])
def get_dmc_color(dmc_number):
    """
    GET /api/dmc/<dmc_number> - Get color name and hex code for DMC number

    Args:
        dmc_number: DMC stone number

    Returns:
        JSON response with color name and hex code
    """
    color_name, hex_code = get_color_info(dmc_number)

    if color_name:
        return jsonify({
            'success': True,
            'dmc_number': dmc_number,
            'color_name': color_name,
            'hex_code': hex_code
        }), 200
    else:
        return jsonify({
            'success': False,
            'dmc_number': dmc_number,
            'color_name': '',
            'hex_code': '',
            'message': 'DMC Nummer nicht in Datenbank gefunden'
        }), 200


@app.route('/api/dmc/search', methods=['GET'])
def search_dmc_colors():
    """
    GET /api/dmc/search?q=<query> - Search DMC colors

    Query Parameters:
        q: Search query (DMC number or color name)

    Returns:
        JSON response with matching colors
    """
    query = request.args.get('q', '')

    if not query:
        return jsonify({
            'success': False,
            'error': 'Search query required'
        }), 400

    results = search_colors(query)

    return jsonify({
        'success': True,
        'query': query,
        'count': len(results),
        'results': results
    }), 200


@app.route('/api/dmc/all', methods=['GET'])
def get_all_dmc_colors():
    """
    GET /api/dmc/all - Get all DMC colors

    Returns:
        JSON response with all DMC colors
    """
    all_colors = get_all_colors()

    return jsonify({
        'success': True,
        'count': len(all_colors),
        'colors': all_colors
    }), 200


@app.route('/api/health', methods=['GET'])
def health_check():
    """
    GET /api/health - Health check endpoint

    Returns:
        JSON response with service status
    """
    return jsonify({
        'success': True,
        'status': 'healthy',
        'service': 'Diamond Painting Inventory API',
        'timestamp': datetime.now().isoformat()
    }), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return jsonify({
        'success': False,
        'error': 'Method not allowed'
    }), 405


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


if __name__ == '__main__':
    # Run the Flask development server
    app.run(debug=True, host='0.0.0.0', port=5000)
