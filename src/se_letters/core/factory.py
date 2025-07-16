"""Factory for building modular pipeline components."""

from typing import Dict, Any, Optional
from pathlib import Path

from .interfaces import IPipelineOrchestrator
from .container import ServiceContainer
from .plugin_manager import PluginManager
from .event_bus import EventBus
from .orchestrator import PipelineOrchestrator, ParallelPipelineOrchestrator
from .stages import (
    DocumentProcessingStage, MetadataExtractionStage, 
    ProductMatchingStage, ReportGenerationStage, ValidationStage
)
from .adapters import (
    DocumentProcessorAdapter, MetadataExtractorAdapter,
    ProductMatcherAdapter, ReportGeneratorAdapter
)
from .config import Config
from ..services.document_processor import DocumentProcessor
from ..services.xai_service import XAIService
from ..services.sota_product_database_service import SOTAProductDatabaseService
from ..services.embedding_service import EmbeddingService
from ..utils.logger import get_logger

logger = get_logger(__name__)


class PipelineFactory:
    """Factory for creating modular pipeline components."""
    
    def __init__(self, config: Config):
        """Initialize the factory.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.container = ServiceContainer()
        self.plugin_manager = PluginManager(self.container)
        self.event_bus = EventBus()
        
        # Register core services
        self._register_core_services()
    
    def _register_core_services(self) -> None:
        """Register core services in the container."""
        # Register configuration
        self.container.register_service(Config, self.config)
        
        # Register event bus
        self.container.register_service(EventBus, self.event_bus)
        
        # Register service factories
        self.container.register_factory(
            DocumentProcessor,
            lambda: DocumentProcessor(self.config)
        )
        
        self.container.register_factory(
            XAIService,
            lambda: XAIService(self.config)
        )
        
        self.container.register_singleton(
            SOTAProductDatabaseService,
            lambda: SOTAProductDatabaseService()
        )
        
        self.container.register_singleton(
            EmbeddingService,
            lambda: EmbeddingService(self.config)
        )
        
        logger.info("Core services registered")
    
    def create_pipeline(
        self, 
        pipeline_type: str = "standard",
        stages: Optional[Dict[str, Any]] = None
    ) -> IPipelineOrchestrator:
        """Create a configured pipeline.
        
        Args:
            pipeline_type: Type of pipeline ("standard" or "parallel")
            stages: Optional stage configuration
            
        Returns:
            Configured pipeline orchestrator
        """
        # Create orchestrator
        if pipeline_type == "parallel":
            orchestrator = ParallelPipelineOrchestrator(self.event_bus)
        else:
            orchestrator = PipelineOrchestrator(self.event_bus)
        
        # Add stages
        self._add_pipeline_stages(orchestrator, stages or {})
        
        stage_count = len(orchestrator.get_stages())
        logger.info(f"Created {pipeline_type} pipeline with {stage_count} stages")
        return orchestrator
    
    def _add_pipeline_stages(
        self, 
        orchestrator: IPipelineOrchestrator,
        stage_config: Dict[str, Any]
    ) -> None:
        """Add stages to the pipeline orchestrator.
        
        Args:
            orchestrator: Pipeline orchestrator
            stage_config: Stage configuration
        """
        # Create adapters for existing services
        doc_processor = DocumentProcessorAdapter(
            self.container.get_service(DocumentProcessor)
        )
        
        metadata_extractor = MetadataExtractorAdapter(
            self.container.get_service(XAIService)
        )
        
        product_matcher = ProductMatcherAdapter(
            self.container.get_service(SOTAProductDatabaseService),
            self.container.get_service(EmbeddingService)
        )
        
        # Create report generators
        report_generators = []
        report_formats = stage_config.get('report_formats', ['excel', 'json'])
        for format_type in report_formats:
            report_generators.append(ReportGeneratorAdapter(format_type))
        
        # Add stages to orchestrator
        orchestrator.add_stage(DocumentProcessingStage(doc_processor))
        orchestrator.add_stage(MetadataExtractionStage(metadata_extractor))
        orchestrator.add_stage(ProductMatchingStage(product_matcher))
        orchestrator.add_stage(ReportGenerationStage(report_generators))
        
        # Add validation stage if enabled
        if stage_config.get('enable_validation', True):
            validation_rules = stage_config.get('validation_rules', {})
            orchestrator.add_stage(ValidationStage(validation_rules))
    
    def create_custom_pipeline(
        self, 
        stage_definitions: Dict[str, Dict[str, Any]]
    ) -> IPipelineOrchestrator:
        """Create a custom pipeline with specific stage definitions.
        
        Args:
            stage_definitions: Dictionary mapping stage names to configurations
            
        Returns:
            Configured pipeline orchestrator
        """
        orchestrator = PipelineOrchestrator(self.event_bus)
        
        # Create stages based on definitions
        for stage_name, stage_config in stage_definitions.items():
            stage_type = stage_config.get('type')
            stage_params = stage_config.get('params', {})
            
            stage = self._create_stage(stage_type, stage_params)
            if stage:
                orchestrator.add_stage(stage)
            else:
                logger.warning(f"Failed to create stage: {stage_name}")
        
        return orchestrator
    
    def _create_stage(self, stage_type: str, params: Dict[str, Any]):
        """Create a stage based on type and parameters.
        
        Args:
            stage_type: Type of stage to create
            params: Stage parameters
            
        Returns:
            Created stage instance or None
        """
        if stage_type == "document_processing":
            processor = DocumentProcessorAdapter(
                self.container.get_service(DocumentProcessor)
            )
            return DocumentProcessingStage(processor)
        
        elif stage_type == "metadata_extraction":
            extractor = MetadataExtractorAdapter(
                self.container.get_service(XAIService)
            )
            return MetadataExtractionStage(extractor)
        
        elif stage_type == "product_matching":
            matcher = ProductMatcherAdapter(
                self.container.get_service(SOTAProductDatabaseService),
                self.container.get_service(EmbeddingService)
            )
            return ProductMatchingStage(matcher)
        
        elif stage_type == "report_generation":
            generators = []
            formats = params.get('formats', ['excel'])
            for format_type in formats:
                generators.append(ReportGeneratorAdapter(format_type))
            return ReportGenerationStage(generators)
        
        elif stage_type == "validation":
            rules = params.get('rules', {})
            return ValidationStage(rules)
        
        else:
            logger.error(f"Unknown stage type: {stage_type}")
            return None
    
    def register_plugin(
        self, 
        plugin_type: str, 
        plugin_name: str, 
        plugin_class: type
    ) -> None:
        """Register a plugin.
        
        Args:
            plugin_type: Type of plugin
            plugin_name: Name of the plugin
            plugin_class: Plugin class
        """
        self.plugin_manager.register_plugin(plugin_type, plugin_name, plugin_class)
    
    def discover_plugins(self, plugin_dir: Path) -> None:
        """Discover plugins from a directory.
        
        Args:
            plugin_dir: Directory to scan for plugins
        """
        self.plugin_manager.discover_plugins(plugin_dir)
    
    def get_container(self) -> ServiceContainer:
        """Get the service container.
        
        Returns:
            Service container instance
        """
        return self.container
    
    def get_plugin_manager(self) -> PluginManager:
        """Get the plugin manager.
        
        Returns:
            Plugin manager instance
        """
        return self.plugin_manager
    
    def get_event_bus(self) -> EventBus:
        """Get the event bus.
        
        Returns:
            Event bus instance
        """
        return self.event_bus


class PipelineBuilder:
    """Builder for creating pipelines with fluent interface."""
    
    def __init__(self, factory: PipelineFactory):
        """Initialize the builder.
        
        Args:
            factory: Pipeline factory
        """
        self.factory = factory
        self.pipeline_type = "standard"
        self.stage_config = {}
        self.custom_stages = {}
    
    def with_parallel_execution(self) -> 'PipelineBuilder':
        """Enable parallel execution where possible.
        
        Returns:
            Self for method chaining
        """
        self.pipeline_type = "parallel"
        return self
    
    def with_report_formats(self, formats: list) -> 'PipelineBuilder':
        """Set report formats.
        
        Args:
            formats: List of report formats
            
        Returns:
            Self for method chaining
        """
        self.stage_config['report_formats'] = formats
        return self
    
    def with_validation(self, rules: Dict[str, Any] = None) -> 'PipelineBuilder':
        """Enable validation with optional rules.
        
        Args:
            rules: Validation rules
            
        Returns:
            Self for method chaining
        """
        self.stage_config['enable_validation'] = True
        if rules:
            self.stage_config['validation_rules'] = rules
        return self
    
    def without_validation(self) -> 'PipelineBuilder':
        """Disable validation.
        
        Returns:
            Self for method chaining
        """
        self.stage_config['enable_validation'] = False
        return self
    
    def with_custom_stage(
        self, 
        stage_name: str, 
        stage_type: str, 
        params: Dict[str, Any] = None
    ) -> 'PipelineBuilder':
        """Add a custom stage.
        
        Args:
            stage_name: Name of the stage
            stage_type: Type of the stage
            params: Stage parameters
            
        Returns:
            Self for method chaining
        """
        self.custom_stages[stage_name] = {
            'type': stage_type,
            'params': params or {}
        }
        return self
    
    def build(self) -> IPipelineOrchestrator:
        """Build the pipeline.
        
        Returns:
            Configured pipeline orchestrator
        """
        if self.custom_stages:
            return self.factory.create_custom_pipeline(self.custom_stages)
        else:
            return self.factory.create_pipeline(self.pipeline_type, self.stage_config) 