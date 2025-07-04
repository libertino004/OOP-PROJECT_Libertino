"""
Stock Transaction model for the Alfamart Stock Management System.
Demonstrates polymorphism, inheritance, and transaction patterns.
"""

from datetime import datetime
from enum import Enum
from src.models.base import db, BaseEntityMixin, AuditableMixin


class TransactionType(Enum):
    """
    Enumeration for transaction types.
    Demonstrates proper use of enums in OOP design.
    """
    STOCK_IN = "STOCK_IN"
    STOCK_OUT = "STOCK_OUT"
    ADJUSTMENT = "ADJUSTMENT"
    TRANSFER = "TRANSFER"
    RETURN = "RETURN"


class StockTransaction(db.Model, BaseEntityMixin, AuditableMixin):
    """
    Base stock transaction model.
    Demonstrates inheritance and polymorphism through transaction types.
    """
    
    __tablename__ = 'stock_transactions'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Polymorphic identity
    transaction_type = db.Column(db.Enum(TransactionType), nullable=False)
    
    # Common attributes
    _reference_number = db.Column('reference_number', db.String(50), nullable=False, unique=True)
    _quantity = db.Column('quantity', db.Integer, nullable=False)
    _unit_cost = db.Column('unit_cost', db.Numeric(10, 2))
    _notes = db.Column('notes', db.Text)
    _processed_by = db.Column('processed_by', db.String(100))
    _is_processed = db.Column('is_processed', db.Boolean, default=False)
    
    # Foreign keys
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    
    # Audit fields
    _created_at = db.Column('created_at', db.DateTime, default=datetime.utcnow)
    _updated_at = db.Column('updated_at', db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product = db.relationship('Product', backref='stock_transactions')
    
    # Polymorphic configuration
    __mapper_args__ = {
        'polymorphic_identity': 'base_transaction',
        'polymorphic_on': transaction_type
    }
    
    def __init__(self, reference_number, product_id, quantity, unit_cost=None, 
                 notes=None, processed_by=None):
        """
        Initialize base stock transaction.
        """
        self.set_reference_number(reference_number)
        self.product_id = product_id
        self.set_quantity(quantity)
        self.set_unit_cost(unit_cost)
        self.set_notes(notes)
        self.set_processed_by(processed_by)
        self._is_processed = False
    
    # Property methods for encapsulation
    @property
    def reference_number(self):
        """Get reference number"""
        return self._reference_number
    
    def set_reference_number(self, ref_number):
        """Set reference number with validation"""
        if not ref_number or len(ref_number.strip()) < 3:
            raise ValueError("Reference number must be at least 3 characters long")
        self._reference_number = ref_number.strip().upper()
    
    @property
    def quantity(self):
        """Get transaction quantity"""
        return self._quantity
    
    def set_quantity(self, quantity):
        """Set quantity with validation"""
        if quantity == 0:
            raise ValueError("Transaction quantity cannot be zero")
        self._quantity = quantity
    
    @property
    def unit_cost(self):
        """Get unit cost"""
        return float(self._unit_cost) if self._unit_cost else 0
    
    def set_unit_cost(self, cost):
        """Set unit cost with validation"""
        if cost is not None and cost < 0:
            raise ValueError("Unit cost cannot be negative")
        self._unit_cost = cost
    
    @property
    def notes(self):
        """Get transaction notes"""
        return self._notes
    
    def set_notes(self, notes):
        """Set transaction notes"""
        self._notes = notes.strip() if notes else None
    
    @property
    def processed_by(self):
        """Get processed by user"""
        return self._processed_by
    
    def set_processed_by(self, user):
        """Set processed by user"""
        self._processed_by = user.strip() if user else None
    
    @property
    def is_processed(self):
        """Get processed status"""
        return self._is_processed
    
    def process_transaction(self):
        """
        Process the transaction.
        Template method pattern - to be overridden by subclasses.
        """
        if self._is_processed:
            raise ValueError("Transaction already processed")
        
        # Validate transaction before processing
        errors = self.validate()
        if errors:
            raise ValueError(f"Transaction validation failed: {', '.join(errors)}")
        
        # Apply the transaction (to be implemented by subclasses)
        self._apply_transaction()
        
        # Mark as processed
        self._is_processed = True
        self._updated_at = datetime.utcnow()
    
    def _apply_transaction(self):
        """
        Apply the transaction to product stock.
        Abstract method to be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement _apply_transaction method")
    
    # Implementation of abstract methods from BaseEntity
    def to_dict(self):
        """Convert transaction to dictionary"""
        return {
            'id': self.id,
            'transaction_type': self.transaction_type.value if self.transaction_type else None,
            'reference_number': self.reference_number,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'unit_cost': self.unit_cost,
            'total_cost': self.get_total_cost(),
            'notes': self.notes,
            'processed_by': self.processed_by,
            'is_processed': self.is_processed,
            'created_at': self.get_created_at().isoformat() if self.get_created_at() else None,
            'updated_at': self.get_updated_at().isoformat() if self.get_updated_at() else None
        }
    
    def validate(self):
        """Validate transaction data"""
        errors = []
        
        if not self.reference_number or len(self.reference_number.strip()) < 3:
            errors.append("Reference number must be at least 3 characters long")
        
        if self.quantity == 0:
            errors.append("Transaction quantity cannot be zero")
        
        if self.unit_cost is not None and self.unit_cost < 0:
            errors.append("Unit cost cannot be negative")
        
        if not self.product_id:
            errors.append("Product ID is required")
        
        return errors
    
    # Implementation of Auditable interface
    def get_created_at(self):
        """Get creation timestamp"""
        return self._created_at
    
    def get_updated_at(self):
        """Get last update timestamp"""
        return self._updated_at
    
    # Business methods
    def get_total_cost(self):
        """Calculate total cost of transaction"""
        return abs(self.quantity) * self.unit_cost if self.unit_cost else 0
    
    def __repr__(self):
        """String representation of StockTransaction"""
        return f'<StockTransaction {self.reference_number}: {self.transaction_type.value if self.transaction_type else "Unknown"}>'


class StockInTransaction(StockTransaction):
    """
    Stock In transaction - demonstrates inheritance and polymorphism.
    """
    
    __mapper_args__ = {
        'polymorphic_identity': TransactionType.STOCK_IN
    }
    
    def __init__(self, reference_number, product_id, quantity, unit_cost, 
                 supplier_reference=None, notes=None, processed_by=None):
        """Initialize stock in transaction"""
        super().__init__(reference_number, product_id, quantity, unit_cost, notes, processed_by)
        self.transaction_type = TransactionType.STOCK_IN
        self._supplier_reference = supplier_reference
    
    def _apply_transaction(self):
        """Apply stock in transaction to product"""
        if self.product:
            self.product.add_stock(self.quantity)
    
    def validate(self):
        """Validate stock in transaction"""
        errors = super().validate()
        
        if self.quantity <= 0:
            errors.append("Stock in quantity must be positive")
        
        if not self.unit_cost or self.unit_cost <= 0:
            errors.append("Unit cost is required for stock in transactions")
        
        return errors


class StockOutTransaction(StockTransaction):
    """
    Stock Out transaction - demonstrates inheritance and polymorphism.
    """
    
    __mapper_args__ = {
        'polymorphic_identity': TransactionType.STOCK_OUT
    }
    
    def __init__(self, reference_number, product_id, quantity, 
                 customer_reference=None, notes=None, processed_by=None):
        """Initialize stock out transaction"""
        super().__init__(reference_number, product_id, -abs(quantity), None, notes, processed_by)
        self.transaction_type = TransactionType.STOCK_OUT
        self._customer_reference = customer_reference
    
    def _apply_transaction(self):
        """Apply stock out transaction to product"""
        if self.product:
            self.product.reduce_stock(abs(self.quantity))
    
    def validate(self):
        """Validate stock out transaction"""
        errors = super().validate()
        
        if self.quantity >= 0:
            errors.append("Stock out quantity must be negative")
        
        # Check if sufficient stock is available
        if self.product and not self.product.check_availability(abs(self.quantity)):
            errors.append(f"Insufficient stock. Available: {self.product.stock_quantity}, Required: {abs(self.quantity)}")
        
        return errors


class StockAdjustmentTransaction(StockTransaction):
    """
    Stock Adjustment transaction - demonstrates inheritance and polymorphism.
    """
    
    __mapper_args__ = {
        'polymorphic_identity': TransactionType.ADJUSTMENT
    }
    
    def __init__(self, reference_number, product_id, adjustment_quantity, 
                 reason=None, notes=None, processed_by=None):
        """Initialize stock adjustment transaction"""
        super().__init__(reference_number, product_id, adjustment_quantity, None, notes, processed_by)
        self.transaction_type = TransactionType.ADJUSTMENT
        self._reason = reason
    
    def _apply_transaction(self):
        """Apply stock adjustment transaction to product"""
        if self.product:
            if self.quantity > 0:
                self.product.add_stock(self.quantity)
            else:
                self.product.reduce_stock(abs(self.quantity))
    
    def validate(self):
        """Validate stock adjustment transaction"""
        errors = super().validate()
        
        if self.quantity == 0:
            errors.append("Adjustment quantity cannot be zero")
        
        # For negative adjustments, check if sufficient stock is available
        if self.quantity < 0 and self.product:
            if not self.product.check_availability(abs(self.quantity)):
                errors.append(f"Insufficient stock for adjustment. Available: {self.product.stock_quantity}, Required: {abs(self.quantity)}")
        
        return errors


# Factory pattern for creating transactions
class TransactionFactory:
    """
    Factory class for creating different types of stock transactions.
    Demonstrates factory pattern and polymorphism.
    """
    
    @staticmethod
    def create_transaction(transaction_type, **kwargs):
        """
        Create transaction based on type.
        Demonstrates static polymorphism through factory pattern.
        """
        if transaction_type == TransactionType.STOCK_IN:
            return StockInTransaction(**kwargs)
        elif transaction_type == TransactionType.STOCK_OUT:
            return StockOutTransaction(**kwargs)
        elif transaction_type == TransactionType.ADJUSTMENT:
            return StockAdjustmentTransaction(**kwargs)
        else:
            raise ValueError(f"Unsupported transaction type: {transaction_type}")
    
    @staticmethod
    def get_supported_types():
        """Get list of supported transaction types"""
        return [TransactionType.STOCK_IN, TransactionType.STOCK_OUT, TransactionType.ADJUSTMENT]

