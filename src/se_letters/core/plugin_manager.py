"""Plugin manager for modular pipeline components."""

from typing import Dict, Any, List, Type
import importlib
import inspect
from pathlib import Path

from .interfaces import IPluginManager
from .container import ServiceContainer


class PluginManager(IPluginManager):
    """Plugin manager for dynamic component loading."""
    
    def __init__(self, container: ServiceContainer):
        """Initialize the plugin manager.
        
        Args:
            container: Service container for dependency injection
        """
        self.container = container
        self._plugins: Dict[str, Dict[str, Type]] = {}
        self._instances: Dict[str, Any] = {}
    
    def register_plugin(
        self, plugin_type: str, plugin_name: str, plugin_class: Type
    ) -> None:
        """Register a plugin.
        
        Args:
            plugin_type: Type of plugin (e.g., 'document_processor')
            plugin_name: Name of the plugin (e.g., 'pdf_processor')
            plugin_class: Plugin class to register
        """
        if plugin_type not in self._plugins:
            self._plugins[plugin_type] = {}
        
        self._plugins[plugin_type][plugin_name] = plugin_class
    
    def get_plugin(self, plugin_type: str, plugin_name: str) -> Any:
        """Get a plugin instance.
        
        Args:
            plugin_type: Type of plugin
            plugin_name: Name of the plugin
            
        Returns:
            Plugin instance
            
        Raises:
            ValueError: If plugin is not registered
        """
        if plugin_type not in self._plugins:
            raise ValueError(f"Plugin type '{plugin_type}' not registered")
        
        if plugin_name not in self._plugins[plugin_type]:
            raise ValueError(
                f"Plugin '{plugin_name}' not found in type '{plugin_type}'"
            )
        
        # Create instance key
        instance_key = f"{plugin_type}:{plugin_name}"
        
        # Return cached instance if exists
        if instance_key in self._instances:
            return self._instances[instance_key]
        
        # Create new instance
        plugin_class = self._plugins[plugin_type][plugin_name]
        
        # Try to inject dependencies
        try:
            instance = self._create_instance_with_dependencies(plugin_class)
        except Exception:
            # Fallback to no-args constructor
            instance = plugin_class()
        
        self._instances[instance_key] = instance
        return instance
    
    def list_plugins(self, plugin_type: str) -> List[str]:
        """List available plugins of a type.
        
        Args:
            plugin_type: Type of plugin
            
        Returns:
            List of plugin names
        """
        if plugin_type not in self._plugins:
            return []
        
        return list(self._plugins[plugin_type].keys())
    
    def list_plugin_types(self) -> List[str]:
        """List all registered plugin types.
        
        Returns:
            List of plugin types
        """
        return list(self._plugins.keys())
    
    def discover_plugins(self, plugin_dir: Path) -> None:
        """Discover plugins from a directory.
        
        Args:
            plugin_dir: Directory to scan for plugins
        """
        if not plugin_dir.exists():
            return
        
        for plugin_file in plugin_dir.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue
            
            try:
                self._load_plugin_from_file(plugin_file)
            except Exception as e:
                print(f"Failed to load plugin {plugin_file}: {e}")
    
    def _create_instance_with_dependencies(self, plugin_class: Type) -> Any:
        """Create plugin instance with dependency injection.
        
        Args:
            plugin_class: Plugin class to instantiate
            
        Returns:
            Plugin instance with injected dependencies
        """
        # Get constructor signature
        sig = inspect.signature(plugin_class.__init__)
        
        # Build constructor arguments
        kwargs = {}
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            
            # Try to get service from container
            if param.annotation != inspect.Parameter.empty:
                try:
                    service = self.container.get_service(param.annotation)
                    kwargs[param_name] = service
                except ValueError:
                    # Service not available, skip if optional
                    if param.default == inspect.Parameter.empty:
                        raise
        
        return plugin_class(**kwargs)
    
    def _load_plugin_from_file(self, plugin_file: Path) -> None:
        """Load plugin from a Python file.
        
        Args:
            plugin_file: Path to plugin file
        """
        # Import the module
        module_name = plugin_file.stem
        spec = importlib.util.spec_from_file_location(
            module_name, plugin_file
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Look for plugin classes
        for name, obj in inspect.getmembers(module, inspect.isclass):
            # Skip imported classes
            if obj.__module__ != module_name:
                continue
            
            # Check if it has plugin metadata
            if hasattr(obj, '_plugin_type') and hasattr(obj, '_plugin_name'):
                self.register_plugin(
                    obj._plugin_type, obj._plugin_name, obj
                )
    
    def clear_plugins(self) -> None:
        """Clear all registered plugins."""
        self._plugins.clear()
        self._instances.clear()
    
    def get_plugin_info(
        self, plugin_type: str, plugin_name: str
    ) -> Dict[str, Any]:
        """Get information about a plugin.
        
        Args:
            plugin_type: Type of plugin
            plugin_name: Name of the plugin
            
        Returns:
            Dictionary with plugin information
        """
        if plugin_type not in self._plugins:
            return {}
        
        if plugin_name not in self._plugins[plugin_type]:
            return {}
        
        plugin_class = self._plugins[plugin_type][plugin_name]
        
        return {
            'name': plugin_name,
            'type': plugin_type,
            'class': plugin_class.__name__,
            'module': plugin_class.__module__,
            'doc': plugin_class.__doc__,
        } 