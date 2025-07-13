"""Modular pipeline orchestrator for the SE Letters pipeline."""

from typing import Dict, List, Any, Optional
import asyncio
from collections import defaultdict

from .interfaces import IPipelineOrchestrator, IPipelineStage, PipelineContext
from .interfaces import ProcessingResult
from .event_bus import EventBus, EventTypes
from ..utils.logger import get_logger

logger = get_logger(__name__)


class PipelineOrchestrator(IPipelineOrchestrator):
    """Orchestrator for modular pipeline execution."""
    
    def __init__(self, event_bus: EventBus = None):
        """Initialize the orchestrator.
        
        Args:
            event_bus: Event bus for component communication
        """
        self.event_bus = event_bus or EventBus()
        self._stages: Dict[str, IPipelineStage] = {}
        self._stage_order: List[str] = []
        self._dependencies: Dict[str, List[str]] = {}
    
    def add_stage(self, stage: IPipelineStage) -> None:
        """Add a stage to the pipeline.
        
        Args:
            stage: Pipeline stage to add
        """
        stage_name = stage.get_stage_name()
        self._stages[stage_name] = stage
        self._dependencies[stage_name] = stage.get_dependencies()
        
        # Rebuild stage order
        self._rebuild_stage_order()
        
        logger.info(f"Added stage: {stage_name}")
    
    def remove_stage(self, stage_name: str) -> None:
        """Remove a stage from the pipeline.
        
        Args:
            stage_name: Name of stage to remove
        """
        if stage_name in self._stages:
            del self._stages[stage_name]
            del self._dependencies[stage_name]
            
            # Remove from stage order
            if stage_name in self._stage_order:
                self._stage_order.remove(stage_name)
            
            logger.info(f"Removed stage: {stage_name}")
    
    def get_stages(self) -> List[str]:
        """Get list of registered stages in execution order.
        
        Returns:
            List of stage names in execution order
        """
        return self._stage_order.copy()
    
    def get_stage_dependencies(self, stage_name: str) -> List[str]:
        """Get dependencies for a stage.
        
        Args:
            stage_name: Name of the stage
            
        Returns:
            List of dependency stage names
        """
        return self._dependencies.get(stage_name, [])
    
    async def execute_pipeline(self, input_data: Dict[str, Any]) -> ProcessingResult:
        """Execute the complete pipeline.
        
        Args:
            input_data: Input data for the pipeline
            
        Returns:
            Processing result with pipeline output
        """
        logger.info("Starting pipeline execution")
        
        # Publish pipeline started event
        self.event_bus.publish(EventTypes.PIPELINE_STARTED, {
            'stages': self._stage_order,
            'input_data': input_data
        })
        
        try:
            # Initialize pipeline context
            context = PipelineContext(
                stage="initialization",
                data=input_data.copy(),
                metadata={},
                errors=[]
            )
            
            # Execute stages in order
            for stage_name in self._stage_order:
                logger.info(f"Executing stage: {stage_name}")
                
                stage = self._stages[stage_name]
                context.stage = stage_name
                
                # Execute the stage
                context = await stage.execute(context)
                
                # Publish stage completed event
                self.event_bus.publish(EventTypes.PIPELINE_STAGE_COMPLETED, {
                    'stage': stage_name,
                    'context': context,
                    'errors': context.errors
                })
                
                logger.info(f"Completed stage: {stage_name}")
            
            # Create final result
            result = ProcessingResult(
                success=len(context.errors) == 0,
                data=context.data,
                metadata=context.metadata
            )
            
            if context.errors:
                result.error = f"Pipeline completed with {len(context.errors)} errors"
            
            # Publish pipeline completed event
            self.event_bus.publish(EventTypes.PIPELINE_COMPLETED, {
                'result': result,
                'context': context
            })
            
            logger.info("Pipeline execution completed")
            return result
            
        except Exception as e:
            error_msg = f"Pipeline execution failed: {e}"
            logger.error(error_msg)
            
            # Publish pipeline error event
            self.event_bus.publish(EventTypes.PIPELINE_ERROR, {
                'error': error_msg,
                'exception': e
            })
            
            return ProcessingResult(
                success=False,
                error=error_msg
            )
    
    async def execute_stage(
        self, stage_name: str, context: PipelineContext
    ) -> PipelineContext:
        """Execute a single stage.
        
        Args:
            stage_name: Name of the stage to execute
            context: Pipeline context
            
        Returns:
            Updated pipeline context
        """
        if stage_name not in self._stages:
            raise ValueError(f"Stage '{stage_name}' not found")
        
        stage = self._stages[stage_name]
        return await stage.execute(context)
    
    def validate_pipeline(self) -> List[str]:
        """Validate the pipeline configuration.
        
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check for circular dependencies
        try:
            self._rebuild_stage_order()
        except ValueError as e:
            errors.append(f"Circular dependency detected: {e}")
        
        # Check that all dependencies exist
        for stage_name, deps in self._dependencies.items():
            for dep in deps:
                if dep not in self._stages:
                    errors.append(f"Stage '{stage_name}' depends on missing stage '{dep}'")
        
        return errors
    
    def _rebuild_stage_order(self) -> None:
        """Rebuild the stage execution order based on dependencies."""
        # Topological sort to determine execution order
        visited = set()
        temp_visited = set()
        result = []
        
        def visit(stage_name: str):
            if stage_name in temp_visited:
                raise ValueError(f"Circular dependency involving {stage_name}")
            
            if stage_name in visited:
                return
            
            temp_visited.add(stage_name)
            
            # Visit dependencies first
            for dep in self._dependencies.get(stage_name, []):
                if dep in self._stages:
                    visit(dep)
            
            temp_visited.remove(stage_name)
            visited.add(stage_name)
            result.append(stage_name)
        
        # Visit all stages
        for stage_name in self._stages:
            if stage_name not in visited:
                visit(stage_name)
        
        self._stage_order = result
    
    def get_pipeline_info(self) -> Dict[str, Any]:
        """Get information about the pipeline.
        
        Returns:
            Dictionary with pipeline information
        """
        return {
            'stages': self._stage_order,
            'dependencies': self._dependencies,
            'stage_count': len(self._stages),
            'validation_errors': self.validate_pipeline()
        }
    
    def clear_pipeline(self) -> None:
        """Clear all stages from the pipeline."""
        self._stages.clear()
        self._dependencies.clear()
        self._stage_order.clear()
        logger.info("Pipeline cleared")


class ParallelPipelineOrchestrator(PipelineOrchestrator):
    """Orchestrator that can execute independent stages in parallel."""
    
    async def execute_pipeline(self, input_data: Dict[str, Any]) -> ProcessingResult:
        """Execute the pipeline with parallel stage execution where possible.
        
        Args:
            input_data: Input data for the pipeline
            
        Returns:
            Processing result with pipeline output
        """
        logger.info("Starting parallel pipeline execution")
        
        # Publish pipeline started event
        self.event_bus.publish(EventTypes.PIPELINE_STARTED, {
            'stages': self._stage_order,
            'input_data': input_data,
            'parallel': True
        })
        
        try:
            # Initialize pipeline context
            context = PipelineContext(
                stage="initialization",
                data=input_data.copy(),
                metadata={},
                errors=[]
            )
            
            # Group stages by dependency level
            stage_levels = self._group_stages_by_level()
            
            # Execute stages level by level
            for level, stage_names in enumerate(stage_levels):
                logger.info(f"Executing level {level}: {stage_names}")
                
                if len(stage_names) == 1:
                    # Single stage, execute normally
                    stage_name = stage_names[0]
                    stage = self._stages[stage_name]
                    context.stage = stage_name
                    context = await stage.execute(context)
                else:
                    # Multiple stages, execute in parallel
                    tasks = []
                    for stage_name in stage_names:
                        stage = self._stages[stage_name]
                        # Create a copy of context for each stage
                        stage_context = PipelineContext(
                            stage=stage_name,
                            data=context.data.copy(),
                            metadata=context.metadata.copy(),
                            errors=context.errors.copy()
                        )
                        tasks.append(stage.execute(stage_context))
                    
                    # Wait for all stages to complete
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Merge results back into main context
                    for i, result in enumerate(results):
                        if isinstance(result, Exception):
                            context.errors.append(f"Stage {stage_names[i]} failed: {result}")
                        else:
                            # Merge data and metadata
                            context.data.update(result.data)
                            context.metadata.update(result.metadata)
                            context.errors.extend(result.errors)
                
                # Publish stage completed events
                for stage_name in stage_names:
                    self.event_bus.publish(EventTypes.PIPELINE_STAGE_COMPLETED, {
                        'stage': stage_name,
                        'context': context,
                        'errors': context.errors
                    })
                
                logger.info(f"Completed level {level}")
            
            # Create final result
            result = ProcessingResult(
                success=len(context.errors) == 0,
                data=context.data,
                metadata=context.metadata
            )
            
            if context.errors:
                result.error = f"Pipeline completed with {len(context.errors)} errors"
            
            # Publish pipeline completed event
            self.event_bus.publish(EventTypes.PIPELINE_COMPLETED, {
                'result': result,
                'context': context
            })
            
            logger.info("Parallel pipeline execution completed")
            return result
            
        except Exception as e:
            error_msg = f"Parallel pipeline execution failed: {e}"
            logger.error(error_msg)
            
            # Publish pipeline error event
            self.event_bus.publish(EventTypes.PIPELINE_ERROR, {
                'error': error_msg,
                'exception': e
            })
            
            return ProcessingResult(
                success=False,
                error=error_msg
            )
    
    def _group_stages_by_level(self) -> List[List[str]]:
        """Group stages by dependency level for parallel execution.
        
        Returns:
            List of stage groups, where each group can be executed in parallel
        """
        levels = []
        remaining_stages = set(self._stage_order)
        completed_stages = set()
        
        while remaining_stages:
            # Find stages that can be executed (all dependencies completed)
            ready_stages = []
            for stage_name in remaining_stages:
                deps = self._dependencies.get(stage_name, [])
                if all(dep in completed_stages for dep in deps):
                    ready_stages.append(stage_name)
            
            if not ready_stages:
                # Should not happen if dependencies are valid
                raise ValueError("No stages ready for execution - circular dependency?")
            
            levels.append(ready_stages)
            remaining_stages -= set(ready_stages)
            completed_stages.update(ready_stages)
        
        return levels 