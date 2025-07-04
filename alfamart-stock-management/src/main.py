import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS

# Import database and all models
from src.models.base import db
from src.models.category import Category
from src.models.supplier import Supplier
from src.models.product import Product
from src.models.stock_transaction import StockTransaction
from src.models.user import User

# Import all route blueprints
from src.routes.user import user_bp
from src.routes.category import category_bp
from src.routes.supplier import supplier_bp
from src.routes.product import product_bp
from src.routes.stock_transaction import stock_transaction_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Enable CORS for all routes
CORS(app)

# Register all blueprints with API prefix
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(category_bp, url_prefix='/api')
app.register_blueprint(supplier_bp, url_prefix='/api')
app.register_blueprint(product_bp, url_prefix='/api')
app.register_blueprint(stock_transaction_bp, url_prefix='/api')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Create all database tables
with app.app_context():
    db.create_all()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """
    Serve static files and handle SPA routing.
    """
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for monitoring.
    """
    return {
        'status': 'healthy',
        'message': 'Alfamart Stock Management System is running',
        'version': '1.0.0'
    }


@app.errorhandler(404)
def not_found(error):
    """
    Handle 404 errors with JSON response for API routes.
    """
    return {
        'success': False,
        'error': 'Resource not found'
    }, 404


@app.errorhandler(500)
def internal_error(error):
    """
    Handle 500 errors with JSON response.
    """
    db.session.rollback()
    return {
        'success': False,
        'error': 'Internal server error'
    }, 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

