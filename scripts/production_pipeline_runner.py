#!/usr/bin/env python3
"""
Production Pipeline Runner
Processes documents through the complete production pipeline with full logging

Version: 2.1.0
Last Updated: 2025-01-27
"""

import sys
import argparse
import time
from pathlib import Path
from typing import List, Dict, Any

from loguru import logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from se_letters.services.production_pipeline_service import (
    ProductionPipelineService,
    ProcessingStatus,
    ProcessingResult
)


class ProductionPipelineRunner:
    """Production pipeline runner with comprehensive logging and error handling"""
    
    def __init__(self, db_path: str = "data/letters.duckdb"):
        """Initialize pipeline runner"""
        self.db_path = db_path
        self.pipeline_service = ProductionPipelineService(db_path)
        self.processing_results: List[ProcessingResult] = []
        
        # Setup runner-specific logging
        self._setup_logging()
        
        logger.info("🚀 Production Pipeline Runner initialized")
        logger.info(f"📊 Database: {self.db_path}")
    
    def _setup_logging(self) -> None:
        """Setup comprehensive logging for pipeline runner"""
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
        
        logger.configure(
            handlers=[
                {
                    "sink": sys.stdout,
                    "format": log_format,
                    "level": "INFO"
                },
                {
                    "sink": "logs/pipeline_runner.log",
                    "format": log_format,
                    "level": "DEBUG",
                    "rotation": "10 MB",
                    "retention": "7 days"
                },
                {
                    "sink": "logs/pipeline_runner_errors.log",
                    "format": log_format,
                    "level": "ERROR",
                    "rotation": "10 MB",
                    "retention": "30 days"
                }
            ]
        )
    
    def process_single_document(self, file_path: Path, force_reprocess: bool = False) -> ProcessingResult:
        """Process a single document through the pipeline"""
        logger.info(f"📄 Processing document: {file_path}")
        logger.info(f"🔄 Force reprocess: {force_reprocess}")
        
        if not file_path.exists():
            logger.error(f"❌ File not found: {file_path}")
            return ProcessingResult(
                success=False,
                status=ProcessingStatus.FAILED,
                error_message=f"File not found: {file_path}"
            )
        
        if not file_path.is_file():
            logger.error(f"❌ Path is not a file: {file_path}")
            return ProcessingResult(
                success=False,
                status=ProcessingStatus.FAILED,
                error_message=f"Path is not a file: {file_path}"
            )
        
        # Check file size
        file_size = file_path.stat().st_size
        if file_size == 0:
            logger.error(f"❌ Empty file: {file_path}")
            return ProcessingResult(
                success=False,
                status=ProcessingStatus.FAILED,
                error_message=f"Empty file: {file_path}"
            )
        
        if file_size > 50 * 1024 * 1024:  # 50MB limit
            logger.warning(f"⚠️ Large file detected: {file_size / (1024*1024):.2f}MB")
        
        try:
            # Process through pipeline
            result = self.pipeline_service.process_document(file_path, force_reprocess=force_reprocess)
            
            # Log result
            self._log_processing_result(file_path, result)
            
            # Store result
            self.processing_results.append(result)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Unexpected error processing {file_path}: {e}")
            return ProcessingResult(
                success=False,
                status=ProcessingStatus.FAILED,
                error_message=f"Unexpected error: {e}"
            )
    
    def process_directory(self, directory_path: Path, recursive: bool = False) -> List[ProcessingResult]:
        """Process all documents in a directory"""
        logger.info(f"📁 Processing directory: {directory_path}")
        logger.info(f"🔄 Recursive: {recursive}")
        
        if not directory_path.exists():
            logger.error(f"❌ Directory not found: {directory_path}")
            return []
        
        if not directory_path.is_dir():
            logger.error(f"❌ Path is not a directory: {directory_path}")
            return []
        
        # Supported file extensions
        supported_extensions = {'.pdf', '.docx', '.doc', '.txt'}
        
        # Find files
        if recursive:
            files = []
            for ext in supported_extensions:
                files.extend(directory_path.rglob(f"*{ext}"))
        else:
            files = []
            for ext in supported_extensions:
                files.extend(directory_path.glob(f"*{ext}"))
        
        if not files:
            logger.warning(f"⚠️ No supported files found in {directory_path}")
            return []
        
        logger.info(f"📊 Found {len(files)} files to process")
        
        results = []
        for i, file_path in enumerate(files, 1):
            logger.info(f"🔄 Processing file {i}/{len(files)}: {file_path.name}")
            
            result = self.process_single_document(file_path)
            results.append(result)
            
            # Brief pause between files
            time.sleep(0.1)
        
        return results
    
    def process_file_list(self, file_list: List[Path]) -> List[ProcessingResult]:
        """Process a list of files"""
        logger.info(f"📋 Processing {len(file_list)} files from list")
        
        results = []
        for i, file_path in enumerate(file_list, 1):
            logger.info(f"🔄 Processing file {i}/{len(file_list)}: {file_path.name}")
            
            result = self.process_single_document(file_path)
            results.append(result)
            
            # Brief pause between files
            time.sleep(0.1)
        
        return results
    
    def _log_processing_result(self, file_path: Path, result: ProcessingResult) -> None:
        """Log processing result with comprehensive details"""
        if result.success:
            if result.status == ProcessingStatus.COMPLETED:
                logger.success(f"✅ Successfully processed: {file_path.name}")
                logger.info(f"📊 Document ID: {result.document_id}")
                logger.info(f"🎯 Confidence: {result.confidence_score:.2f}")
                logger.info(f"⏱️ Processing time: {result.processing_time_ms:.2f}ms")
                
                if result.validation_result:
                    logger.info(f"📦 Product ranges: {result.validation_result.product_ranges}")
                
            elif result.status == ProcessingStatus.SKIPPED:
                logger.info(f"⏭️ Skipped (already processed): {file_path.name}")
                logger.info(f"📊 Document ID: {result.document_id}")
                
        else:
            logger.error(f"❌ Failed to process: {file_path.name}")
            logger.error(f"💥 Error: {result.error_message}")
            logger.error(f"⏱️ Failed after: {result.processing_time_ms:.2f}ms")
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate comprehensive summary report"""
        if not self.processing_results:
            return {"message": "No documents processed"}
        
        # Calculate statistics
        total_files = len(self.processing_results)
        successful = sum(1 for r in self.processing_results if r.success)
        failed = sum(1 for r in self.processing_results if not r.success)
        skipped = sum(1 for r in self.processing_results if r.status == ProcessingStatus.SKIPPED)
        completed = sum(1 for r in self.processing_results if r.status == ProcessingStatus.COMPLETED)
        
        # Calculate processing times
        processing_times = [r.processing_time_ms for r in self.processing_results if r.processing_time_ms > 0]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        # Calculate confidence scores
        confidence_scores = [r.confidence_score for r in self.processing_results if r.confidence_score > 0]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        # Get database statistics
        db_stats = self.pipeline_service.get_processing_statistics()
        
        summary = {
            "processing_session": {
                "total_files": total_files,
                "successful": successful,
                "failed": failed,
                "skipped": skipped,
                "completed": completed,
                "success_rate": (successful / total_files * 100) if total_files > 0 else 0,
                "avg_processing_time_ms": avg_processing_time,
                "avg_confidence_score": avg_confidence
            },
            "database_statistics": db_stats,
            "failed_files": [
                {
                    "file": r.error_message.split(": ")[-1] if r.error_message else "unknown",
                    "error": r.error_message,
                    "status": r.status.value
                }
                for r in self.processing_results if not r.success
            ]
        }
        
        return summary
    
    def output_json_results(self, results: List[ProcessingResult], input_path: Path) -> None:
        """Output results as JSON for webapp consumption"""
        import json
        
        if not results:
            output = {
                "success": False,
                "error": "No results to output",
                "file_name": input_path.name,
                "file_path": str(input_path)
            }
            print(json.dumps(output))
            return
        
        # Get the first (and typically only) result for single file processing
        result = results[0]
            
        # Extract product ranges from validation result
        extracted_ranges = []
        if result.validation_result and result.validation_result.product_ranges:
            extracted_ranges = result.validation_result.product_ranges
        
        # Build JSON output compatible with frontend expectations
        output = {
                "success": result.success,
                "error": result.error_message if not result.success else None,
            "file_name": input_path.name,
            "file_path": str(input_path),
            "processing_time_ms": result.processing_time_ms,
            "extracted_ranges": extracted_ranges,
            "valid_ranges": extracted_ranges,  # Same as extracted for now
                "invalid_ranges": [],
                "obsolete_products": [],
                "replacement_products": [],
                "obsolete_count": 0,
                "replacement_count": 0,
                "extraction_method": "production_pipeline",
            "extraction_confidence": result.confidence_score,
                "search_strategy": "xai_grok_processing",
                "search_space_reduction": 0,
            "json_outputs_saved": True,
            "json_outputs_location": f"data/output/json_outputs/{input_path.stem}_{result.document_id}/latest/"
        }
        
        # Add grok metadata if available
        if hasattr(result, 'grok_metadata') and result.grok_metadata:
            output["grok_metadata"] = result.grok_metadata
        
        # Print JSON to stdout for API to capture
        print(json.dumps(output))


def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(
        description="Production Pipeline Runner - Process documents with full validation and logging"
    )
    
    parser.add_argument(
        "input",
        help="Input file or directory path"
    )
    
    parser.add_argument(
        "--db-path",
        default="data/letters.duckdb",
        help="Database path (default: data/letters.duckdb)"
    )
    
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Process directories recursively"
    )
    
    parser.add_argument(
        "--file-list",
        action="store_true",
        help="Treat input as a text file containing list of files to process"
    )
    
    parser.add_argument(
        "--force-reprocess",
        action="store_true",
        help="Force reprocess even if document already exists"
    )
    
    parser.add_argument(
        "--json-output",
        action="store_true",
        help="Output results as JSON for webapp consumption"
    )
    
    args = parser.parse_args()
    
    # Initialize runner
    runner = ProductionPipelineRunner(db_path=args.db_path)
    
    input_path = Path(args.input)
    
    try:
        if args.file_list:
            # Process file list
            if not input_path.exists():
                logger.error(f"❌ File list not found: {input_path}")
                sys.exit(1)
            
            with open(input_path, 'r') as f:
                file_paths = [Path(line.strip()) for line in f if line.strip()]
            
            logger.info(f"📋 Processing {len(file_paths)} files from list")
            results = runner.process_file_list(file_paths)
            
        elif input_path.is_file():
            # Process single file
            logger.info(f"📄 Processing single file: {input_path}")
            result = runner.process_single_document(input_path, force_reprocess=args.force_reprocess)
            results = [result]
            
        elif input_path.is_dir():
            # Process directory
            logger.info(f"📁 Processing directory: {input_path}")
            results = runner.process_directory(input_path, recursive=args.recursive)
            
        else:
            logger.error(f"❌ Invalid input path: {input_path}")
            sys.exit(1)
        
        # Handle output format
        if args.json_output:
            # Output JSON for webapp consumption
            runner.output_json_results(results, input_path)
        else:
            # Print summary for CLI usage
            summary = runner.generate_summary_report()
            logger.info("📊 Processing Summary:")
            logger.info(f"✅ Successful: {summary.get('successful_count', 0)}")
            logger.info(f"❌ Failed: {summary.get('failed_count', 0)}")
        
        # Exit with appropriate code
        failed_count = sum(1 for r in results if not r.success)
        if failed_count > 0:
            if not args.json_output:
                logger.warning(f"⚠️ {failed_count} files failed processing")
            sys.exit(1)
        else:
            if not args.json_output:
                logger.success("🎉 All files processed successfully")
            sys.exit(0)
            
    except KeyboardInterrupt:
        logger.warning("⚠️ Processing interrupted by user")
        if 'runner' in locals():
            summary = runner.generate_summary_report()
            logger.info(f"📊 Processed: {summary.get('successful_count', 0)}")
        sys.exit(130)
        
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        if 'results' in locals() and 'runner' in locals():
            summary = runner.generate_summary_report()
            logger.info(f"📊 Processed: {summary.get('successful_count', 0)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 