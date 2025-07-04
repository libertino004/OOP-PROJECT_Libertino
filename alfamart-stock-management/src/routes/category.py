"""
Category routes for the Alfamart Stock Management System.
Implements full CRUD operations with proper error handling and validation.
"""

from flask import Blueprint, jsonify, request
from src.models.base import db
from src.models.category import Category

category_bp = Blueprint('category', __name__)


@category_bp.route('/categories', methods=['GET'])
def get_categories():
    """
    Get all categories with optional filtering.
    Supports search by name and active status filtering.
    """
    try:
        # Get query parameters
        search_name = request.args.get('search_name', '')
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        
        # Build query
        query = Category.query
        
        if search_name:
            categories = Category.search_by_name(search_name)
        else:
            categories = query.all()
        
        # Filter by active status if requested
        if active_only:
            categories = [cat for cat in categories if cat.is_active]
        
        return jsonify({
            'success': True,
            'data': [category.to_dict() for category in categories],
            'count': len(categories)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@category_bp.route('/categories', methods=['POST'])
def create_category():
    """
    Create a new category.
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
        description = data.get('description')
        
        if not name or not code:
            return jsonify({
                'success': False,
                'error': 'Name and code are required'
            }), 400
        
        # Check if category with same code already exists
        existing = Category.query.filter_by(_code=code.upper()).first()
        if existing:
            return jsonify({
                'success': False,
                'error': f'Category with code {code.upper()} already exists'
            }), 409
        
        # Create new category
        category = Category(name=name, code=code, description=description)
        
        # Validate category
        validation_errors = category.validate()
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Validation failed',
                'details': validation_errors
            }), 400
        
        # Save to database
        db.session.add(category)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': category.to_dict(),
            'message': 'Category created successfully'
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


@category_bp.route('/categories/<int:category_id>', methods=['GET'])
def get_category(category_id):
    """
    Get a specific category by ID.
    """
    try:
        category = Category.query.get_or_404(category_id)
        return jsonify({
            'success': True,
            'data': category.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404


@category_bp.route('/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    """
    Update an existing category.
    Supports partial updates with validation.
    """
    try:
        category = Category.query.get_or_404(category_id)
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Update fields if provided
        if 'name' in data:
            category.set_name(data['name'])
        
        if 'code' in data:
            # Check if new code conflicts with existing categories
            existing = Category.query.filter(
                Category._code == data['code'].upper(),
                Category.id != category_id
            ).first()
            if existing:
                return jsonify({
                    'success': False,
                    'error': f'Category with code {data["code"].upper()} already exists'
                }), 409
            category.set_code(data['code'])
        
        if 'description' in data:
            category.set_description(data['description'])
        
        if 'is_active' in data:
            if data['is_active']:
                category.activate()
            else:
                category.deactivate()
        
        # Validate updated category
        validation_errors = category.validate()
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
            'data': category.to_dict(),
            'message': 'Category updated successfully'
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


@category_bp.route('/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    """
    Delete a category.
    Checks for dependencies before deletion.
    """
    try:
        category = Category.query.get_or_404(category_id)
        
        # Check if category has products
        if category.products:
            return jsonify({
                'success': False,
                'error': f'Cannot delete category. It has {len(category.products)} associated products.'
            }), 409
        
        # Delete category
        db.session.delete(category)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Category deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@category_bp.route('/categories/<int:category_id>/products', methods=['GET'])
def get_category_products(category_id):
    """
    Get all products in a specific category.
    """
    try:
        category = Category.query.get_or_404(category_id)
        
        # Get query parameters
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        
        products = category.get_active_products() if active_only else category.products
        
        return jsonify({
            'success': True,
            'data': {
                'category': category.to_dict(),
                'products': [product.to_dict() for product in products],
                'product_count': len(products)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404


@category_bp.route('/categories/search', methods=['GET'])
def search_categories():
    """
    Search categories by name or code.
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
            categories = Category.search_by_name(search_term)
        elif search_type == 'code':
            categories = Category.search_by_code(search_term)
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid search type. Use "name" or "code"'
            }), 400
        
        return jsonify({
            'success': True,
            'data': [category.to_dict() for category in categories],
            'count': len(categories),
            'search_term': search_term,
            'search_type': search_type
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

