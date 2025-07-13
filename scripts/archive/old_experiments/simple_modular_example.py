#!/usr/bin/env python3
"""
Simple example of using the new modular pipeline architecture.
This shows the basic usage patterns for the modular system.
"""

import sys
import asyncio
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from se_letters.core import (
    PipelineFactory, 
    PipelineBuilder,
    get_config
)


async def simple_pipeline_example():
    """Simple example of creating and running a modular pipeline."""
    print("🔧 Simple Modular Pipeline Example")
    print("=" * 50)
    
    # 1. Load configuration
    config = get_config()
    print("✅ Configuration loaded")
    
    # 2. Create pipeline factory
    factory = PipelineFactory(config)
    print("✅ Pipeline factory created")
    
    # 3. Create a standard pipeline
    pipeline = factory.create_pipeline("standard")
    print(f"✅ Standard pipeline created with {len(pipeline.get_stages())} stages")
    print(f"📋 Stages: {', '.join(pipeline.get_stages())}")
    
    # 4. Prepare input data
    input_data = {
        'input_files': [
            # Add your document paths here
            'data/input/letters/sample.pdf'
        ]
    }
    
    # 5. Execute pipeline
    print("\n🚀 Executing pipeline...")
    result = await pipeline.execute_pipeline(input_data)
    
    # 6. Check results
    if result.success:
        print("✅ Pipeline executed successfully!")
        print(f"📊 Metadata: {result.metadata}")
        
        # Access the results
        if 'matched_products' in result.data:
            products = result.data['matched_products']
            print(f"🎯 Found {len(products)} matching products")
        
        if 'generated_reports' in result.data:
            reports = result.data['generated_reports']
            print(f"📄 Generated {len(reports)} reports")
    else:
        print(f"❌ Pipeline failed: {result.error}")
    
    return result


async def builder_pattern_example():
    """Example using the builder pattern for pipeline creation."""
    print("\n🏗️ Builder Pattern Example")
    print("=" * 40)
    
    # Load configuration
    config = get_config()
    factory = PipelineFactory(config)
    
    # Use builder pattern to create customized pipeline
    pipeline = (PipelineBuilder(factory)
                .with_parallel_execution()
                .with_report_formats(['excel', 'json'])
                .with_validation({'min_products': 1})
                .build())
    
    print(f"✅ Built pipeline with {len(pipeline.get_stages())} stages")
    print("📋 Configuration:")
    print("  - Parallel execution enabled")
    print("  - Report formats: Excel, JSON")
    print("  - Validation enabled")
    
    # Prepare input data
    input_data = {
        'input_files': [
            'data/input/letters/example.pdf'
        ]
    }
    
    # Execute pipeline
    print("\n🚀 Executing builder pipeline...")
    result = await pipeline.execute_pipeline(input_data)
    
    if result.success:
        print("✅ Builder pipeline executed successfully!")
    else:
        print(f"❌ Builder pipeline failed: {result.error}")
    
    return result


async def custom_pipeline_example():
    """Example of creating a custom pipeline with specific stages."""
    print("\n🎨 Custom Pipeline Example")
    print("=" * 40)
    
    # Load configuration
    config = get_config()
    factory = PipelineFactory(config)
    
    # Define custom stage configuration
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
    
    print(f"✅ Custom pipeline created with {len(pipeline.get_stages())} stages")
    print("📋 Custom stages:")
    for stage in pipeline.get_stages():
        print(f"  - {stage}")
    
    # Prepare input data
    input_data = {
        'input_files': [
            'data/input/letters/custom_example.pdf'
        ]
    }
    
    # Execute pipeline
    print("\n🚀 Executing custom pipeline...")
    result = await pipeline.execute_pipeline(input_data)
    
    if result.success:
        print("✅ Custom pipeline executed successfully!")
    else:
        print(f"❌ Custom pipeline failed: {result.error}")
    
    return result


def event_handling_example():
    """Example of event handling in the modular pipeline."""
    print("\n📡 Event Handling Example")
    print("=" * 40)
    
    # Load configuration
    config = get_config()
    factory = PipelineFactory(config)
    
    # Get event bus
    event_bus = factory.get_event_bus()
    
    # Define event handlers
    def on_pipeline_started(data):
        print(f"🎬 Pipeline started with stages: {data['stages']}")
    
    def on_stage_completed(data):
        stage = data['stage']
        print(f"✅ Stage completed: {stage}")
    
    def on_pipeline_completed(data):
        success = data['result'].success
        print(f"🏁 Pipeline finished: {'SUCCESS' if success else 'FAILED'}")
    
    # Subscribe to events
    from se_letters.core import EventTypes
    event_bus.subscribe(EventTypes.PIPELINE_STARTED, on_pipeline_started)
    event_bus.subscribe(EventTypes.PIPELINE_STAGE_COMPLETED, on_stage_completed)
    event_bus.subscribe(EventTypes.PIPELINE_COMPLETED, on_pipeline_completed)
    
    print("📡 Event handlers registered")
    print(f"📊 Available event types: {len(event_bus.get_event_types())}")
    
    return event_bus


async def main():
    """Main function demonstrating modular pipeline usage."""
    print("🚀 MODULAR PIPELINE EXAMPLES")
    print("=" * 60)
    
    try:
        # Simple pipeline example
        await simple_pipeline_example()
        
        # Builder pattern example
        await builder_pattern_example()
        
        # Custom pipeline example
        await custom_pipeline_example()
        
        # Event handling example
        event_handling_example()
        
        print("\n🎉 All examples completed!")
        
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 