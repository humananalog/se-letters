# Readme

**Version: 2.2.0**  
**Author: Alexandre Huther**  
**Date: 2025-07-16**


**Version: 2.2.0
**Author: Alexandre Huther
**Date: 2025-07-16**


This directory contains services that have been archived from the production environment to maintain a clean and focused codebase.

## Archive Structure

### `experimental/`
Contains experimental and development services that were created during research and development phases but are not used in the production pipeline.

## Archived Services

### Experimental Services (`experimental/`)

1. **`enhanced_document_processor.py`** - Enhanced document processing with PL_SERVICES intelligence
2. **`enhanced_vector_search_engine.py`** - Hierarchical vector search with PPIBS gap analysis
3. **`semantic_extraction_engine.py`** - Semantic extraction with embeddings from DuckDB
4. **`product_modernization_engine.py`** - Product modernization and lifecycle tracking
5. **`advanced_preview_service.py`** - Advanced document preview with annotation overlay
6. **`document_metadata_service.py`** - Document metadata management in DuckDB
7. **`sota_grok_service.py`** - SOTA Grok service with unified schema
8. **`raw_file_grok_service.py`** - Raw file processing without OCR preprocessing
9. **`enhanced_image_processor.py`** - Enhanced image processing for embedded images
10. **`enhanced_duckdb_service.py`** - Enhanced DuckDB service with advanced features
11. **`enhanced_semantic_extraction_engine.py`** - Enhanced semantic extraction engine
12. **`robust_document_processor.py`** - Robust document processor with fallback mechanisms

## Production Services (Remaining)

The following services remain in the production environment:

1. **`production_pipeline_service.py`** - Core production pipeline service
2. **`document_processor.py`** - Standard document processing
3. **`xai_service.py`** - XAI API integration
4. **`excel_service.py`** - Excel/DuckDB data operations
5. **`embedding_service.py`** - Vector embeddings and similarity search
6. **`preview_service.py`** - Document preview generation

## Restoration Process

If any archived service needs to be restored to production:

1. Move the service file back to `src/se_letters/services/`
2. Update `src/se_letters/services/__init__.py` to include the service
3. Update any import statements in dependent modules
4. Run tests to ensure compatibility
5. Update documentation

## Archive Date

Services archived on: 2025-01-27

## Reason for Archival

These services were archived to:
- Maintain a clean production environment
- Reduce DevOps complexity
- Focus on core production functionality
- Prevent interference with production deployments
- Improve maintainability and clarity

## Contact

For questions about archived services, contact the SE Letters development team. 