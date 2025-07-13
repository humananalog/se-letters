#!/usr/bin/env python3
"""
Demonstration of the new modular pipeline architecture.
Shows how to build and configure pipelines with different components.
"""

import sys
import asyncio
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from se_letters.core.config import get_config
from se_letters.core.factory import PipelineFactory, PipelineBuilder
from se_letters.core.event_bus import EventTypes


async def demo_standard_pipeline():
    """Demonstrate standard pipeline execution."""
    print("🔧 MODULAR PIPELINE ARCHITECTURE DEMO")
    print("=" * 60)
    
    # Load configuration
    config = get_config()
    
    # Create pipeline factory
    factory = PipelineFactory(config)
    
    # Create standard pipeline
    pipeline = factory.create_pipeline("standard")
    
    print(f"✅ Created standard pipeline with {len(pipeline.get_stages())} stages")
    print(f"📋 Stages: {', '.join(pipeline.get_stages())}")
    
    # Prepare input data
    input_data = {
        'input_files': [
            'data/input/letters/sample_letter.pdf'
        ]
    }
    
    # Execute pipeline
    print("\n🚀 Executing standard pipeline...")
    result = await pipeline.execute_pipeline(input_data)
    
    if result.success:
        print("✅ Pipeline executed successfully!")
        print(f"📊 Results: {result.metadata}")
    else:
        print(f"❌ Pipeline failed: {result.error}")
    
    return result


async def demo_parallel_pipeline():
    """Demonstrate parallel pipeline execution."""
    print("\n🔄 PARALLEL PIPELINE DEMO")
    print("=" * 40)
    
    # Load configuration
    config = get_config()
    
    # Create pipeline factory
    factory = PipelineFactory(config)
    
    # Create parallel pipeline
    pipeline = factory.create_pipeline("parallel")
    
    print(f"✅ Created parallel pipeline with {len(pipeline.get_stages())} stages")
    
    # Prepare input data
    input_data = {
        'input_files': [
            'data/input/letters/sample1.pdf',
            'data/input/letters/sample2.pdf'
        ]
    }
    
    # Execute pipeline
    print("\n🚀 Executing parallel pipeline...")
    result = await pipeline.execute_pipeline(input_data)
    
    if result.success:
        print("✅ Parallel pipeline executed successfully!")
        print(f"📊 Results: {result.metadata}")
    else:
        print(f"❌ Parallel pipeline failed: {result.error}")
    
    return result


async def demo_custom_pipeline():
    """Demonstrate custom pipeline creation."""
    print("\n🎨 CUSTOM PIPELINE DEMO")
    print("=" * 30)
    
    # Load configuration
    config = get_config()
    
    # Create pipeline factory
    factory = PipelineFactory(config)
    
    # Define custom stages
    stage_definitions = {
        'document_processing': {
            'type': 'document_processing',
            'params': {}
        },
        'metadata_extraction': {
            'type': 'metadata_extraction',
            'params': {}
        },
        'product_matching': {
            'type': 'product_matching',
            'params': {}
        },
        'custom_reporting': {
            'type': 'report_generation',
            'params': {
                'formats': ['excel', 'json', 'summary']
            }
        }
    }
    
    # Create custom pipeline
    pipeline = factory.create_custom_pipeline(stage_definitions)
    
    print(f"✅ Created custom pipeline with {len(pipeline.get_stages())} stages")
    print(f"📋 Stages: {', '.join(pipeline.get_stages())}")
    
    # Prepare input data
    input_data = {
        'input_files': [
            'data/input/letters/custom_sample.pdf'
        ]
    }
    
    # Execute pipeline
    print("\n🚀 Executing custom pipeline...")
    result = await pipeline.execute_pipeline(input_data)
    
    if result.success:
        print("✅ Custom pipeline executed successfully!")
        print(f"📊 Results: {result.metadata}")
    else:
        print(f"❌ Custom pipeline failed: {result.error}")
    
    return result


async def demo_pipeline_builder():
    """Demonstrate pipeline builder pattern."""
    print("\n🏗️ PIPELINE BUILDER DEMO")
    print("=" * 35)
    
    # Load configuration
    config = get_config()
    
    # Create pipeline factory
    factory = PipelineFactory(config)
    
    # Use builder pattern to create pipeline
    pipeline = (PipelineBuilder(factory)
                .with_parallel_execution()
                .with_report_formats(['excel', 'json'])
                .with_validation({'min_products': 1})
                .build())
    
    print(f"✅ Built pipeline with {len(pipeline.get_stages())} stages")
    print(f"📋 Stages: {', '.join(pipeline.get_stages())}")
    
    # Prepare input data
    input_data = {
        'input_files': [
            'data/input/letters/builder_sample.pdf'
        ]
    }
    
    # Execute pipeline
    print("\n🚀 Executing builder pipeline...")
    result = await pipeline.execute_pipeline(input_data)
    
    if result.success:
        print("✅ Builder pipeline executed successfully!")
        print(f"📊 Results: {result.metadata}")
    else:
        print(f"❌ Builder pipeline failed: {result.error}")
    
    return result


def demo_event_handling():
    """Demonstrate event handling capabilities."""
    print("\n📡 EVENT HANDLING DEMO")
    print("=" * 30)
    
    # Load configuration
    config = get_config()
    
    # Create pipeline factory
    factory = PipelineFactory(config)
    
    # Get event bus
    event_bus = factory.get_event_bus()
    
    # Define event handlers
    def on_pipeline_started(data):
        print(f"🎬 Pipeline started with {len(data['stages'])} stages")
    
    def on_stage_completed(data):
        stage = data['stage']
        error_count = len(data['errors'])
        print(f"✅ Stage '{stage}' completed with {error_count} errors")
    
    def on_pipeline_completed(data):
        success = data['result'].success
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"🏁 Pipeline completed: {status}")
    
    # Subscribe to events
    event_bus.subscribe(EventTypes.PIPELINE_STARTED, on_pipeline_started)
    event_bus.subscribe(EventTypes.PIPELINE_STAGE_COMPLETED, on_stage_completed)
    event_bus.subscribe(EventTypes.PIPELINE_COMPLETED, on_pipeline_completed)
    
    print("📡 Event handlers registered")
    print(f"📊 Event types: {event_bus.get_event_types()}")
    
    return event_bus


def demo_service_container():
    """Demonstrate service container capabilities."""
    print("\n🏭 SERVICE CONTAINER DEMO")
    print("=" * 35)
    
    # Load configuration
    config = get_config()
    
    # Create pipeline factory
    factory = PipelineFactory(config)
    
    # Get service container
    container = factory.get_container()
    
    # Show registered services
    services = container.get_registered_services()
    print(f"📦 Registered services: {len(services)}")
    for name, service_type in services.items():
        print(f"  - {name}: {service_type}")
    
    # Test service retrieval
    from se_letters.core.config import Config
    from se_letters.services.document_processor import DocumentProcessor
    
    config_service = container.get_service(Config)
    doc_processor = container.get_service(DocumentProcessor)
    
    print(f"✅ Retrieved config service: {type(config_service)}")
    print(f"✅ Retrieved document processor: {type(doc_processor)}")
    
    return container


def demo_plugin_system():
    """Demonstrate plugin system capabilities."""
    print("\n🔌 PLUGIN SYSTEM DEMO")
    print("=" * 30)
    
    # Load configuration
    config = get_config()
    
    # Create pipeline factory
    factory = PipelineFactory(config)
    
    # Get plugin manager
    plugin_manager = factory.get_plugin_manager()
    
    # Show plugin capabilities
    plugin_types = plugin_manager.list_plugin_types()
    print(f"🔌 Plugin types: {plugin_types}")
    
    # Example: Register a custom plugin
    class CustomDocumentProcessor:
        """Example custom document processor."""
        _plugin_type = "document_processor"
        _plugin_name = "custom_processor"
        
        def process_document(self, file_path):
            return f"Processed {file_path} with custom processor"
    
    # Register the plugin
    plugin_manager.register_plugin(
        "document_processor", 
        "custom_processor", 
        CustomDocumentProcessor
    )
    
    # List available plugins
    processors = plugin_manager.list_plugins("document_processor")
    print(f"📄 Document processors: {processors}")
    
    return plugin_manager


async def main():
    """Main demonstration function."""
    print("🚀 MODULAR PIPELINE ARCHITECTURE DEMONSTRATION")
    print("=" * 80)
    
    # Demo different pipeline types
    try:
        # Standard pipeline
        await demo_standard_pipeline()
        
        # Parallel pipeline
        await demo_parallel_pipeline()
        
        # Custom pipeline
        await demo_custom_pipeline()
        
        # Builder pattern
        await demo_pipeline_builder()
        
        # Event handling
        demo_event_handling()
        
        # Service container
        demo_service_container()
        
        # Plugin system
        demo_plugin_system()
        
        print("\n🎉 ALL DEMOS COMPLETED SUCCESSFULLY!")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 