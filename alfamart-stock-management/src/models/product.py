"""
Product model for the Alfamart Stock Management System.
Demonstrates inheritance, encapsulation, and polymorphism.
"""

from datetime import datetime
from decimal import Decimal
from src.models.base import db, BaseEntityMixin, AuditableMixin, SearchableMixin, StockOperationsMixin


class Product(db.Model, BaseEntityMixin, AuditableMixin, SearchableMixin, StockOperationsMixin):
    """
    Product model implementing multiple inheritance and interfaces.
    Demonstrates encapsulation, validation, and business logic.
    """
    
    __tablename__ = 'products'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Encapsulated attributes
    _name = db.Column('name', db.String(200), nullable=False)
    _code = db.Column('code', db.String(50), nullable=False, unique=True)
    _barcode = db.Column('barcode', db.String(50), unique=True)
    _description = db.Column('description', db.Text)
    _unit_price = db.Column('unit_price', db.Numeric(10, 2), nullable=False)
    _cost_price = db.Column('cost_price', db.Numeric(10, 2), nullable=False)
    _stock_quantity = db.Column('stock_quantity', db.Integer, default=0)
    _minimum_stock = db.Column('minimum_stock', db.Integer, default=0)
    _maximum_stock = db.Column('maximum_stock', db.Integer, default=1000)
    _unit_of_measure = db.Column('unit_of_measure', db.String(20), default='PCS')
    _is_active = db.Column('is_active', db.Boolean, default=True)
    _expiry_date = db.Column('expiry_date', db.Date)
    
    # Foreign keys
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    
    # Audit fields
    _created_at = db.Column('created_at', db.DateTime, default=datetime.utcnow)
    _updated_at = db.Column('updated_at', db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, name, code, unit_price, cost_price, category_id, supplier_id, 
                 barcode=None, description=None, minimum_stock=0, maximum_stock=1000, 
                 unit_of_measure='PCS', expiry_date=None):
        """
        Initialize Product with validation.
        Demonstrates constructor encapsulation and validation.
        """
        self.set_name(name)
        self.set_code(code)
        self.set_unit_price(unit_price)
        self.set_cost_price(cost_price)
        self.set_barcode(barcode)
        self.set_description(description)
        self.set_stock_limits(minimum_stock, maximum_stock)
        self.set_unit_of_measure(unit_of_measure)
        self.set_expiry_date(expiry_date)
        
        self.category_id = category_id
        self.supplier_id = supplier_id
        self._stock_quantity = 0
        self._is_active = True
    
    # Property methods for encapsulation
    @property
    def name(self):
        """Get product name"""
        return self._name
    
    def set_name(self, name):
        """Set product name with validation"""
        if not name or len(name.strip()) < 2:
            raise ValueError("Product name must be at least 2 characters long")
        self._name = name.strip().title()
    
    @property
    def code(self):
        """Get product code"""
        return self._code
    
    def set_code(self, code):
        """Set product code with validation"""
        if not code or len(code.strip()) < 2:
            raise ValueError("Product code must be at least 2 characters long")
        self._code = code.strip().upper()
    
    @property
    def barcode(self):
        """Get product barcode"""
        return self._barcode
    
    def set_barcode(self, barcode):
        """Set product barcode with validation"""
        if barcode and len(barcode.strip()) < 8:
            raise ValueError("Barcode must be at least 8 characters long")
        self._barcode = barcode.strip() if barcode else None
    
    @property
    def description(self):
        """Get product description"""
        return self._description
    
    def set_description(self, description):
        """Set product description"""
        self._description = description.strip() if description else None
    
    @property
    def unit_price(self):
        """Get unit price"""
        return float(self._unit_price) if self._unit_price else 0
    
    def set_unit_price(self, price):
        """Set unit price with validation"""
        if price < 0:
            raise ValueError("Unit price cannot be negative")
        self._unit_price = Decimal(str(price))
    
    @property
    def cost_price(self):
        """Get cost price"""
        return float(self._cost_price) if self._cost_price else 0
    
    def set_cost_price(self, price):
        """Set cost price with validation"""
        if price < 0:
            raise ValueError("Cost price cannot be negative")
        self._cost_price = Decimal(str(price))
    
    @property
    def stock_quantity(self):
        """Get current stock quantity"""
        return self._stock_quantity
    
    @property
    def minimum_stock(self):
        """Get minimum stock level"""
        return self._minimum_stock
    
    @property
    def maximum_stock(self):
        """Get maximum stock level"""
        return self._maximum_stock
    
    def set_stock_limits(self, minimum, maximum):
        """Set stock limits with validation"""
        if minimum < 0:
            raise ValueError("Minimum stock cannot be negative")
        if maximum < minimum:
            raise ValueError("Maximum stock cannot be less than minimum stock")
        self._minimum_stock = minimum
        self._maximum_stock = maximum
    
    @property
    def unit_of_measure(self):
        """Get unit of measure"""
        return self._unit_of_measure
    
    def set_unit_of_measure(self, unit):
        """Set unit of measure"""
        valid_units = ['PCS', 'KG', 'LTR', 'MTR', 'BOX', 'PACK']
        unit = unit.upper() if unit else 'PCS'
        if unit not in valid_units:
            raise ValueError(f"Unit of measure must be one of: {', '.join(valid_units)}")
        self._unit_of_measure = unit
    
    @property
    def expiry_date(self):
        """Get expiry date"""
        return self._expiry_date
    
    def set_expiry_date(self, date):
        """Set expiry date"""
        self._expiry_date = date
    
    @property
    def is_active(self):
        """Get active status"""
        return self._is_active
    
    def activate(self):
        """Activate product"""
        self._is_active = True
        self._updated_at = datetime.utcnow()
    
    def deactivate(self):
        """Deactivate product"""
        self._is_active = False
        self._updated_at = datetime.utcnow()
    
    # Implementation of StockOperations abstract methods
    def add_stock(self, quantity):
        """
        Add stock quantity with validation.
        Implementation of abstract method from StockOperations.
        """
        if quantity <= 0:
            raise ValueError("Quantity to add must be positive")
        
        new_quantity = self._stock_quantity + quantity
        if new_quantity > self._maximum_stock:
            raise ValueError(f"Adding {quantity} would exceed maximum stock limit of {self._maximum_stock}")
        
        self._stock_quantity = new_quantity
        self._updated_at = datetime.utcnow()
        return self._stock_quantity
    
    def reduce_stock(self, quantity):
        """
        Reduce stock quantity with validation.
        Implementation of abstract method from StockOperations.
        """
        if quantity <= 0:
            raise ValueError("Quantity to reduce must be positive")
        
        if quantity > self._stock_quantity:
            raise ValueError(f"Cannot reduce {quantity} items. Only {self._stock_quantity} available")
        
        self._stock_quantity -= quantity
        self._updated_at = datetime.utcnow()
        return self._stock_quantity
    
    def check_availability(self, required_quantity):
        """
        Check if required quantity is available.
        Implementation of abstract method from StockOperations.
        """
        return self._stock_quantity >= required_quantity
    
    # Implementation of abstract methods from BaseEntity
    def to_dict(self):
        """Convert product to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'barcode': self.barcode,
            'description': self.description,
            'unit_price': self.unit_price,
            'cost_price': self.cost_price,
            'stock_quantity': self.stock_quantity,
            'minimum_stock': self.minimum_stock,
            'maximum_stock': self.maximum_stock,
            'unit_of_measure': self.unit_of_measure,
            'is_active': self.is_active,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'category_id': self.category_id,
            'supplier_id': self.supplier_id,
            'created_at': self.get_created_at().isoformat() if self.get_created_at() else None,
            'updated_at': self.get_updated_at().isoformat() if self.get_updated_at() else None,
            'profit_margin': self.get_profit_margin(),
            'stock_value': self.get_stock_value(),
            'stock_status': self.get_stock_status()
        }
    
    def validate(self):
        """Validate product data"""
        errors = []
        
        if not self.name or len(self.name.strip()) < 2:
            errors.append("Product name must be at least 2 characters long")
        
        if not self.code or len(self.code.strip()) < 2:
            errors.append("Product code must be at least 2 characters long")
        
        if self.unit_price < 0:
            errors.append("Unit price cannot be negative")
        
        if self.cost_price < 0:
            errors.append("Cost price cannot be negative")
        
        if self.minimum_stock < 0:
            errors.append("Minimum stock cannot be negative")
        
        if self.maximum_stock < self.minimum_stock:
            errors.append("Maximum stock cannot be less than minimum stock")
        
        return errors
    
    # Implementation of Auditable interface
    def get_created_at(self):
        """Get creation timestamp"""
        return self._created_at
    
    def get_updated_at(self):
        """Get last update timestamp"""
        return self._updated_at
    
    # Implementation of Searchable interface
    @classmethod
    def search_by_name(cls, name):
        """Search products by name"""
        return cls.query.filter(cls._name.ilike(f'%{name}%')).all()
    
    @classmethod
    def search_by_code(cls, code):
        """Search products by code"""
        return cls.query.filter(cls._code.ilike(f'%{code}%')).all()
    
    @classmethod
    def search_by_barcode(cls, barcode):
        """Search products by barcode"""
        return cls.query.filter(cls._barcode == barcode).first()
    
    # Business methods
    def get_profit_margin(self):
        """Calculate profit margin percentage"""
        if self.cost_price == 0:
            return 0
        return ((self.unit_price - self.cost_price) / self.cost_price) * 100
    
    def get_stock_value(self):
        """Calculate total stock value at cost price"""
        return self.stock_quantity * self.cost_price
    
    def get_stock_status(self):
        """Get stock status based on minimum/maximum levels"""
        if self.stock_quantity == 0:
            return 'OUT_OF_STOCK'
        elif self.stock_quantity <= self.minimum_stock:
            return 'LOW_STOCK'
        elif self.stock_quantity >= self.maximum_stock:
            return 'OVERSTOCK'
        else:
            return 'NORMAL'
    
    def is_expired(self):
        """Check if product is expired"""
        if not self.expiry_date:
            return False
        return datetime.now().date() > self.expiry_date
    
    def days_until_expiry(self):
        """Calculate days until expiry"""
        if not self.expiry_date:
            return None
        delta = self.expiry_date - datetime.now().date()
        return delta.days
    
    def __repr__(self):
        """String representation of Product"""
        return f'<Product {self.code}: {self.name}>'
    
    def __str__(self):
        """Human-readable string representation"""
        return f"{self.name} ({self.code}) - Stock: {self.stock_quantity}"

