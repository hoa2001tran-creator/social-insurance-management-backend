from flask import Blueprint, request, jsonify
from models.insurance import InsuranceRecord, InsuranceClaim
from models.employee import Employee
from app import db
from datetime import datetime

insurance_bp = Blueprint('insurance', __name__)

# ==================== Insurance Records ====================

@insurance_bp.route('/records', methods=['GET'])
def list_insurance_records():
    """Get list of insurance records"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    records = InsuranceRecord.query.paginate(page=page, per_page=per_page)
    
    return jsonify({
        'total': records.total,
        'pages': records.pages,
        'records': [r.to_dict() for r in records.items]
    }), 200

@insurance_bp.route('/records/<int:record_id>', methods=['GET'])
def get_insurance_record(record_id):
    """Get insurance record by ID"""
    record = InsuranceRecord.query.get(record_id)
    
    if not record:
        return jsonify({'error': 'Insurance record not found'}), 404
    
    return jsonify(record.to_dict()), 200

@insurance_bp.route('/records', methods=['POST'])
def create_insurance_record():
    """Create new insurance record for employee"""
    data = request.get_json()
    
    required_fields = ['employee_id', 'insurance_number', 'start_date']
    if not data or not all(k in data for k in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    employee = Employee.query.get(data['employee_id'])
    if not employee:
        return jsonify({'error': 'Employee not found'}), 404
    
    if InsuranceRecord.query.filter_by(insurance_number=data['insurance_number']).first():
        return jsonify({'error': 'Insurance number already exists'}), 409
    
    record = InsuranceRecord(
        employee_id=data['employee_id'],
        insurance_number=data['insurance_number'],
        health_insurance=data.get('health_insurance', 0),
        social_insurance=data.get('social_insurance', 0),
        unemployment_insurance=data.get('unemployment_insurance', 0),
        contribution_rate=data.get('contribution_rate', 0.085),
        employer_contribution_rate=data.get('employer_contribution_rate', 0.195),
        start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date(),
        status=data.get('status', 'active')
    )
    
    db.session.add(record)
    db.session.commit()
    
    return jsonify({
        'message': 'Insurance record created successfully',
        'record': record.to_dict()
    }), 201

@insurance_bp.route('/records/<int:record_id>', methods=['PUT'])
def update_insurance_record(record_id):
    """Update insurance record"""
    record = InsuranceRecord.query.get(record_id)
    
    if not record:
        return jsonify({'error': 'Insurance record not found'}), 404
    
    data = request.get_json()
    
    for field in ['health_insurance', 'social_insurance', 'unemployment_insurance', 'contribution_rate', 'status']:
        if field in data:
            setattr(record, field, data[field])
    
    if 'last_contribution_date' in data:
        record.last_contribution_date = datetime.strptime(data['last_contribution_date'], '%Y-%m-%d').date()
    
    db.session.commit()
    
    return jsonify({
        'message': 'Insurance record updated successfully',
        'record': record.to_dict()
    }), 200

# ==================== Insurance Claims ====================

@insurance_bp.route('/claims', methods=['GET'])
def list_insurance_claims():
    """Get list of insurance claims"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    claims = InsuranceClaim.query.paginate(page=page, per_page=per_page)
    
    return jsonify({
        'total': claims.total,
        'pages': claims.pages,
        'claims': [c.to_dict() for c in claims.items]
    }), 200

@insurance_bp.route('/claims/<int:claim_id>', methods=['GET'])
def get_insurance_claim(claim_id):
    """Get insurance claim by ID"""
    claim = InsuranceClaim.query.get(claim_id)
    
    if not claim:
        return jsonify({'error': 'Insurance claim not found'}), 404
    
    return jsonify(claim.to_dict()), 200

@insurance_bp.route('/claims', methods=['POST'])
def create_insurance_claim():
    """Create new insurance claim"""
    data = request.get_json()
    
    required_fields = ['insurance_id', 'claim_number', 'claim_type', 'amount', 'claim_date']
    if not data or not all(k in data for k in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    record = InsuranceRecord.query.get(data['insurance_id'])
    if not record:
        return jsonify({'error': 'Insurance record not found'}), 404
    
    if InsuranceClaim.query.filter_by(claim_number=data['claim_number']).first():
        return jsonify({'error': 'Claim number already exists'}), 409
    
    claim = InsuranceClaim(
        insurance_id=data['insurance_id'],
        claim_number=data['claim_number'],
        claim_type=data['claim_type'],
        description=data.get('description'),
        amount=data['amount'],
        claim_date=datetime.strptime(data['claim_date'], '%Y-%m-%d').date(),
        status=data.get('status', 'pending'),
        notes=data.get('notes')
    )
    
    db.session.add(claim)
    db.session.commit()
    
    return jsonify({
        'message': 'Insurance claim created successfully',
        'claim': claim.to_dict()
    }), 201

@insurance_bp.route('/claims/<int:claim_id>', methods=['PUT'])
def update_insurance_claim(claim_id):
    """Update insurance claim"""
    claim = InsuranceClaim.query.get(claim_id)
    
    if not claim:
        return jsonify({'error': 'Insurance claim not found'}), 404
    
    data = request.get_json()
    
    for field in ['claim_type', 'description', 'amount', 'status', 'notes']:
        if field in data:
            setattr(claim, field, data[field])
    
    if 'approval_date' in data:
        claim.approval_date = datetime.strptime(data['approval_date'], '%Y-%m-%d').date()
    
    if 'payment_date' in data:
        claim.payment_date = datetime.strptime(data['payment_date'], '%Y-%m-%d').date()
    
    db.session.commit()
    
    return jsonify({
        'message': 'Insurance claim updated successfully',
        'claim': claim.to_dict()
    }), 200

# ==================== Statistics ====================

@insurance_bp.route('/statistics/contributions', methods=['GET'])
def get_contribution_statistics():
    """Get contribution statistics"""
    total_records = InsuranceRecord.query.count()
    active_records = InsuranceRecord.query.filter_by(status='active').count()
    
    total_health = db.session.query(db.func.sum(InsuranceRecord.health_insurance)).scalar() or 0
    total_social = db.session.query(db.func.sum(InsuranceRecord.social_insurance)).scalar() or 0
    total_unemployment = db.session.query(db.func.sum(InsuranceRecord.unemployment_insurance)).scalar() or 0
    
    return jsonify({
        'total_records': total_records,
        'active_records': active_records,
        'total_health_insurance': total_health,
        'total_social_insurance': total_social,
        'total_unemployment_insurance': total_unemployment,
        'total_all': total_health + total_social + total_unemployment
    }), 200

@insurance_bp.route('/statistics/claims', methods=['GET'])
def get_claims_statistics():
    """Get claims statistics"""
    total_claims = InsuranceClaim.query.count()
    pending_claims = InsuranceClaim.query.filter_by(status='pending').count()
    approved_claims = InsuranceClaim.query.filter_by(status='approved').count()
    paid_claims = InsuranceClaim.query.filter_by(status='paid').count()
    
    total_amount = db.session.query(db.func.sum(InsuranceClaim.amount)).scalar() or 0
    
    return jsonify({
        'total_claims': total_claims,
        'pending_claims': pending_claims,
        'approved_claims': approved_claims,
        'paid_claims': paid_claims,
        'total_amount': total_amount
    }), 200
