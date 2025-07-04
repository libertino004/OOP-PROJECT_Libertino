"""
Base abstract classes and interfaces for the Alfamart Stock Management System.
This module implements inheritance, abstract classes, and interfaces as required.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class BaseEntity(ABC):
    """
    Abstract base class for all entities in the system.
    Implements common functionality and enforces interface contracts.
    """
    
    @abstractmethod
    def to_dict(self):
        """Convert entity to dictionary representation"""
        pass
    
    @abstractmethod
    def validate(self):
        """Validate entity data"""
        pass


class Auditable(ABC):
    """
    Interface for entities that require audit trail.
    Demonstrates interface implementation.
    """
    
    @abstractmethod
    def get_created_at(self):
        """Get creation timestamp"""
        pass
    
    @abstractmethod
    def get_updated_at(self):
        """Get last update timestamp"""
        pass


class Searchable(ABC):
    """
    Interface for entities that can be searched.
    Demonstrates multiple interface inheritance.
    """
    
    @abstractmethod
    def search_by_name(self, name):
        """Search entities by name"""
        pass
    
    @abstractmethod
    def search_by_code(self, code):
        """Search entities by code"""
        pass


class StockOperations(ABC):
    """
    Abstract class defining stock operation contracts.
    Demonstrates abstract method implementation.
    """
    
    @abstractmethod
    def add_stock(self, quantity):
        """Add stock quantity"""
        pass
    
    @abstractmethod
    def reduce_stock(self, quantity):
        """Reduce stock quantity"""
        pass
    
    @abstractmethod
    def check_availability(self, required_quantity):
        """Check if required quantity is available"""
        pass


class NotificationService(ABC):
    """
    Abstract notification service for polymorphism demonstration.
    """
    
    @abstractmethod
    def send_notification(self, message, recipient):
        """Send notification"""
        pass


class EmailNotificationService(NotificationService):
    """
    Email notification implementation.
    Demonstrates static polymorphism.
    """
    
    def send_notification(self, message, recipient):
        """Send email notification"""
        print(f"Email sent to {recipient}: {message}")
        return True


class SMSNotificationService(NotificationService):
    """
    SMS notification implementation.
    Demonstrates static polymorphism.
    """
    
    def send_notification(self, message, recipient):
        """Send SMS notification"""
        print(f"SMS sent to {recipient}: {message}")
        return True


class NotificationManager:
    """
    Notification manager demonstrating dynamic polymorphism.
    Uses strategy pattern for runtime notification type selection.
    """
    
    def __init__(self):
        self._services = {
            'email': EmailNotificationService(),
            'sms': SMSNotificationService()
        }
    
    def send_notification(self, notification_type, message, recipient):
        """
        Send notification using specified service type.
        Demonstrates dynamic polymorphism.
        """
        service = self._services.get(notification_type)
        if service:
            return service.send_notification(message, recipient)
        else:
            raise ValueError(f"Unsupported notification type: {notification_type}")
    
    def add_service(self, service_type, service):
        """Add new notification service dynamically"""
        self._services[service_type] = service


# Mixin classes to resolve metaclass conflicts
class BaseEntityMixin:
    """
    Mixin class providing BaseEntity functionality without ABC metaclass.
    """
    
    def to_dict(self):
        """Default implementation - should be overridden"""
        raise NotImplementedError("Subclasses must implement to_dict method")
    
    def validate(self):
        """Default implementation - should be overridden"""
        raise NotImplementedError("Subclasses must implement validate method")


class AuditableMixin:
    """
    Mixin class providing Auditable functionality without ABC metaclass.
    """
    
    def get_created_at(self):
        """Default implementation - should be overridden"""
        raise NotImplementedError("Subclasses must implement get_created_at method")
    
    def get_updated_at(self):
        """Default implementation - should be overridden"""
        raise NotImplementedError("Subclasses must implement get_updated_at method")


class SearchableMixin:
    """
    Mixin class providing Searchable functionality without ABC metaclass.
    """
    
    @classmethod
    def search_by_name(cls, name):
        """Default implementation - should be overridden"""
        raise NotImplementedError("Subclasses must implement search_by_name method")
    
    @classmethod
    def search_by_code(cls, code):
        """Default implementation - should be overridden"""
        raise NotImplementedError("Subclasses must implement search_by_code method")


class StockOperationsMixin:
    """
    Mixin class providing StockOperations functionality without ABC metaclass.
    """
    
    def add_stock(self, quantity):
        """Default implementation - should be overridden"""
        raise NotImplementedError("Subclasses must implement add_stock method")
    
    def reduce_stock(self, quantity):
        """Default implementation - should be overridden"""
        raise NotImplementedError("Subclasses must implement reduce_stock method")
    
    def check_availability(self, required_quantity):
        """Default implementation - should be overridden"""
        raise NotImplementedError("Subclasses must implement check_availability method")

