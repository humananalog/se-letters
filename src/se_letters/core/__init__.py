"""Core business logic and orchestration components."""

from .config import get_config, Config
from .pipeline import Pipeline
from .exceptions import (
    SELettersError,
    ProcessingError,
    ValidationError,
    APIError,
)

# New modular architecture components
from .interfaces import (
    IDocumentProcessor,
    IMetadataExtractor,
    IProductMatcher,
    IReportGenerator,
    IPipelineStage,
    IPipelineOrchestrator,
    IPluginManager,
    IServiceContainer,
    IEventBus,
    ProcessingResult,
    PipelineContext,
)
from .container import ServiceContainer
from .plugin_manager import PluginManager
from .event_bus import EventBus, EventTypes
from .orchestrator import PipelineOrchestrator, ParallelPipelineOrchestrator
from .factory import PipelineFactory, PipelineBuilder
from .stages import (
    DocumentProcessingStage,
    MetadataExtractionStage,
    ProductMatchingStage,
    ReportGenerationStage,
    ValidationStage,
)
from .adapters import (
    DocumentProcessorAdapter,
    MetadataExtractorAdapter,
    ProductMatcherAdapter,
    ReportGeneratorAdapter,
)

__all__ = [
    # Legacy components
    "get_config",
    "Config",
    "Pipeline",
    "SELettersError",
    "ProcessingError",
    "ValidationError",
    "APIError",
    
    # Modular architecture interfaces
    "IDocumentProcessor",
    "IMetadataExtractor",
    "IProductMatcher",
    "IReportGenerator",
    "IPipelineStage",
    "IPipelineOrchestrator",
    "IPluginManager",
    "IServiceContainer",
    "IEventBus",
    "ProcessingResult",
    "PipelineContext",
    
    # Core modular components
    "ServiceContainer",
    "PluginManager",
    "EventBus",
    "EventTypes",
    "PipelineOrchestrator",
    "ParallelPipelineOrchestrator",
    "PipelineFactory",
    "PipelineBuilder",
    
    # Pipeline stages
    "DocumentProcessingStage",
    "MetadataExtractionStage",
    "ProductMatchingStage",
    "ReportGenerationStage",
    "ValidationStage",
    
    # Service adapters
    "DocumentProcessorAdapter",
    "MetadataExtractorAdapter",
    "ProductMatcherAdapter",
    "ReportGeneratorAdapter",
] 