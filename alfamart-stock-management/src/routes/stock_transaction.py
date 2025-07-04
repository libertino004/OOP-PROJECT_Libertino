"""
Stock Transaction routes for the Alfamart Stock Management System.
Implements CRUD operations for stock transactions with polymorphism support.
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
from src.models.base import db
from src.models.stock_transaction import (
    StockTransaction, TransactionFactory, TransactionType,
    StockInTransaction, StockOutTransaction, StockAdjustmentTransaction
)
from src.models.product import Product

stock_transaction_bp = Blueprint('stock_transaction', __name__)


@stock_transaction_bp.route('/stock-transactions', methods=['GET'])
def get_stock_transactions():
    """
    Get all stock transactions with optional filtering.
    Supports filtering by product, transaction type, and date range.
    """
    try:
        # Get query parameters
        product_id = request.args.get('product_id', type=int)
        transaction_type = request.args.get('transaction_type', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        processed_only = request.args.get('processed_only', 'false').lower() == 'true'
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Build query
        query = StockTransaction.query
        
        # Apply filters
        if product_id:
            query = query.filter(StockTransaction.product_id == product_id)
        
        if transaction_type:
            try:
                trans_type = TransactionType(transaction_type.upper())
                query = query.filter(StockTransaction.transaction_type == trans_type)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': f'Invalid transaction type: {transaction_type}'
                }), 400
        
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(StockTransaction._created_at >= start_dt)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid start_date format. Use YYYY-MM-DD'
                }), 400
        
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                # Add one day to include the entire end date
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
                query = query.filter(StockTransaction._created_at <= end_dt)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid end_date format. Use YYYY-MM-DD'
                }), 400
        
        if processed_only:
            query = query.filter(StockTransaction._is_processed == True)
        
        # Order by creation date (newest first)
        query = query.order_by(StockTransaction._created_at.desc())
        
        # Get paginated results
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        transactions = pagination.items
        
        return jsonify({
            'success': True,
            'data': [transaction.to_dict() for transaction in transactions],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            },
            'count': len(transactions)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@stock_transaction_bp.route('/stock-transactions', methods=['POST'])
def create_stock_transaction():
    """
    Create a new stock transaction.
    Uses factory pattern to create appropriate transaction type.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Extract required fields
        transaction_type_str = data.get('transaction_type', '').upper()
        reference_number = data.get('reference_number')
        product_id = data.get('product_id')
        quantity = data.get('quantity')
        
        # Validate required fields
        if not all([transaction_type_str, reference_number, product_id, quantity is not None]):
            return jsonify({
                'success': False,
                'error': 'transaction_type, reference_number, product_id, and quantity are required'
            }), 400
        
        # Validate transaction type
        try:
            transaction_type = TransactionType(transaction_type_str)
        except ValueError:
            return jsonify({
                'success': False,
                'error': f'Invalid transaction type: {transaction_type_str}'
            }), 400
        
        # Check if reference number already exists
        existing = StockTransaction.query.filter_by(_reference_number=reference_number.upper()).first()
        if existing:
            return jsonify({
                'success': False,
                'error': f'Transaction with reference number {reference_number.upper()} already exists'
            }), 409
        
        # Validate product exists
        product = Product.query.get(product_id)
        if not product:
            return jsonify({
                'success': False,
                'error': f'Product with ID {product_id} not found'
            }), 404
        
        # Extract optional fields
        unit_cost = data.get('unit_cost')
        notes = data.get('notes')
        processed_by = data.get('processed_by')
        auto_process = data.get('auto_process', False)
        
        # Prepare transaction parameters
        transaction_params = {
            'reference_number': reference_number,
            'product_id': product_id,
            'quantity': quantity,
            'notes': notes,
            'processed_by': processed_by
        }
        
        # Add type-specific parameters
        if transaction_type == TransactionType.STOCK_IN:
            if not unit_cost or unit_cost <= 0:
                return jsonify({
                    'success': False,
                    'error': 'unit_cost is required and must be positive for stock in transactions'
                }), 400
            transaction_params['unit_cost'] = unit_cost
            transaction_params['supplier_reference'] = data.get('supplier_reference')
        
        elif transaction_type == TransactionType.STOCK_OUT:
            transaction_params['customer_reference'] = data.get('customer_reference')
        
        elif transaction_type == TransactionType.ADJUSTMENT:
            transaction_params['reason'] = data.get('reason')
        
        # Create transaction using factory
        transaction = TransactionFactory.create_transaction(transaction_type, **transaction_params)
        
        # Validate transaction
        validation_errors = transaction.validate()
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Validation failed',
                'details': validation_errors
            }), 400
        
        # Save to database
        db.session.add(transaction)
        db.session.commit()
        
        # Auto-process if requested
        if auto_process:
            try:
                transaction.process_transaction()
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'error': f'Transaction created but processing failed: {str(e)}'
                }), 500
        
        return jsonify({
            'success': True,
            'data': transaction.to_dict(),
            'message': f'Stock transaction created successfully{"and processed" if auto_process else ""}'
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


@stock_transaction_bp.route('/stock-transactions/<int:transaction_id>', methods=['GET'])
def get_stock_transaction(transaction_id):
    """
    Get a specific stock transaction by ID.
    """
    try:
        transaction = StockTransaction.query.get_or_404(transaction_id)
        
        # Include product information
        transaction_dict = transaction.to_dict()
        if transaction.product:
            transaction_dict['product'] = {
                'id': transaction.product.id,
                'name': transaction.product.name,
                'code': transaction.product.code,
                'current_stock': transaction.product.stock_quantity
            }
        
        return jsonify({
            'success': True,
            'data': transaction_dict
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404


@stock_transaction_bp.route('/stock-transactions/<int:transaction_id>/process', methods=['POST'])
def process_stock_transaction(transaction_id):
    """
    Process a stock transaction.
    Applies the transaction to product stock levels.
    """
    try:
        transaction = StockTransaction.query.get_or_404(transaction_id)
        
        if transaction.is_processed:
            return jsonify({
                'success': False,
                'error': 'Transaction is already processed'
            }), 409
        
        # Get current stock before processing
        old_stock = transaction.product.stock_quantity if transaction.product else 0
        
        # Process the transaction
        transaction.process_transaction()
        db.session.commit()
        
        # Get new stock after processing
        new_stock = transaction.product.stock_quantity if transaction.product else 0
        
        return jsonify({
            'success': True,
            'data': {
                'transaction': transaction.to_dict(),
                'stock_change': {
                    'old_stock': old_stock,
                    'new_stock': new_stock,
                    'change': new_stock - old_stock
                }
            },
            'message': 'Transaction processed successfully'
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


@stock_transaction_bp.route('/stock-transactions/<int:transaction_id>', methods=['PUT'])
def update_stock_transaction(transaction_id):
    """
    Update a stock transaction.
    Only allows updates to unprocessed transactions.
    """
    try:
        transaction = StockTransaction.query.get_or_404(transaction_id)
        
        if transaction.is_processed:
            return jsonify({
                'success': False,
                'error': 'Cannot update processed transaction'
            }), 409
        
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Update allowed fields
        if 'notes' in data:
            transaction.set_notes(data['notes'])
        
        if 'processed_by' in data:
            transaction.set_processed_by(data['processed_by'])
        
        if 'unit_cost' in data and hasattr(transaction, 'set_unit_cost'):
            transaction.set_unit_cost(data['unit_cost'])
        
        # Validate updated transaction
        validation_errors = transaction.validate()
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
            'data': transaction.to_dict(),
            'message': 'Transaction updated successfully'
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


@stock_transaction_bp.route('/stock-transactions/<int:transaction_id>', methods=['DELETE'])
def delete_stock_transaction(transaction_id):
    """
    Delete a stock transaction.
    Only allows deletion of unprocessed transactions.
    """
    try:
        transaction = StockTransaction.query.get_or_404(transaction_id)
        
        if transaction.is_processed:
            return jsonify({
                'success': False,
                'error': 'Cannot delete processed transaction'
            }), 409
        
        # Delete transaction
        db.session.delete(transaction)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Transaction deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@stock_transaction_bp.route('/stock-transactions/types', methods=['GET'])
def get_transaction_types():
    """
    Get supported transaction types.
    """
    try:
        types = TransactionFactory.get_supported_types()
        return jsonify({
            'success': True,
            'data': [t.value for t in types]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@stock_transaction_bp.route('/stock-transactions/summary', methods=['GET'])
def get_transaction_summary():
    """
    Get transaction summary statistics.
    """
    try:
        # Get query parameters for date filtering
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        
        query = StockTransaction.query.filter(StockTransaction._is_processed == True)
        
        # Apply date filters
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(StockTransaction._created_at >= start_dt)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid start_date format. Use YYYY-MM-DD'
                }), 400
        
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
                query = query.filter(StockTransaction._created_at <= end_dt)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid end_date format. Use YYYY-MM-DD'
                }), 400
        
        transactions = query.all()
        
        # Calculate summary statistics
        summary = {
            'total_transactions': len(transactions),
            'stock_in_count': 0,
            'stock_out_count': 0,
            'adjustment_count': 0,
            'total_stock_in_value': 0,
            'total_stock_out_value': 0,
            'total_adjustment_value': 0
        }
        
        for transaction in transactions:
            if transaction.transaction_type == TransactionType.STOCK_IN:
                summary['stock_in_count'] += 1
                summary['total_stock_in_value'] += transaction.get_total_cost()
            elif transaction.transaction_type == TransactionType.STOCK_OUT:
                summary['stock_out_count'] += 1
                summary['total_stock_out_value'] += transaction.get_total_cost()
            elif transaction.transaction_type == TransactionType.ADJUSTMENT:
                summary['adjustment_count'] += 1
                summary['total_adjustment_value'] += transaction.get_total_cost()
        
        return jsonify({
            'success': True,
            'data': summary,
            'date_range': {
                'start_date': start_date or 'All time',
                'end_date': end_date or 'All time'
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

