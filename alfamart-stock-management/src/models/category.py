"""
Category model for the Alfamart Stock Management System.
Demonstrates encapsulation, inheritance, and proper OOP design.
"""

from datetime import datetime
from src.models.base import db, BaseEntityMixin, AuditableMixin, SearchableMixin


class Category(db.Model, BaseEntityMixin, AuditableMixin, SearchableMixin):
    """
    Category model implementing multiple interfaces and inheritance.
    Demonstrates encapsulation with private attributes and public methods.
    """
    
    __tablename__ = 'categories'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Encapsulated attributes
    _name = db.Column('name', db.String(100), nullable=False, unique=True)
    _code = db.Column('code', db.String(20), nullable=False, unique=True)
    _description = db.Column('description', db.Text)
    _is_active = db.Column('is_active', db.Boolean, default=True)
    
    # Audit fields
    _created_at = db.Column('created_at', db.DateTime, default=datetime.utcnow)
    _updated_at = db.Column('updated_at', db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    products = db.relationship('Product', backref='category', lazy=True)
    
    def __init__(self, name, code, description=None):
        """
        Initialize Category with validation.
        Demonstrates constructor encapsulation.
        """
        self.set_name(name)
        self.set_code(code)
        self.set_description(description)
        self._is_active = True
    
    # Property methods for encapsulation
    @property
    def name(self):
        """Get category name"""
        return self._name
    
    def set_name(self, name):
        """
        Set category name with validation.
        Demonstrates encapsulation and data validation.
        """
        if not name or len(name.strip()) < 2:
            raise ValueError("Category name must be at least 2 characters long")
        self._name = name.strip().title()
    
    @property
    def code(self):
        """Get category code"""
        return self._code
    
    def set_code(self, code):
        """
        Set category code with validation.
        Demonstrates encapsulation and business rules.
        """
        if not code or len(code.strip()) < 2:
            raise ValueError("Category code must be at least 2 characters long")
        self._code = code.strip().upper()
    
    @property
    def description(self):
        """Get category description"""
        return self._description
    
    def set_description(self, description):
        """Set category description"""
        self._description = description.strip() if description else None
    
    @property
    def is_active(self):
        """Get active status"""
        return self._is_active
    
    def activate(self):
        """Activate category"""
        self._is_active = True
        self._updated_at = datetime.utcnow()
    
    def deactivate(self):
        """Deactivate category"""
        self._is_active = False
        self._updated_at = datetime.utcnow()
    
    # Implementation of abstract methods from BaseEntity
    def to_dict(self):
        """
        Convert category to dictionary.
        Implementation of abstract method from BaseEntity.
        """
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.get_created_at().isoformat() if self.get_created_at() else None,
            'updated_at': self.get_updated_at().isoformat() if self.get_updated_at() else None,
            'product_count': len(self.products) if self.products else 0
        }
    
    def validate(self):
        """
        Validate category data.
        Implementation of abstract method from BaseEntity.
        """
        errors = []
        
        if not self.name or len(self.name.strip()) < 2:
            errors.append("Category name must be at least 2 characters long")
        
        if not self.code or len(self.code.strip()) < 2:
            errors.append("Category code must be at least 2 characters long")
        
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
        """Search categories by name"""
        return cls.query.filter(cls._name.ilike(f'%{name}%')).all()
    
    @classmethod
    def search_by_code(cls, code):
        """Search categories by code"""
        return cls.query.filter(cls._code.ilike(f'%{code}%')).all()
    
    # Additional business methods
    def get_active_products(self):
        """Get all active products in this category"""
        return [product for product in self.products if product.is_active]
    
    def get_total_stock_value(self):
        """Calculate total stock value for this category"""
        total = 0
        for product in self.get_active_products():
            if hasattr(product, 'get_stock_value'):
                total += product.get_stock_value()
        return total
    
    def __repr__(self):
        """String representation of Category"""
        return f'<Category {self.code}: {self.name}>'
    
    def __str__(self):
        """Human-readable string representation"""
        return f"{self.name} ({self.code})"

