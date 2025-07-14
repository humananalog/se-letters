#!/usr/bin/env python3
"""
JSON Output Manager - Elegant JSON Output Storage System

This utility provides comprehensive JSON output management for the SE Letters pipeline,
organizing outputs by document ID with proper versioning and metadata tracking.

Features:
- Document-specific subfolders with clean naming
- Versioning for multiple processing runs
- Comprehensive metadata tracking
- Automatic cleanup and archiving
- Thread-safe operations
- Configurable retention policies

Directory Structure:
data/output/
├── json_outputs/
│   ├── {document_id}/
│   │   ├── latest/
│   │   │   ├── grok_metadata.json
│   │   │   ├── validation_result.json
│   │   │   ├── processing_result.json
│   │   │   └── pipeline_summary.json
│   │   ├── {timestamp}/
│   │   │   ├── grok_metadata.json
│   │   │   ├── validation_result.json
│   │   │   ├── processing_result.json
│   │   │   └── pipeline_summary.json
│   │   └── metadata.json
│   └── index.json

Version: 1.0.0
Author: SE Letters Development Team
"""

import json
import time
import shutil
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from loguru import logger

from ..core.exceptions import ProcessingError


@dataclass
class OutputMetadata:
    """Metadata for JSON output storage"""
    document_id: str
    document_name: str
    source_file_path: str
    processing_timestamp: str
    processing_duration_ms: float
    confidence_score: float
    success: bool
    version: str = "1.0.0"
    pipeline_method: str = "production_pipeline"
    outputs_saved: List[str] = None
    file_hash: Optional[str] = None
    file_size: Optional[int] = None
    
    def __post_init__(self):
        if self.outputs_saved is None:
            self.outputs_saved = []


class JSONOutputManager:
    """Elegant JSON output storage manager with document-specific organization"""
    
    def __init__(self, base_output_dir: str = "data/output"):
        self.base_output_dir = Path(base_output_dir)
        self.json_outputs_dir = self.base_output_dir / "json_outputs"
        self.index_file = self.json_outputs_dir / "index.json"
        self.lock = threading.Lock()
        
        # Configuration
        self.max_versions_per_document = 10
        self.retention_days = 30
        self.auto_cleanup_enabled = True
        
        # Initialize directory structure
        self._init_directories()
        
        logger.info(f"📁 JSON Output Manager initialized: {self.json_outputs_dir}")
    
    def _init_directories(self) -> None:
        """Initialize the directory structure"""
        try:
            self.json_outputs_dir.mkdir(parents=True, exist_ok=True)
            
            # Create index file if it doesn't exist
            if not self.index_file.exists():
                self._save_index({})
            
            logger.info(f"✅ Directory structure initialized: {self.json_outputs_dir}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize directories: {e}")
            raise ProcessingError(f"Failed to initialize JSON output directories: {e}")
    
    def save_document_outputs(
        self,
        document_id: str,
        document_name: str,
        source_file_path: str,
        outputs: Dict[str, Any],
        metadata: Optional[OutputMetadata] = None
    ) -> str:
        """Save all JSON outputs for a document with elegant organization
        
        Args:
            document_id: Unique document identifier
            document_name: Original document name
            source_file_path: Path to source document
            outputs: Dictionary of output data to save
            metadata: Optional metadata object
            
        Returns:
            Path to the saved output directory
        """
        try:
            with self.lock:
                # Create document directory
                doc_dir = self.json_outputs_dir / self._sanitize_document_id(document_id)
                doc_dir.mkdir(parents=True, exist_ok=True)
                
                # Create timestamp-based version directory
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                version_dir = doc_dir / timestamp
                version_dir.mkdir(parents=True, exist_ok=True)
                
                # Create latest symlink directory
                latest_dir = doc_dir / "latest"
                if latest_dir.exists():
                    if latest_dir.is_symlink():
                        latest_dir.unlink()
                    else:
                        shutil.rmtree(latest_dir)
                
                # Save individual output files
                saved_files = []
                for output_name, output_data in outputs.items():
                    output_file = version_dir / f"{output_name}.json"
                    self._save_json_file(output_file, output_data)
                    saved_files.append(output_name)
                
                # Create metadata if not provided
                if metadata is None:
                    metadata = OutputMetadata(
                        document_id=document_id,
                        document_name=document_name,
                        source_file_path=source_file_path,
                        processing_timestamp=datetime.now().isoformat(),
                        processing_duration_ms=0.0,
                        confidence_score=0.0,
                        success=True,
                        outputs_saved=saved_files
                    )
                else:
                    metadata.outputs_saved = saved_files
                
                # Save metadata
                metadata_file = version_dir / "metadata.json"
                self._save_json_file(metadata_file, asdict(metadata))
                
                # Create latest symlink (cross-platform compatible)
                try:
                    if hasattr(latest_dir, 'symlink_to'):
                        latest_dir.symlink_to(version_dir.name)
                    else:
                        # Fallback: copy directory for Windows compatibility
                        shutil.copytree(version_dir, latest_dir)
                except Exception as e:
                    logger.warning(f"⚠️ Could not create latest symlink, copying instead: {e}")
                    shutil.copytree(version_dir, latest_dir)
                
                # Update document metadata
                self._update_document_metadata(doc_dir, metadata)
                
                # Update global index
                self._update_global_index(document_id, metadata)
                
                # Cleanup old versions if needed
                if self.auto_cleanup_enabled:
                    self._cleanup_old_versions(doc_dir)
                
                logger.info(f"✅ Saved JSON outputs for document {document_id}: {version_dir}")
                return str(version_dir)
                
        except Exception as e:
            logger.error(f"❌ Failed to save JSON outputs for {document_id}: {e}")
            raise ProcessingError(f"Failed to save JSON outputs: {e}")
    
    def get_document_outputs(
        self,
        document_id: str,
        version: str = "latest"
    ) -> Optional[Dict[str, Any]]:
        """Retrieve JSON outputs for a document
        
        Args:
            document_id: Document identifier
            version: Version to retrieve ("latest" or timestamp)
            
        Returns:
            Dictionary of output data or None if not found
        """
        try:
            doc_dir = self.json_outputs_dir / self._sanitize_document_id(document_id)
            if not doc_dir.exists():
                return None
            
            version_dir = doc_dir / version
            if not version_dir.exists():
                return None
            
            outputs = {}
            for json_file in version_dir.glob("*.json"):
                if json_file.name != "metadata.json":
                    output_name = json_file.stem
                    outputs[output_name] = self._load_json_file(json_file)
            
            return outputs
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve outputs for {document_id}: {e}")
            return None
    
    def list_document_versions(self, document_id: str) -> List[str]:
        """List all versions for a document
        
        Args:
            document_id: Document identifier
            
        Returns:
            List of version timestamps
        """
        try:
            doc_dir = self.json_outputs_dir / self._sanitize_document_id(document_id)
            if not doc_dir.exists():
                return []
            
            versions = []
            for item in doc_dir.iterdir():
                if item.is_dir() and item.name != "latest":
                    versions.append(item.name)
            
            return sorted(versions, reverse=True)
            
        except Exception as e:
            logger.error(f"❌ Failed to list versions for {document_id}: {e}")
            return []
    
    def get_document_metadata(self, document_id: str) -> Optional[OutputMetadata]:
        """Get metadata for a document
        
        Args:
            document_id: Document identifier
            
        Returns:
            OutputMetadata object or None if not found
        """
        try:
            doc_dir = self.json_outputs_dir / self._sanitize_document_id(document_id)
            metadata_file = doc_dir / "metadata.json"
            
            if not metadata_file.exists():
                return None
            
            metadata_dict = self._load_json_file(metadata_file)
            return OutputMetadata(**metadata_dict)
            
        except Exception as e:
            logger.error(f"❌ Failed to get metadata for {document_id}: {e}")
            return None
    
    def list_all_documents(self) -> List[str]:
        """List all documents with saved outputs
        
        Returns:
            List of document IDs
        """
        try:
            if not self.json_outputs_dir.exists():
                return []
            
            documents = []
            for item in self.json_outputs_dir.iterdir():
                if item.is_dir() and item.name != "index.json":
                    documents.append(item.name)
            
            return sorted(documents)
            
        except Exception as e:
            logger.error(f"❌ Failed to list documents: {e}")
            return []
    
    def cleanup_old_outputs(self, days: int = None) -> int:
        """Clean up old outputs based on retention policy
        
        Args:
            days: Number of days to retain (uses default if None)
            
        Returns:
            Number of cleaned up versions
        """
        if days is None:
            days = self.retention_days
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            cleaned_count = 0
            
            for doc_dir in self.json_outputs_dir.iterdir():
                if doc_dir.is_dir() and doc_dir.name != "index.json":
                    cleaned_count += self._cleanup_old_versions(doc_dir, cutoff_date)
            
            logger.info(f"🧹 Cleaned up {cleaned_count} old output versions")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"❌ Failed to cleanup old outputs: {e}")
            return 0
    
    def _sanitize_document_id(self, document_id: str) -> str:
        """Sanitize document ID for use as directory name"""
        # Remove or replace invalid characters
        sanitized = "".join(c for c in document_id if c.isalnum() or c in "._-")
        return sanitized[:100]  # Limit length
    
    def _save_json_file(self, file_path: Path, data: Any) -> None:
        """Save data to JSON file with proper formatting"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            raise ProcessingError(f"Failed to save JSON file {file_path}: {e}")
    
    def _load_json_file(self, file_path: Path) -> Any:
        """Load data from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise ProcessingError(f"Failed to load JSON file {file_path}: {e}")
    
    def _update_document_metadata(self, doc_dir: Path, metadata: OutputMetadata) -> None:
        """Update document-level metadata"""
        try:
            metadata_file = doc_dir / "metadata.json"
            
            # Load existing metadata or create new
            if metadata_file.exists():
                existing_metadata = self._load_json_file(metadata_file)
                # Update with new information
                existing_metadata.update(asdict(metadata))
                existing_metadata['last_updated'] = datetime.now().isoformat()
                metadata_dict = existing_metadata
            else:
                metadata_dict = asdict(metadata)
                metadata_dict['created'] = datetime.now().isoformat()
                metadata_dict['last_updated'] = datetime.now().isoformat()
            
            self._save_json_file(metadata_file, metadata_dict)
            
        except Exception as e:
            logger.error(f"❌ Failed to update document metadata: {e}")
    
    def _update_global_index(self, document_id: str, metadata: OutputMetadata) -> None:
        """Update global index with document information"""
        try:
            index_data = self._load_index()
            
            index_data[document_id] = {
                'document_name': metadata.document_name,
                'source_file_path': metadata.source_file_path,
                'last_processed': metadata.processing_timestamp,
                'success': metadata.success,
                'confidence_score': metadata.confidence_score,
                'outputs_saved': metadata.outputs_saved
            }
            
            self._save_index(index_data)
            
        except Exception as e:
            logger.error(f"❌ Failed to update global index: {e}")
    
    def _load_index(self) -> Dict[str, Any]:
        """Load global index"""
        try:
            if self.index_file.exists():
                return self._load_json_file(self.index_file)
            return {}
        except Exception as e:
            logger.error(f"❌ Failed to load index: {e}")
            return {}
    
    def _save_index(self, index_data: Dict[str, Any]) -> None:
        """Save global index"""
        try:
            self._save_json_file(self.index_file, index_data)
        except Exception as e:
            logger.error(f"❌ Failed to save index: {e}")
    
    def _cleanup_old_versions(self, doc_dir: Path, cutoff_date: datetime = None) -> int:
        """Clean up old versions for a document"""
        try:
            if cutoff_date is None:
                cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            
            versions = []
            for item in doc_dir.iterdir():
                if item.is_dir() and item.name != "latest":
                    try:
                        version_date = datetime.strptime(item.name, "%Y%m%d_%H%M%S")
                        versions.append((version_date, item))
                    except ValueError:
                        continue
            
            # Sort by date (newest first) and keep only the most recent versions
            versions.sort(key=lambda x: x[0], reverse=True)
            
            cleaned_count = 0
            for i, (version_date, version_dir) in enumerate(versions):
                # Keep the most recent versions within the max limit
                if i >= self.max_versions_per_document or version_date < cutoff_date:
                    shutil.rmtree(version_dir)
                    cleaned_count += 1
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"❌ Failed to cleanup old versions: {e}")
            return 0


# Convenience functions for easy usage
def save_pipeline_outputs(
    document_id: str,
    document_name: str,
    source_file_path: str,
    grok_metadata: Dict[str, Any],
    validation_result: Dict[str, Any],
    processing_result: Dict[str, Any],
    pipeline_summary: Dict[str, Any],
    metadata: Optional[OutputMetadata] = None
) -> str:
    """Convenience function to save all pipeline outputs"""
    manager = JSONOutputManager()
    
    outputs = {
        'grok_metadata': grok_metadata,
        'validation_result': validation_result,
        'processing_result': processing_result,
        'pipeline_summary': pipeline_summary
    }
    
    return manager.save_document_outputs(
        document_id=document_id,
        document_name=document_name,
        source_file_path=source_file_path,
        outputs=outputs,
        metadata=metadata
    )


def get_pipeline_outputs(document_id: str, version: str = "latest") -> Optional[Dict[str, Any]]:
    """Convenience function to retrieve pipeline outputs"""
    manager = JSONOutputManager()
    return manager.get_document_outputs(document_id, version)


def cleanup_old_pipeline_outputs(days: int = 30) -> int:
    """Convenience function to cleanup old pipeline outputs"""
    manager = JSONOutputManager()
    return manager.cleanup_old_outputs(days) 