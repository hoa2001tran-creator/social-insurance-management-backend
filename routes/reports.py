from flask import Blueprint, request, jsonify
from models.employee import Employee
from models.insurance import InsuranceRecord, InsuranceClaim
from sqlalchemy import func
from datetime import datetime

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/summary', methods=['GET'])
def get_summary_report():
    """Get summary report"""
    total_employees = Employee.query.count()
    active_employees = Employee.query.filter_by(status='active').count()
    
    total_insurance_records = InsuranceRecord.query.count()
    active_insurance = InsuranceRecord.query.filter_by(status='active').count()
    
    total_claims = InsuranceClaim.query.count()
    pending_claims = InsuranceClaim.query.filter_by(status='pending').count()
    
    return jsonify({
        'employees': {
            'total': total_employees,
            'active': active_employees
        },
        'insurance': {
            'total_records': total_insurance_records,
            'active': active_insurance
        },
        'claims': {
            'total': total_claims,
            'pending': pending_claims
        }
    }), 200

@reports_bp.route('/contributions/by-department', methods=['GET'])
def get_contributions_by_department():
    """Get contributions grouped by department"""
    result = db.session.query(
        Employee.department,
        func.count(Employee.id).label('employee_count'),
        func.sum(InsuranceRecord.health_insurance).label('total_health'),
        func.sum(InsuranceRecord.social_insurance).label('total_social'),
        func.sum(InsuranceRecord.unemployment_insurance).label('total_unemployment')
    ).join(InsuranceRecord).group_by(Employee.department).all()
    
    data = [{
        'department': r[0],
        'employee_count': r[1],
        'total_health': r[2] or 0,
        'total_social': r[3] or 0,
        'total_unemployment': r[4] or 0,
        'total': (r[2] or 0) + (r[3] or 0) + (r[4] or 0)
    } for r in result]
    
    return jsonify({'data': data}), 200

@reports_bp.route('/claims/by-type', methods=['GET'])
def get_claims_by_type():
    """Get claims grouped by type"""
    result = db.session.query(
        InsuranceClaim.claim_type,
        func.count(InsuranceClaim.id).label('count'),
        func.sum(InsuranceClaim.amount).label('total_amount')
    ).group_by(InsuranceClaim.claim_type).all()
    
    data = [{
        'claim_type': r[0],
        'count': r[1],
        'total_amount': r[2] or 0
    } for r in result]
    
    return jsonify({'data': data}), 200

@reports_bp.route('/claims/by-status', methods=['GET'])
def get_claims_by_status():
    """Get claims grouped by status"""
    result = db.session.query(
        InsuranceClaim.status,
        func.count(InsuranceClaim.id).label('count'),
        func.sum(InsuranceClaim.amount).label('total_amount')
    ).group_by(InsuranceClaim.status).all()
    
    data = [{
        'status': r[0],
        'count': r[1],
        'total_amount': r[2] or 0
    } for r in result]
    
    return jsonify({'data': data}), 200

@reports_bp.route('/export/csv', methods=['GET'])
def export_csv():
    """Export employee and insurance data to CSV"""
    import csv
    from io import StringIO
    
    # Create CSV content
    output = StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow([
        'Employee Code', 'Full Name', 'Department', 'Insurance Number', 
        'Health Insurance', 'Social Insurance', 'Unemployment Insurance', 'Status'
    ])
    
    # Data
    employees = Employee.query.all()
    for emp in employees:
        insurance = InsuranceRecord.query.filter_by(employee_id=emp.id).first()
        if insurance:
            writer.writerow([
                emp.employee_code,
                emp.full_name,
                emp.department,
                insurance.insurance_number,
                insurance.health_insurance,
                insurance.social_insurance,
                insurance.unemployment_insurance,
                insurance.status
            ])
    
    return {
        'message': 'Export successful',
        'data': output.getvalue()
    }, 200
