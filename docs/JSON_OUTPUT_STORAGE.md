# Json Output Storage

**Version: 2.2.0**  
**Author: Alexandre Huther**  
**Date: 2025-07-16**


**Version: 2.2.0
**Author: Alexandre Huther
**Date: 2025-07-16**


**Version: 2.2.0
**Component: JSON Output Manager**

## 📋 Overview

The JSON Output Storage System provides elegant, organized storage of all pipeline processing results with document-specific subfolders, versioning, and comprehensive metadata tracking. Every document processed through the production pipeline automatically saves complete JSON outputs for audit trails, debugging, and analysis.

### Key Features
- **Document-Specific Organization**: Each document gets its own subfolder with clean naming
- **Automatic Versioning**: Multiple processing runs create timestamped versions
- **Comprehensive Metadata**: Complete processing details and statistics
- **Thread-Safe Operations**: Concurrent processing support
- **Configurable Retention**: Automatic cleanup of old versions
- **Cross-Platform Compatibility**: Works on Windows, macOS, and Linux
- **Rich CLI Tools**: Command-line utilities for management

## 🏗️ Directory Structure

```
data/output/
├── json_outputs/
│   ├── {document_id}/
│   │   ├── latest/                    # Symlink to most recent version
│   │   │   ├── grok_metadata.json
│   │   │   ├── validation_result.json
│   │   │   ├── processing_result.json
│   │   │   ├── pipeline_summary.json
│   │   │   └── metadata.json
│   │   ├── 20250127_143022/           # Timestamped version
│   │   │   ├── grok_metadata.json
│   │   │   ├── validation_result.json
│   │   │   ├── processing_result.json
│   │   │   ├── pipeline_summary.json
│   │   │   └── metadata.json
│   │   ├── 20250127_142015/           # Previous version
│   │   │   └── ...
│   │   └── metadata.json              # Document-level metadata
│   ├── PIX2B_Phase_out_Letter_10/     # Example document
│   ├── SEPAM2040_PWP_Notice_11/       # Example document
│   └── index.json                     # Global index
```

### Document ID Format
- **Pattern**: `{filename_without_extension}_{database_id}`
- **Examples**: 
  - `PIX2B_Phase_out_Letter_10`
  - `SEPAM2040_PWP_Notice_11`
  - `Galaxy_6000_End_of_Life_12`

## 📄 JSON Output Files

### 1. `grok_metadata.json`
Complete Grok extraction results with structured product information:

```json
{
  "document_information": {
    "document_type": "obsolescence_letter",
    "document_title": "PIX2B Phase Out Letter",
    "language": "English",
    "document_date": "2024-01-15"
  },
  "products": [
    {
      "product_identifier": "PIX2B-24",
      "range_label": "PIX2B",
      "subrange_label": "PIX Double Bus Bar",
      "product_line": "DPIBS",
      "product_description": "PIX Double Bus Bar Protection System",
      "obsolescence_status": "End of Life",
      "end_of_service_date": "2024-12-31",
      "replacement_suggestions": "Use PIX3B series"
    }
  ],
  "technical_specifications": {
    "voltage_levels": ["24V", "48V"],
    "current_ratings": ["10A", "20A"],
    "power_ratings": ["240W", "480W"],
    "frequencies": ["50Hz", "60Hz"]
  },
  "business_information": {
    "customer_impact": "High - affects multiple installations",
    "migration_timeline": "6 months",
    "support_contacts": "support@schneider-electric.com"
  },
  "extraction_metadata": {
    "confidence_score": 0.95,
    "processing_method": "grok_production",
    "extraction_timestamp": "2025-01-27T14:30:22Z"
  }
}
```

### 2. `validation_result.json`
Content compliance validation results:

```json
{
  "is_compliant": true,
  "confidence_score": 0.95,
  "product_ranges": ["PIX2B", "PIX"],
  "technical_specs": {
    "voltage_levels": ["24V", "48V"],
    "current_ratings": ["10A", "20A"]
  },
  "validation_errors": [],
  "extracted_metadata": {
    "document_type": "obsolescence_letter",
    "language": "English",
    "page_count": 3
  }
}
```

### 3. `processing_result.json`
Complete processing execution details:

```json
{
  "success": true,
  "document_id": 10,
  "processing_time_ms": 12600.5,
  "confidence_score": 0.95,
  "status": "completed",
  "file_hash": "sha256:abc123...",
  "file_size": 245760,
  "processed_at": 1706361022.5
}
```

### 4. `pipeline_summary.json`
Pipeline execution summary and configuration:

```json
{
  "pipeline_version": "2.2.0",
  "processing_method": "production_pipeline",
  "xai_model": "grok-3-latest",
  "document_processor": "DocumentProcessor",
  "database_path": "data/letters.duckdb",
  "ingestion_details": {
    "document_id": 10,
    "products_inserted": 5,
    "file_hash": "sha256:abc123..."
  },
  "products_extracted": 5,
  "technical_specs_found": true,
  "validation_errors": []
}
```

### 5. `metadata.json`
Document-level metadata and processing history:

```json
{
  "document_id": "PIX2B_Phase_out_Letter_10",
  "document_name": "PIX2B_Phase_out_Letter.pdf",
  "source_file_path": "/path/to/PIX2B_Phase_out_Letter.pdf",
  "processing_timestamp": "2025-01-27T14:30:22Z",
  "processing_duration_ms": 12600.5,
  "confidence_score": 0.95,
  "success": true,
  "version": "1.0.0",
  "pipeline_method": "production_pipeline",
  "outputs_saved": ["grok_metadata", "validation_result", "processing_result", "pipeline_summary"],
  "file_hash": "sha256:abc123...",
  "file_size": 245760,
  "created": "2025-01-27T14:30:22Z",
  "last_updated": "2025-01-27T14:30:22Z"
}
```

## 🔧 Configuration

### Default Settings
```python
# JSONOutputManager configuration
max_versions_per_document = 10    # Keep 10 most recent versions
retention_days = 30               # Delete versions older than 30 days
auto_cleanup_enabled = True       # Automatic cleanup on save
base_output_dir = "data/output"   # Base directory for outputs
```

### Customization
```python
from se_letters.utils.json_output_manager import JSONOutputManager

# Custom configuration
manager = JSONOutputManager(base_output_dir="custom/output/path")
manager.max_versions_per_document = 5
manager.retention_days = 14
manager.auto_cleanup_enabled = False
```

## 🚀 Usage Examples

### Automatic Integration (Production Pipeline)
The JSON output storage is automatically integrated into the production pipeline:

```python
from se_letters.services.production_pipeline_service import ProductionPipelineService

# Initialize service (JSON output manager is automatically created)
pipeline = ProductionPipelineService()

# Process document (JSON outputs are automatically saved)
result = pipeline.process_document(Path("document.pdf"))

# JSON outputs are saved to:
# data/output/json_outputs/document_<id>/latest/
```

### Manual Usage
```python
from se_letters.utils.json_output_manager import JSONOutputManager, OutputMetadata

# Initialize manager
manager = JSONOutputManager()

# Prepare outputs
outputs = {
    'grok_metadata': grok_data,
    'validation_result': validation_data,
    'processing_result': processing_data,
    'pipeline_summary': summary_data
}

# Save outputs
output_dir = manager.save_document_outputs(
    document_id="my_document_123",
    document_name="my_document.pdf",
    source_file_path="/path/to/my_document.pdf",
    outputs=outputs
)

print(f"Outputs saved to: {output_dir}")
```

### Retrieving Outputs
```python
# Get latest outputs
outputs = manager.get_document_outputs("my_document_123")

# Get specific version
outputs = manager.get_document_outputs("my_document_123", "20250127_143022")

# Get document metadata
metadata = manager.get_document_metadata("my_document_123")

# List all versions
versions = manager.list_document_versions("my_document_123")
```

## 🛠️ Command Line Tools

### Management Utility
```bash
# List all documents with JSON outputs
python scripts/manage_json_outputs.py list

# View specific document outputs
python scripts/manage_json_outputs.py view PIX2B_Phase_out_Letter_10

# View specific version
python scripts/manage_json_outputs.py view PIX2B_Phase_out_Letter_10 --version 20250127_143022

# Clean up old outputs
python scripts/manage_json_outputs.py cleanup --days 30

# Export document outputs
python scripts/manage_json_outputs.py export PIX2B_Phase_out_Letter_10 --format json
python scripts/manage_json_outputs.py export PIX2B_Phase_out_Letter_10 --format txt --output report.txt

# Show statistics
python scripts/manage_json_outputs.py stats
```

### Example Output
```
📋 Documents with JSON outputs:
==================================================

📄 Document ID: PIX2B_Phase_out_Letter_10
   📝 Name: PIX2B_Phase_out_Letter.pdf
   📁 Source: /path/to/PIX2B_Phase_out_Letter.pdf
   ⏱️ Last processed: 2025-01-27T14:30:22Z
   🎯 Confidence: 0.95
   ✅ Success: True
   📊 Versions: 3
   📅 Latest: 20250127_143022
   📅 Oldest: 20250127_140015
```

## 🔍 Integration with Webapp

### API Endpoints
The JSON outputs are accessible through the webapp API:

```typescript
// Get document outputs
GET /api/json-outputs/{document_id}
GET /api/json-outputs/{document_id}?version=20250127_143022

// List all documents
GET /api/json-outputs

// Get output statistics
GET /api/json-outputs/stats
```

### Pipeline Response Enhancement
The production pipeline now includes JSON output information:

```json
{
  "success": true,
  "file_name": "PIX2B_Phase_out_Letter.pdf",
  "processing_time_ms": 12600.5,
  "extraction_confidence": 0.95,
  "grok_metadata": { ... },
  "json_outputs_saved": true,
  "json_outputs_location": "data/output/json_outputs/PIX2B_Phase_out_Letter_10/latest/"
}
```

## 🧹 Maintenance

### Automatic Cleanup
- **Triggered**: Every time a document is processed
- **Retention**: Configurable (default: 30 days)
- **Version Limit**: Configurable (default: 10 versions per document)
- **Thread-Safe**: Multiple processes can run cleanup simultaneously

### Manual Cleanup
```python
# Clean up all old outputs
manager.cleanup_old_outputs(days=30)

# Clean up specific document
manager._cleanup_old_versions(doc_dir, cutoff_date)
```

### Monitoring
```python
# Get statistics
stats = manager.get_processing_statistics()

# Check disk usage
import shutil
total, used, free = shutil.disk_usage(manager.json_outputs_dir)
```

## 🔒 Security Considerations

### File Permissions
- **Directory**: 755 (rwxr-xr-x)
- **JSON Files**: 644 (rw-r--r--)
- **Metadata Files**: 644 (rw-r--r--)

### Sensitive Data
- **No API Keys**: API keys are never stored in JSON outputs
- **Path Sanitization**: Document IDs are sanitized for file system safety
- **Access Control**: Outputs inherit directory permissions

### Backup Recommendations
- **Regular Backups**: Include `data/output/json_outputs/` in backup strategy
- **Version Control**: Critical outputs should be committed to version control
- **Archival**: Consider archiving old outputs to external storage

## 📊 Performance

### Benchmarks
- **Save Time**: ~50ms per document (4 JSON files)
- **Retrieval Time**: ~10ms per document
- **Disk Usage**: ~100KB per document (uncompressed)
- **Memory Usage**: ~10MB for manager instance

### Optimization Tips
- **Batch Processing**: Process multiple documents in sequence
- **Compression**: Enable compression for long-term storage
- **Indexing**: Use the global index for fast lookups
- **Cleanup**: Regular cleanup prevents disk space issues

## 🐛 Troubleshooting

### Common Issues

#### Permission Errors
```bash
# Fix directory permissions
chmod -R 755 data/output/json_outputs/

# Fix file permissions
find data/output/json_outputs/ -type f -exec chmod 644 {} \;
```

#### Disk Space Issues
```bash
# Check disk usage
du -sh data/output/json_outputs/

# Clean up old outputs
python scripts/manage_json_outputs.py cleanup --days 7
```

#### Corrupted JSON Files
```python
# Validate JSON files
import json
from pathlib import Path

def validate_json_file(file_path):
    try:
        with open(file_path, 'r') as f:
            json.load(f)
        return True
    except json.JSONDecodeError:
        return False
```

#### Missing Outputs
```python
# Check if outputs exist
outputs = manager.get_document_outputs("document_id")
if not outputs:
    print("No outputs found - document may not have been processed")
```

### Debugging
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check manager state
print(f"Base directory: {manager.base_output_dir}")
print(f"JSON outputs directory: {manager.json_outputs_dir}")
print(f"Index file: {manager.index_file}")
```

## 🔄 Migration Guide

### From Manual File Storage
```python
# Migrate existing JSON files
import shutil
from pathlib import Path

def migrate_existing_outputs():
    old_dir = Path("old_outputs")
    manager = JSONOutputManager()
    
    for json_file in old_dir.glob("*.json"):
        # Parse filename to get document info
        doc_id = json_file.stem
        
        # Load existing data
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Save through manager
        manager.save_document_outputs(
            document_id=doc_id,
            document_name=f"{doc_id}.pdf",
            source_file_path=str(json_file),
            outputs={'legacy_data': data}
        )
```

### Version Upgrades
- **Backward Compatibility**: New versions maintain compatibility with old outputs
- **Schema Evolution**: Metadata schemas can evolve without breaking existing data
- **Migration Scripts**: Provided for major version upgrades

## 📈 Future Enhancements

### Planned Features
- **Compression**: Automatic compression for long-term storage
- **Cloud Storage**: Integration with cloud storage providers
- **Search**: Full-text search across JSON outputs
- **Analytics**: Advanced analytics and reporting
- **Notifications**: Alerts for processing failures or disk space issues

### API Enhancements
- **GraphQL**: GraphQL API for flexible data querying
- **Real-time**: WebSocket support for real-time updates
- **Batch Operations**: Bulk operations for multiple documents

---

**JSON Output Storage System** - Providing elegant, organized, and comprehensive storage of all SE Letters pipeline processing results with automatic versioning, metadata tracking, and powerful management tools.

**Status**: ✅ **Production Ready** | **Version**: 1.0.0 | **Integration**: ✅ **Complete** 