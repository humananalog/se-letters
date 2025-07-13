"""Dependency injection container for modular pipeline components."""

from typing import Dict, Any, Type, Callable
from .interfaces import IServiceContainer


class ServiceContainer(IServiceContainer):
    """Simple dependency injection container."""
    
    def __init__(self):
        """Initialize the container."""
        self._services: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}
        self._singletons: Dict[Type, Any] = {}
    
    def register_service(
        self, service_type: Type, implementation: Any
    ) -> None:
        """Register a service implementation.
        
        Args:
            service_type: The interface or base class type
            implementation: The concrete implementation instance
        """
        self._services[service_type] = implementation
    
    def register_factory(
        self, service_type: Type, factory_func: Callable
    ) -> None:
        """Register a factory function for a service.
        
        Args:
            service_type: The interface or base class type
            factory_func: Factory function that creates the service
        """
        self._factories[service_type] = factory_func
    
    def register_singleton(
        self, service_type: Type, factory_func: Callable
    ) -> None:
        """Register a singleton service with factory function.
        
        Args:
            service_type: The interface or base class type
            factory_func: Factory function that creates the service
        """
        self._factories[service_type] = factory_func
        # Mark as singleton by adding to singletons dict
        if service_type not in self._singletons:
            self._singletons[service_type] = None
    
    def get_service(self, service_type: Type) -> Any:
        """Get a service instance.
        
        Args:
            service_type: The interface or base class type
            
        Returns:
            The service instance
            
        Raises:
            ValueError: If service is not registered
        """
        # Check if it's a direct service registration
        if service_type in self._services:
            return self._services[service_type]
        
        # Check if it's a singleton
        if service_type in self._singletons:
            if self._singletons[service_type] is None:
                # Create singleton instance
                factory = self._factories[service_type]
                self._singletons[service_type] = factory()
            return self._singletons[service_type]
        
        # Check if it's a factory
        if service_type in self._factories:
            factory = self._factories[service_type]
            return factory()
        
        raise ValueError(f"Service {service_type} is not registered")
    
    def has_service(self, service_type: Type) -> bool:
        """Check if a service is registered.
        
        Args:
            service_type: The interface or base class type
            
        Returns:
            True if service is registered, False otherwise
        """
        return (
            service_type in self._services or
            service_type in self._factories or
            service_type in self._singletons
        )
    
    def clear(self) -> None:
        """Clear all registered services."""
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()
    
    def get_registered_services(self) -> Dict[str, Type]:
        """Get all registered service types.
        
        Returns:
            Dictionary mapping service names to types
        """
        all_services = {}
        
        for service_type in self._services.keys():
            all_services[service_type.__name__] = service_type
            
        for service_type in self._factories.keys():
            all_services[service_type.__name__] = service_type
            
        return all_services 