"""
Supplier routes for the Alfamart Stock Management System.
Implements full CRUD operations with proper error handling and validation.
"""

from flask import Blueprint, jsonify, request
from src.models.base import db
from src.models.supplier import Supplier, ContactInfo

supplier_bp = Blueprint('supplier', __name__)


@supplier_bp.route('/suppliers', methods=['GET'])
def get_suppliers():
    """
    Get all suppliers with optional filtering.
    Supports search by name and active status filtering.
    """
    try:
        # Get query parameters
        search_name = request.args.get('search_name', '')
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        
        # Build query
        if search_name:
            suppliers = Supplier.search_by_name(search_name)
        else:
            suppliers = Supplier.query.all()
        
        # Filter by active status if requested
        if active_only:
            suppliers = [supplier for supplier in suppliers if supplier.is_active]
        
        return jsonify({
            'success': True,
            'data': [supplier.to_dict() for supplier in suppliers],
            'count': len(suppliers)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@supplier_bp.route('/suppliers', methods=['POST'])
def create_supplier():
    """
    Create a new supplier.
    Validates input data and handles business rules.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Extract required fields
        name = data.get('name')
        code = data.get('code')
        contact_info_data = data.get('contact_info', {})
        credit_limit = data.get('credit_limit', 0)
        payment_terms = data.get('payment_terms', 30)
        
        if not name or not code:
            return jsonify({
                'success': False,
                'error': 'Name and code are required'
            }), 400
        
        # Check if supplier with same code already exists
        existing = Supplier.query.filter_by(_code=code.upper()).first()
        if existing:
            return jsonify({
                'success': False,
                'error': f'Supplier with code {code.upper()} already exists'
            }), 409
        
        # Create contact info object
        contact_info = None
        if contact_info_data:
            contact_info = ContactInfo(
                phone=contact_info_data.get('phone'),
                email=contact_info_data.get('email'),
                address=contact_info_data.get('address')
            )
        
        # Create new supplier
        supplier = Supplier(
            name=name,
            code=code,
            contact_info=contact_info,
            credit_limit=credit_limit,
            payment_terms=payment_terms
        )
        
        # Validate supplier
        validation_errors = supplier.validate()
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Validation failed',
                'details': validation_errors
            }), 400
        
        # Save to database
        db.session.add(supplier)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': supplier.to_dict(),
            'message': 'Supplier created successfully'
        }), 201
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@supplier_bp.route('/suppliers/<int:supplier_id>', methods=['GET'])
def get_supplier(supplier_id):
    """
    Get a specific supplier by ID.
    """
    try:
        supplier = Supplier.query.get_or_404(supplier_id)
        return jsonify({
            'success': True,
            'data': supplier.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404


@supplier_bp.route('/suppliers/<int:supplier_id>', methods=['PUT'])
def update_supplier(supplier_id):
    """
    Update an existing supplier.
    Supports partial updates with validation.
    """
    try:
        supplier = Supplier.query.get_or_404(supplier_id)
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Update fields if provided
        if 'name' in data:
            supplier.set_name(data['name'])
        
        if 'code' in data:
            # Check if new code conflicts with existing suppliers
            existing = Supplier.query.filter(
                Supplier._code == data['code'].upper(),
                Supplier.id != supplier_id
            ).first()
            if existing:
                return jsonify({
                    'success': False,
                    'error': f'Supplier with code {data["code"].upper()} already exists'
                }), 409
            supplier.set_code(data['code'])
        
        if 'contact_info' in data:
            contact_info_data = data['contact_info']
            contact_info = ContactInfo(
                phone=contact_info_data.get('phone'),
                email=contact_info_data.get('email'),
                address=contact_info_data.get('address')
            )
            supplier.set_contact_info(contact_info)
        
        if 'credit_limit' in data:
            supplier.set_credit_limit(data['credit_limit'])
        
        if 'payment_terms' in data:
            supplier.set_payment_terms(data['payment_terms'])
        
        if 'is_active' in data:
            if data['is_active']:
                supplier.activate()
            else:
                supplier.deactivate()
        
        # Validate updated supplier
        validation_errors = supplier.validate()
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Validation failed',
                'details': validation_errors
            }), 400
        
        # Save changes
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': supplier.to_dict(),
            'message': 'Supplier updated successfully'
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@supplier_bp.route('/suppliers/<int:supplier_id>', methods=['DELETE'])
def delete_supplier(supplier_id):
    """
    Delete a supplier.
    Checks for dependencies before deletion.
    """
    try:
        supplier = Supplier.query.get_or_404(supplier_id)
        
        # Check if supplier has products
        if supplier.products:
            return jsonify({
                'success': False,
                'error': f'Cannot delete supplier. It has {len(supplier.products)} associated products.'
            }), 409
        
        # Delete supplier
        db.session.delete(supplier)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Supplier deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@supplier_bp.route('/suppliers/<int:supplier_id>/products', methods=['GET'])
def get_supplier_products(supplier_id):
    """
    Get all products from a specific supplier.
    """
    try:
        supplier = Supplier.query.get_or_404(supplier_id)
        
        # Get query parameters
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        
        products = supplier.get_active_products() if active_only else supplier.products
        
        return jsonify({
            'success': True,
            'data': {
                'supplier': supplier.to_dict(),
                'products': [product.to_dict() for product in products],
                'product_count': len(products)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404


@supplier_bp.route('/suppliers/<int:supplier_id>/credit-check', methods=['POST'])
def check_supplier_credit(supplier_id):
    """
    Check if supplier has available credit for a given amount.
    """
    try:
        supplier = Supplier.query.get_or_404(supplier_id)
        data = request.get_json()
        
        if not data or 'amount' not in data:
            return jsonify({
                'success': False,
                'error': 'Amount is required'
            }), 400
        
        amount = data['amount']
        if amount <= 0:
            return jsonify({
                'success': False,
                'error': 'Amount must be positive'
            }), 400
        
        credit_available = supplier.is_credit_available(amount)
        outstanding = supplier.get_total_outstanding()
        
        return jsonify({
            'success': True,
            'data': {
                'supplier_id': supplier_id,
                'supplier_name': supplier.name,
                'credit_limit': supplier.credit_limit,
                'outstanding_amount': outstanding,
                'available_credit': supplier.credit_limit - outstanding,
                'requested_amount': amount,
                'credit_available': credit_available
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@supplier_bp.route('/suppliers/search', methods=['GET'])
def search_suppliers():
    """
    Search suppliers by name or code.
    """
    try:
        search_term = request.args.get('q', '')
        search_type = request.args.get('type', 'name')  # 'name' or 'code'
        
        if not search_term:
            return jsonify({
                'success': False,
                'error': 'Search term is required'
            }), 400
        
        if search_type == 'name':
            suppliers = Supplier.search_by_name(search_term)
        elif search_type == 'code':
            suppliers = Supplier.search_by_code(search_term)
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid search type. Use "name" or "code"'
            }), 400
        
        return jsonify({
            'success': True,
            'data': [supplier.to_dict() for supplier in suppliers],
            'count': len(suppliers),
            'search_term': search_term,
            'search_type': search_type
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

