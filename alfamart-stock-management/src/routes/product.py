"""
Product routes for the Alfamart Stock Management System.
Implements full CRUD operations with proper error handling and validation.
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
from src.models.base import db
from src.models.product import Product
from src.models.category import Category
from src.models.supplier import Supplier

product_bp = Blueprint('product', __name__)


@product_bp.route('/products', methods=['GET'])
def get_products():
    """
    Get all products with optional filtering and pagination.
    Supports search by name, category, supplier, and stock status.
    """
    try:
        # Get query parameters
        search_name = request.args.get('search_name', '')
        category_id = request.args.get('category_id', type=int)
        supplier_id = request.args.get('supplier_id', type=int)
        stock_status = request.args.get('stock_status', '')
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Build query
        query = Product.query
        
        # Apply filters
        if search_name:
            products = Product.search_by_name(search_name)
            query = Product.query.filter(Product.id.in_([p.id for p in products]))
        
        if category_id:
            query = query.filter(Product.category_id == category_id)
        
        if supplier_id:
            query = query.filter(Product.supplier_id == supplier_id)
        
        if active_only:
            query = query.filter(Product._is_active == True)
        
        # Get paginated results
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        products = pagination.items
        
        # Filter by stock status if requested
        if stock_status:
            products = [p for p in products if p.get_stock_status() == stock_status.upper()]
        
        return jsonify({
            'success': True,
            'data': [product.to_dict() for product in products],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            },
            'count': len(products)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@product_bp.route('/products', methods=['POST'])
def create_product():
    """
    Create a new product.
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
        unit_price = data.get('unit_price')
        cost_price = data.get('cost_price')
        category_id = data.get('category_id')
        supplier_id = data.get('supplier_id')
        
        # Validate required fields
        if not all([name, code, unit_price is not None, cost_price is not None, category_id, supplier_id]):
            return jsonify({
                'success': False,
                'error': 'Name, code, unit_price, cost_price, category_id, and supplier_id are required'
            }), 400
        
        # Check if product with same code already exists
        existing = Product.query.filter_by(_code=code.upper()).first()
        if existing:
            return jsonify({
                'success': False,
                'error': f'Product with code {code.upper()} already exists'
            }), 409
        
        # Validate category and supplier exist
        category = Category.query.get(category_id)
        if not category:
            return jsonify({
                'success': False,
                'error': f'Category with ID {category_id} not found'
            }), 404
        
        supplier = Supplier.query.get(supplier_id)
        if not supplier:
            return jsonify({
                'success': False,
                'error': f'Supplier with ID {supplier_id} not found'
            }), 404
        
        # Extract optional fields
        barcode = data.get('barcode')
        description = data.get('description')
        minimum_stock = data.get('minimum_stock', 0)
        maximum_stock = data.get('maximum_stock', 1000)
        unit_of_measure = data.get('unit_of_measure', 'PCS')
        expiry_date = data.get('expiry_date')
        
        # Parse expiry date if provided
        if expiry_date:
            try:
                expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid expiry date format. Use YYYY-MM-DD'
                }), 400
        
        # Create new product
        product = Product(
            name=name,
            code=code,
            unit_price=unit_price,
            cost_price=cost_price,
            category_id=category_id,
            supplier_id=supplier_id,
            barcode=barcode,
            description=description,
            minimum_stock=minimum_stock,
            maximum_stock=maximum_stock,
            unit_of_measure=unit_of_measure,
            expiry_date=expiry_date
        )
        
        # Validate product
        validation_errors = product.validate()
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Validation failed',
                'details': validation_errors
            }), 400
        
        # Save to database
        db.session.add(product)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': product.to_dict(),
            'message': 'Product created successfully'
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


@product_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """
    Get a specific product by ID.
    """
    try:
        product = Product.query.get_or_404(product_id)
        return jsonify({
            'success': True,
            'data': product.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404


@product_bp.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """
    Update an existing product.
    Supports partial updates with validation.
    """
    try:
        product = Product.query.get_or_404(product_id)
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Update fields if provided
        if 'name' in data:
            product.set_name(data['name'])
        
        if 'code' in data:
            # Check if new code conflicts with existing products
            existing = Product.query.filter(
                Product._code == data['code'].upper(),
                Product.id != product_id
            ).first()
            if existing:
                return jsonify({
                    'success': False,
                    'error': f'Product with code {data["code"].upper()} already exists'
                }), 409
            product.set_code(data['code'])
        
        if 'barcode' in data:
            product.set_barcode(data['barcode'])
        
        if 'description' in data:
            product.set_description(data['description'])
        
        if 'unit_price' in data:
            product.set_unit_price(data['unit_price'])
        
        if 'cost_price' in data:
            product.set_cost_price(data['cost_price'])
        
        if 'minimum_stock' in data or 'maximum_stock' in data:
            min_stock = data.get('minimum_stock', product.minimum_stock)
            max_stock = data.get('maximum_stock', product.maximum_stock)
            product.set_stock_limits(min_stock, max_stock)
        
        if 'unit_of_measure' in data:
            product.set_unit_of_measure(data['unit_of_measure'])
        
        if 'expiry_date' in data:
            expiry_date = data['expiry_date']
            if expiry_date:
                try:
                    expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({
                        'success': False,
                        'error': 'Invalid expiry date format. Use YYYY-MM-DD'
                    }), 400
            product.set_expiry_date(expiry_date)
        
        if 'category_id' in data:
            category = Category.query.get(data['category_id'])
            if not category:
                return jsonify({
                    'success': False,
                    'error': f'Category with ID {data["category_id"]} not found'
                }), 404
            product.category_id = data['category_id']
        
        if 'supplier_id' in data:
            supplier = Supplier.query.get(data['supplier_id'])
            if not supplier:
                return jsonify({
                    'success': False,
                    'error': f'Supplier with ID {data["supplier_id"]} not found'
                }), 404
            product.supplier_id = data['supplier_id']
        
        if 'is_active' in data:
            if data['is_active']:
                product.activate()
            else:
                product.deactivate()
        
        # Validate updated product
        validation_errors = product.validate()
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
            'data': product.to_dict(),
            'message': 'Product updated successfully'
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


@product_bp.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """
    Delete a product.
    Checks for dependencies before deletion.
    """
    try:
        product = Product.query.get_or_404(product_id)
        
        # Check if product has stock transactions
        if product.stock_transactions:
            return jsonify({
                'success': False,
                'error': f'Cannot delete product. It has {len(product.stock_transactions)} associated stock transactions.'
            }), 409
        
        # Delete product
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Product deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@product_bp.route('/products/<int:product_id>/stock', methods=['POST'])
def update_product_stock(product_id):
    """
    Update product stock quantity.
    Supports add, reduce, and set operations.
    """
    try:
        product = Product.query.get_or_404(product_id)
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        operation = data.get('operation')  # 'add', 'reduce', 'set'
        quantity = data.get('quantity')
        
        if not operation or quantity is None:
            return jsonify({
                'success': False,
                'error': 'Operation and quantity are required'
            }), 400
        
        if operation not in ['add', 'reduce', 'set']:
            return jsonify({
                'success': False,
                'error': 'Operation must be "add", "reduce", or "set"'
            }), 400
        
        old_quantity = product.stock_quantity
        
        if operation == 'add':
            new_quantity = product.add_stock(quantity)
        elif operation == 'reduce':
            new_quantity = product.reduce_stock(quantity)
        elif operation == 'set':
            if quantity < 0:
                return jsonify({
                    'success': False,
                    'error': 'Stock quantity cannot be negative'
                }), 400
            product._stock_quantity = quantity
            new_quantity = quantity
        
        # Save changes
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'product_id': product_id,
                'operation': operation,
                'quantity_changed': quantity,
                'old_quantity': old_quantity,
                'new_quantity': new_quantity,
                'stock_status': product.get_stock_status()
            },
            'message': f'Stock {operation} operation completed successfully'
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


@product_bp.route('/products/search', methods=['GET'])
def search_products():
    """
    Search products by name, code, or barcode.
    """
    try:
        search_term = request.args.get('q', '')
        search_type = request.args.get('type', 'name')  # 'name', 'code', or 'barcode'
        
        if not search_term:
            return jsonify({
                'success': False,
                'error': 'Search term is required'
            }), 400
        
        if search_type == 'name':
            products = Product.search_by_name(search_term)
        elif search_type == 'code':
            products = Product.search_by_code(search_term)
        elif search_type == 'barcode':
            product = Product.search_by_barcode(search_term)
            products = [product] if product else []
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid search type. Use "name", "code", or "barcode"'
            }), 400
        
        return jsonify({
            'success': True,
            'data': [product.to_dict() for product in products],
            'count': len(products),
            'search_term': search_term,
            'search_type': search_type
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@product_bp.route('/products/low-stock', methods=['GET'])
def get_low_stock_products():
    """
    Get products with low stock levels.
    """
    try:
        products = Product.query.filter(Product._is_active == True).all()
        low_stock_products = [p for p in products if p.get_stock_status() in ['LOW_STOCK', 'OUT_OF_STOCK']]
        
        return jsonify({
            'success': True,
            'data': [product.to_dict() for product in low_stock_products],
            'count': len(low_stock_products)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@product_bp.route('/products/expiring', methods=['GET'])
def get_expiring_products():
    """
    Get products that are expiring soon.
    """
    try:
        days_ahead = request.args.get('days', 30, type=int)
        products = Product.query.filter(
            Product._is_active == True,
            Product._expiry_date.isnot(None)
        ).all()
        
        expiring_products = []
        for product in products:
            days_until_expiry = product.days_until_expiry()
            if days_until_expiry is not None and days_until_expiry <= days_ahead:
                product_dict = product.to_dict()
                product_dict['days_until_expiry'] = days_until_expiry
                product_dict['is_expired'] = product.is_expired()
                expiring_products.append(product_dict)
        
        return jsonify({
            'success': True,
            'data': expiring_products,
            'count': len(expiring_products),
            'days_ahead': days_ahead
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

