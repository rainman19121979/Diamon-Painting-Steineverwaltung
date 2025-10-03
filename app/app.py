"""
Diamond Painting Stone Inventory Management System
Flask Backend with SQLite Database
"""

from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import os
from datetime import datetime
from io import BytesIO

# Import database module
from database import (
    init_db, migrate_from_json, get_all_stones, get_stone,
    add_stone as db_add_stone, update_stone as db_update_stone,
    delete_stone as db_delete_stone, search_stones as db_search_stones,
    export_to_json, import_from_json
)
from dmc_colors_de import get_color_info, search_colors, get_all_colors

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Configuration
DATA_DIR = 'data'

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Initialize database on startup
init_db()

# Migrate from JSON if exists
migrated_count = migrate_from_json()
if migrated_count > 0:
    print(f"✓ Migrated {migrated_count} stones from JSON to SQLite")


@app.route('/')
def index():
    """Render the main application page"""
    return render_template('index.html')


@app.route('/api/stones', methods=['GET'])
def get_stones():
    """GET /api/stones - Retrieve all stones from inventory"""
    try:
        stones = get_all_stones()
        return jsonify({
            'success': True,
            'data': stones,
            'count': len(stones)
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stones', methods=['POST'])
def add_stone():
    """POST /api/stones - Add new stone to inventory"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400

        # Validate required fields
        if 'dmc_number' not in data or not data['dmc_number']:
            return jsonify({
                'success': False,
                'error': 'DMC number is required'
            }), 400

        # Check if quantity or pieces is provided
        if not data.get('quantity') and not data.get('pieces'):
            return jsonify({
                'success': False,
                'error': 'Either quantity or pieces is required'
            }), 400

        # Add stone to database
        stone_id = db_add_stone(data)
        new_stone = get_stone(stone_id)

        return jsonify({
            'success': True,
            'data': new_stone,
            'message': 'Stone added successfully'
        }), 201

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stones/<int:stone_id>', methods=['GET'])
def get_stone_by_id(stone_id: int):
    """GET /api/stones/<id> - Get single stone by ID"""
    try:
        stone = get_stone(stone_id)
        if not stone:
            return jsonify({
                'success': False,
                'error': f'Stone with ID {stone_id} not found'
            }), 404

        return jsonify({
            'success': True,
            'data': stone
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stones/<int:stone_id>', methods=['PUT'])
def update_stone(stone_id: int):
    """PUT /api/stones/<id> - Update existing stone"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400

        # Update stone
        success = db_update_stone(stone_id, data)
        if not success:
            return jsonify({
                'success': False,
                'error': f'Stone with ID {stone_id} not found'
            }), 404

        updated_stone = get_stone(stone_id)
        return jsonify({
            'success': True,
            'data': updated_stone,
            'message': 'Stone updated successfully'
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stones/<int:stone_id>', methods=['DELETE'])
def delete_stone(stone_id: int):
    """DELETE /api/stones/<id> - Delete stone from inventory"""
    try:
        success = db_delete_stone(stone_id)
        if not success:
            return jsonify({
                'success': False,
                'error': f'Stone with ID {stone_id} not found'
            }), 404

        return jsonify({
            'success': True,
            'message': 'Stone deleted successfully'
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stones/search', methods=['GET'])
def search_stones():
    """GET /api/stones/search?q=<query> - Search stones"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query is required'
            }), 400

        results = db_search_stones(query)
        return jsonify({
            'success': True,
            'data': results,
            'count': len(results),
            'query': query
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/backup/export', methods=['GET'])
def export_backup():
    """GET /api/backup/export - Export database as JSON"""
    try:
        json_data = export_to_json()
        filename = f"diamond_painting_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        return send_file(
            BytesIO(json_data.encode('utf-8')),
            mimetype='application/json',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/backup/import', methods=['POST'])
def import_backup():
    """POST /api/backup/import - Import database from JSON"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        if not file.filename.endswith('.json'):
            return jsonify({
                'success': False,
                'error': 'File must be a JSON file'
            }), 400

        # Read and import file
        json_data = file.read().decode('utf-8')
        count = import_from_json(json_data)

        return jsonify({
            'success': True,
            'message': f'Successfully imported {count} stones',
            'count': count
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/dmc/<dmc_number>', methods=['GET'])
def get_dmc_color(dmc_number):
    """GET /api/dmc/<dmc_number> - Get DMC color info"""
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
    """GET /api/dmc/search?q=<query> - Search DMC colors"""
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
    """GET /api/dmc/all - Get all DMC colors"""
    all_colors = get_all_colors()
    return jsonify({
        'success': True,
        'count': len(all_colors),
        'colors': all_colors
    }), 200


@app.route('/api/health', methods=['GET'])
def health_check():
    """GET /api/health - Health check endpoint"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'service': 'Diamond Painting Inventory API',
        'database': 'SQLite',
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
    port = int(os.environ.get('FLASK_PORT', 8080))
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'

    print(f"🚀 Starting Diamond Painting Organizer on port {port}")
    print(f"   Database: SQLite (data/stones.db)")
    print(f"   Access at: http://localhost:{port}")

    app.run(debug=debug, host='0.0.0.0', port=port)
