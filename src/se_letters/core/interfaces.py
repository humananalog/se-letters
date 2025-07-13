"""Interface definitions for modular pipeline components."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass

from ..models.document import Document


@dataclass
class ProcessingResult:
    """Result of a processing operation."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class PipelineContext:
    """Context passed between pipeline stages."""
    stage: str
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    errors: List[str]


class IDocumentProcessor(ABC):
    """Interface for document processing components."""
    
    @abstractmethod
    async def process_document(self, file_path: Path) -> ProcessingResult:
        """Process a single document."""
        pass
    
    @abstractmethod
    def supports_format(self, file_path: Path) -> bool:
        """Check if processor supports this file format."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources."""
        pass


class IMetadataExtractor(ABC):
    """Interface for metadata extraction components."""
    
    @abstractmethod
    async def extract_metadata(self, document: Document) -> ProcessingResult:
        """Extract metadata from document."""
        pass
    
    @abstractmethod
    def get_confidence_score(self) -> float:
        """Get confidence score for last extraction."""
        pass


class IProductMatcher(ABC):
    """Interface for product matching components."""
    
    @abstractmethod
    async def find_matching_products(
        self, metadata: Dict[str, Any]
    ) -> ProcessingResult:
        """Find products matching the metadata."""
        pass
    
    @abstractmethod
    async def build_index(self) -> None:
        """Build search index."""
        pass


class IReportGenerator(ABC):
    """Interface for report generation components."""
    
    @abstractmethod
    async def generate_report(
        self, results: List[ProcessingResult]
    ) -> ProcessingResult:
        """Generate final report."""
        pass
    
    @abstractmethod
    def supports_format(self, format_type: str) -> bool:
        """Check if generator supports this format."""
        pass


class IPipelineStage(ABC):
    """Interface for pipeline stages."""
    
    @abstractmethod
    async def execute(self, context: PipelineContext) -> PipelineContext:
        """Execute the pipeline stage."""
        pass
    
    @abstractmethod
    def get_stage_name(self) -> str:
        """Get the name of this stage."""
        pass
    
    @abstractmethod
    def get_dependencies(self) -> List[str]:
        """Get list of required previous stages."""
        pass


class IPipelineOrchestrator(ABC):
    """Interface for pipeline orchestration."""
    
    @abstractmethod
    async def execute_pipeline(
        self, input_data: Dict[str, Any]
    ) -> ProcessingResult:
        """Execute the complete pipeline."""
        pass
    
    @abstractmethod
    def add_stage(self, stage: IPipelineStage) -> None:
        """Add a stage to the pipeline."""
        pass
    
    @abstractmethod
    def remove_stage(self, stage_name: str) -> None:
        """Remove a stage from the pipeline."""
        pass


class IPluginManager(ABC):
    """Interface for plugin management."""
    
    @abstractmethod
    def register_plugin(
        self, plugin_type: str, plugin_name: str, plugin_class: type
    ) -> None:
        """Register a plugin."""
        pass
    
    @abstractmethod
    def get_plugin(self, plugin_type: str, plugin_name: str) -> Any:
        """Get a plugin instance."""
        pass
    
    @abstractmethod
    def list_plugins(self, plugin_type: str) -> List[str]:
        """List available plugins of a type."""
        pass


class IServiceContainer(ABC):
    """Interface for dependency injection container."""
    
    @abstractmethod
    def register_service(
        self, service_type: type, implementation: Any
    ) -> None:
        """Register a service implementation."""
        pass
    
    @abstractmethod
    def get_service(self, service_type: type) -> Any:
        """Get a service instance."""
        pass
    
    @abstractmethod
    def register_factory(
        self, service_type: type, factory_func: callable
    ) -> None:
        """Register a factory function for a service."""
        pass


class IEventBus(ABC):
    """Interface for event-driven communication."""
    
    @abstractmethod
    def publish(self, event_type: str, data: Dict[str, Any]) -> None:
        """Publish an event."""
        pass
    
    @abstractmethod
    def subscribe(self, event_type: str, handler: callable) -> None:
        """Subscribe to an event."""
        pass
    
    @abstractmethod
    def unsubscribe(self, event_type: str, handler: callable) -> None:
        """Unsubscribe from an event."""
        pass 