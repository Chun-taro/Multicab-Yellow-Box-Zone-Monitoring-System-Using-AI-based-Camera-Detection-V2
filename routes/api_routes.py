from flask import Blueprint, jsonify
from database.database import Database

api_bp = Blueprint('api', __name__)

@api_bp.route('/violations')
def get_violations():
    db = Database()
    violations = db.get_all_violations()
    db.close()
    return jsonify(violations)

@api_bp.route('/zone', methods=['POST'])
def save_zone():
    from flask import request
    from config.config import config
    
    data = request.json
    if not data or 'zone' not in data:
        return jsonify({'error': 'No zone data provided'}), 400
    
    zone_coords = data['zone']
    # Validate structure (list of 4 points)
    if not isinstance(zone_coords, list) or len(zone_coords) != 4:
         return jsonify({'error': 'Zone must be 4 points'}), 400

    if config.save_zone_config(zone_coords):
        return jsonify({'success': True, 'message': 'Zone updated'})
    else:
        return jsonify({'error': 'Failed to save zone'}), 500

@api_bp.route('/zone', methods=['GET'])
def get_zone():
    from config.config import config
    return jsonify(config.YELLOW_BOX_ZONE)
