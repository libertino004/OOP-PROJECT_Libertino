"""
Supplier model for the Alfamart Stock Management System.
Demonstrates encapsulation, inheritance, and composition patterns.
"""

from datetime import datetime
from src.models.base import db, BaseEntityMixin, AuditableMixin, SearchableMixin


class ContactInfo:
    """
    Composition class for contact information.
    Demonstrates composition over inheritance principle.
    """
    
    def __init__(self, phone=None, email=None, address=None):
        self._phone = phone
        self._email = email
        self._address = address
    
    @property
    def phone(self):
        return self._phone
    
    @phone.setter
    def phone(self, value):
        if value and not self._validate_phone(value):
            raise ValueError("Invalid phone number format")
        self._phone = value
    
    @property
    def email(self):
        return self._email
    
    @email.setter
    def email(self, value):
        if value and not self._validate_email(value):
            raise ValueError("Invalid email format")
        self._email = value
    
    @property
    def address(self):
        return self._address
    
    @address.setter
    def address(self, value):
        self._address = value
    
    def _validate_phone(self, phone):
        """Validate phone number format"""
        import re
        pattern = r'^[\+]?[1-9][\d]{0,15}$'
        return re.match(pattern, phone.replace('-', '').replace(' ', ''))
    
    def _validate_email(self, email):
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email)
    
    def to_dict(self):
        """Convert contact info to dictionary"""
        return {
            'phone': self.phone,
            'email': self.email,
            'address': self.address
        }


class Supplier(db.Model, BaseEntityMixin, AuditableMixin, SearchableMixin):
    """
    Supplier model implementing inheritance and composition.
    Demonstrates encapsulation with private attributes and validation.
    """
    
    __tablename__ = 'suppliers'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Encapsulated attributes
    _name = db.Column('name', db.String(100), nullable=False)
    _code = db.Column('code', db.String(20), nullable=False, unique=True)
    _contact_phone = db.Column('contact_phone', db.String(20))
    _contact_email = db.Column('contact_email', db.String(100))
    _contact_address = db.Column('contact_address', db.Text)
    _is_active = db.Column('is_active', db.Boolean, default=True)
    _credit_limit = db.Column('credit_limit', db.Numeric(15, 2), default=0)
    _payment_terms = db.Column('payment_terms', db.Integer, default=30)  # days
    
    # Audit fields
    _created_at = db.Column('created_at', db.DateTime, default=datetime.utcnow)
    _updated_at = db.Column('updated_at', db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    products = db.relationship('Product', backref='supplier', lazy=True)
    
    def __init__(self, name, code, contact_info=None, credit_limit=0, payment_terms=30):
        """
        Initialize Supplier with validation.
        Demonstrates constructor with composition.
        """
        self.set_name(name)
        self.set_code(code)
        self.set_credit_limit(credit_limit)
        self.set_payment_terms(payment_terms)
        self._is_active = True
        
        # Composition: ContactInfo object
        if contact_info:
            self.set_contact_info(contact_info)
    
    # Property methods for encapsulation
    @property
    def name(self):
        """Get supplier name"""
        return self._name
    
    def set_name(self, name):
        """Set supplier name with validation"""
        if not name or len(name.strip()) < 2:
            raise ValueError("Supplier name must be at least 2 characters long")
        self._name = name.strip().title()
    
    @property
    def code(self):
        """Get supplier code"""
        return self._code
    
    def set_code(self, code):
        """Set supplier code with validation"""
        if not code or len(code.strip()) < 2:
            raise ValueError("Supplier code must be at least 2 characters long")
        self._code = code.strip().upper()
    
    @property
    def contact_info(self):
        """Get contact information as ContactInfo object"""
        return ContactInfo(
            phone=self._contact_phone,
            email=self._contact_email,
            address=self._contact_address
        )
    
    def set_contact_info(self, contact_info):
        """Set contact information from ContactInfo object"""
        if isinstance(contact_info, ContactInfo):
            self._contact_phone = contact_info.phone
            self._contact_email = contact_info.email
            self._contact_address = contact_info.address
        elif isinstance(contact_info, dict):
            # Create ContactInfo from dictionary
            contact = ContactInfo(
                phone=contact_info.get('phone'),
                email=contact_info.get('email'),
                address=contact_info.get('address')
            )
            self.set_contact_info(contact)
        else:
            raise ValueError("Contact info must be ContactInfo object or dictionary")
    
    @property
    def credit_limit(self):
        """Get credit limit"""
        return float(self._credit_limit) if self._credit_limit else 0
    
    def set_credit_limit(self, limit):
        """Set credit limit with validation"""
        if limit < 0:
            raise ValueError("Credit limit cannot be negative")
        self._credit_limit = limit
    
    @property
    def payment_terms(self):
        """Get payment terms in days"""
        return self._payment_terms
    
    def set_payment_terms(self, days):
        """Set payment terms with validation"""
        if days < 0:
            raise ValueError("Payment terms cannot be negative")
        self._payment_terms = days
    
    @property
    def is_active(self):
        """Get active status"""
        return self._is_active
    
    def activate(self):
        """Activate supplier"""
        self._is_active = True
        self._updated_at = datetime.utcnow()
    
    def deactivate(self):
        """Deactivate supplier"""
        self._is_active = False
        self._updated_at = datetime.utcnow()
    
    # Implementation of abstract methods from BaseEntity
    def to_dict(self):
        """Convert supplier to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'contact_info': self.contact_info.to_dict(),
            'is_active': self.is_active,
            'credit_limit': self.credit_limit,
            'payment_terms': self.payment_terms,
            'created_at': self.get_created_at().isoformat() if self.get_created_at() else None,
            'updated_at': self.get_updated_at().isoformat() if self.get_updated_at() else None,
            'product_count': len(self.products) if self.products else 0
        }
    
    def validate(self):
        """Validate supplier data"""
        errors = []
        
        if not self.name or len(self.name.strip()) < 2:
            errors.append("Supplier name must be at least 2 characters long")
        
        if not self.code or len(self.code.strip()) < 2:
            errors.append("Supplier code must be at least 2 characters long")
        
        if self.credit_limit < 0:
            errors.append("Credit limit cannot be negative")
        
        if self.payment_terms < 0:
            errors.append("Payment terms cannot be negative")
        
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
        """Search suppliers by name"""
        return cls.query.filter(cls._name.ilike(f'%{name}%')).all()
    
    @classmethod
    def search_by_code(cls, code):
        """Search suppliers by code"""
        return cls.query.filter(cls._code.ilike(f'%{code}%')).all()
    
    # Business methods
    def get_active_products(self):
        """Get all active products from this supplier"""
        return [product for product in self.products if product.is_active]
    
    def get_total_outstanding(self):
        """Calculate total outstanding amount (placeholder for future implementation)"""
        # This would typically calculate from purchase orders or invoices
        return 0
    
    def is_credit_available(self, amount):
        """Check if credit is available for given amount"""
        outstanding = self.get_total_outstanding()
        return (outstanding + amount) <= self.credit_limit
    
    def __repr__(self):
        """String representation of Supplier"""
        return f'<Supplier {self.code}: {self.name}>'
    
    def __str__(self):
        """Human-readable string representation"""
        return f"{self.name} ({self.code})"

