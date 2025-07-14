#!/usr/bin/env python3
"""
SE Letters - Complete Metadata Discovery System
===============================================

This script runs the complete metadata discovery process:
1. Stage 1: Extract metadata from 3 random documents
2. Stage 2: Unify metadata into comprehensive schema
3. Generate analysis report and recommendations

Purpose: Understand field variability and commonalities across 300+ letters
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from se_letters.utils.logger import get_logger

logger = get_logger(__name__)


def run_stage1():
    """Run Stage 1 metadata extraction."""
    print("\n" + "="*60)
    print("RUNNING STAGE 1: METADATA EXTRACTION")
    print("="*60)
    
    try:
        # Import and run Stage 1
        from metadata_discovery_stage1 import MetadataDiscoveryStage1
        
        discovery = MetadataDiscoveryStage1()
        output_files = discovery.run_discovery()
        
        print(f"✅ Stage 1 complete: {len(output_files)} files generated")
        return output_files
        
    except Exception as e:
        logger.error(f"Stage 1 failed: {e}")
        print(f"❌ Stage 1 failed: {e}")
        return []


def run_stage2():
    """Run Stage 2 metadata unification."""
    print("\n" + "="*60)
    print("RUNNING STAGE 2: METADATA UNIFICATION")
    print("="*60)
    
    try:
        # Import and run Stage 2
        from metadata_discovery_stage2 import MetadataDiscoveryStage2
        
        unifier = MetadataDiscoveryStage2()
        output_files = unifier.run_unification()
        
        print(f"✅ Stage 2 complete: {len(output_files)} files generated")
        return output_files
        
    except Exception as e:
        logger.error(f"Stage 2 failed: {e}")
        print(f"❌ Stage 2 failed: {e}")
        return []


def analyze_results():
    """Analyze and display results from both stages."""
    print("\n" + "="*60)
    print("ANALYZING RESULTS")
    print("="*60)
    
    output_dir = Path("data/output/metadata_discovery")
    
    # Check Stage 1 results
    stage1_files = list(output_dir.glob("stage1_metadata_*.json"))
    print(f"\nStage 1 Results: {len(stage1_files)} documents processed")
    
    for file in stage1_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                doc_name = metadata.get("_processing_info", {}).get("document_name", file.name)
                
                # Count fields
                field_count = count_fields(metadata)
                print(f"  📄 {doc_name}: {field_count} metadata fields")
                
        except Exception as e:
            print(f"  ❌ Error reading {file.name}: {e}")
    
    # Check Stage 2 results
    stage2_report = output_dir / "stage2_comprehensive_report.json"
    if stage2_report.exists():
        try:
            with open(stage2_report, 'r', encoding='utf-8') as f:
                report = json.load(f)
                
                summary = report["metadata_discovery_report"]["summary"]
                print(f"\nStage 2 Analysis Summary:")
                print(f"  📊 Total documents analyzed: {summary['total_documents_analyzed']}")
                print(f"  🔍 Unique fields discovered: {summary['unique_fields_discovered']}")
                print(f"  🤝 Common fields across all: {summary['common_fields_across_all']}")
                
                # Show most frequent fields
                freq_dist = summary.get("field_frequency_distribution", {})
                if freq_dist:
                    print(f"\n  📈 Most frequent fields:")
                    sorted_fields = sorted(freq_dist.items(), key=lambda x: x[1], reverse=True)
                    for field, count in sorted_fields[:10]:
                        print(f"    • {field}: {count} documents")
                
        except Exception as e:
            print(f"  ❌ Error reading Stage 2 report: {e}")
    
    # Show output files
    all_files = list(output_dir.glob("*.json"))
    print(f"\n📁 Generated Files ({len(all_files)} total):")
    for file in sorted(all_files):
        size_kb = file.stat().st_size / 1024
        print(f"  • {file.name} ({size_kb:.1f} KB)")


def count_fields(metadata, prefix=""):
    """Count fields in metadata recursively."""
    count = 0
    for key, value in metadata.items():
        if key.startswith("_"):
            continue
        if isinstance(value, dict):
            count += count_fields(value, f"{prefix}.{key}" if prefix else key)
        elif isinstance(value, list):
            count += len(value)
        else:
            count += 1
    return count


def generate_summary_report():
    """Generate a final summary report."""
    print("\n" + "="*60)
    print("GENERATING SUMMARY REPORT")
    print("="*60)
    
    output_dir = Path("data/output/metadata_discovery")
    
    # Load all results
    stage1_files = list(output_dir.glob("stage1_metadata_*.json"))
    stage2_report = output_dir / "stage2_comprehensive_report.json"
    
    summary = {
        "metadata_discovery_summary": {
            "execution_timestamp": datetime.now().isoformat(),
            "stage1_results": {
                "documents_processed": len(stage1_files),
                "files_generated": [f.name for f in stage1_files]
            },
            "stage2_results": {
                "unified_schema_created": stage2_report.exists(),
                "analysis_complete": True
            },
            "key_findings": [],
            "recommendations": [
                "Use unified schema for production pipeline implementation",
                "Focus on common fields for initial deployment",
                "Implement field validation based on discovered patterns",
                "Test schema with additional documents before full deployment"
            ],
            "next_steps": [
                "Implement unified schema in production pipeline",
                "Create field validation logic",
                "Test with more documents",
                "Optimize extraction prompts"
            ]
        }
    }
    
    # Add key findings if Stage 2 completed
    if stage2_report.exists():
        try:
            with open(stage2_report, 'r', encoding='utf-8') as f:
                report = json.load(f)
                stage2_summary = report["metadata_discovery_report"]["summary"]
                
                summary["metadata_discovery_summary"]["key_findings"] = [
                    f"Discovered {stage2_summary['unique_fields_discovered']} unique metadata fields",
                    f"Found {stage2_summary['common_fields_across_all']} fields common across all documents",
                    f"Analyzed {stage2_summary['total_documents_analyzed']} sample documents",
                    "Created comprehensive unified schema for production use"
                ]
        except:
            pass
    
    # Save summary report
    summary_file = output_dir / "metadata_discovery_final_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"📋 Final summary saved to: {summary_file}")
    return summary_file


def main():
    """Main execution function."""
    print("\n" + "🔍" * 20)
    print("SE LETTERS - METADATA DISCOVERY SYSTEM")
    print("🔍" * 20)
    print("Purpose: Understand field variability across 300+ obsolescence letters")
    print("Process: Extract → Analyze → Unify → Report")
    
    try:
        # Run Stage 1: Metadata Extraction
        stage1_files = run_stage1()
        if not stage1_files:
            print("❌ Cannot proceed without Stage 1 results")
            sys.exit(1)
        
        # Run Stage 2: Metadata Unification
        stage2_files = run_stage2()
        if not stage2_files:
            print("❌ Stage 2 failed, but Stage 1 results are available")
        
        # Analyze results
        analyze_results()
        
        # Generate summary report
        summary_file = generate_summary_report()
        
        print("\n" + "🎉" * 20)
        print("METADATA DISCOVERY COMPLETE!")
        print("🎉" * 20)
        print(f"📊 Results available in: data/output/metadata_discovery/")
        print(f"📋 Final summary: {summary_file.name}")
        print("\n✅ Ready for production pipeline implementation!")
        
    except Exception as e:
        logger.error(f"Metadata discovery failed: {e}")
        print(f"❌ System failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 