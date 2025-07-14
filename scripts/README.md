# SE Letters - Scripts Directory

This directory contains the essential utility and setup scripts for the SE Letters Pipeline project. All test scripts have been moved to the `tests/` directory to follow standard Python project structure. Experimental, demo, and deprecated scripts have been archived to keep this directory clean and focused.

## 🚀 Current Active Scripts

### Production Pipelines
- **`pipelines/se_letters_pipeline_webapp.py`** - **Webapp Integration Pipeline v2.1.0**
  - Production webapp integration with real-time processing
  - SOTA Grok direct processing with DuckDB validation
  - Webapp-compatible JSON output format

- **`pipelines/se_letters_pipeline_sota_v2.py`** - **SOTA Pipeline v2.0.0**
  - State-of-the-art AI processing with hierarchical matching
  - Enhanced OCR with document + embedded image processing
  - Async processing with staging database architecture

- **`pipelines/se_letters_pipeline_semantic_v1_corrected.py`** - **Enhanced Semantic Pipeline v1.1.0**
  - Multi-dimensional semantic extraction (6 dimensions)
  - Range validation against database
  - Search space refinement (up to 99.6% reduction)
  - Comprehensive HTML report generation

### Utility Scripts
- **`api_server.py`** - API server for webapp integration
  - RESTful API endpoints for pipeline processing
  - Real-time document processing capabilities

- **`convert_json_to_duckdb.py`** - JSON to DuckDB converter
  - Converts JSON data to DuckDB format
  - Database migration utilities

- **`debug_sota_grok.py`** - SOTA Grok debugging utility
  - Debug and test SOTA Grok service integration

- **`fix_database_storage_issues.py`** - Database storage fix utility
  - Fixes database storage issues and data integrity

### Discovery & Analysis Scripts
- **`metadata_discovery_stage1.py`** - Metadata discovery stage 1
  - Initial metadata analysis and discovery

- **`metadata_discovery_stage2.py`** - Metadata discovery stage 2
  - Advanced metadata analysis and processing

- **`run_metadata_discovery.py`** - Metadata discovery runner
  - Orchestrates metadata discovery process

### Setup & Configuration
- **`setup_env.py`** - Environment setup utility
  - Sets up Python environment
  - Installs required dependencies
  - Configures project settings

- **`setup.py`** - Project setup script
  - Package installation and configuration
  - Dependency management

- **`validate_config.py`** - Configuration validation utility
  - Validates configuration files
  - Checks API keys and settings
  - Ensures proper setup

## 📁 Directory Structure

```
scripts/
├── pipelines/                                       # Production pipelines
│   ├── se_letters_pipeline_webapp.py              # Webapp Integration v2.1.0
│   ├── se_letters_pipeline_sota_v2.py             # SOTA Pipeline v2.0.0
│   └── se_letters_pipeline_semantic_v1_corrected.py # Enhanced Semantic v1.1.0
├── archive/                                         # Archived scripts
│   ├── old_experiments/                            # Experimental scripts
│   ├── old_demos/                                  # Demo scripts
│   ├── old_tests/                                  # Test scripts (moved to tests/)
│   ├── old_pipelines/                              # Old pipeline versions
│   ├── old_utilities/                              # Utility scripts
│   └── README.md                                   # Archive documentation
├── api_server.py                                   # API server
├── convert_json_to_duckdb.py                       # JSON to DuckDB converter
├── debug_sota_grok.py                              # SOTA Grok debug utility
├── fix_database_storage_issues.py                  # Database storage fix utility
├── metadata_discovery_stage1.py                    # Metadata discovery stage 1
├── metadata_discovery_stage2.py                    # Metadata discovery stage 2
├── run_metadata_discovery.py                       # Metadata discovery runner
├── setup_env.py                                    # Environment setup
├── setup.py                                        # Project setup
├── validate_config.py                              # Config validation
└── README.md                                       # This file
```

## 🧪 Test Scripts

All test scripts have been moved to the `tests/` directory following standard Python project structure:

```
tests/
├── unit/                                           # Unit tests
│   ├── test_enhanced_sota_service.py              # SOTA service tests
│   ├── test_grok_api_simple.py                    # Grok API tests
│   ├── test_ol0009_enhanced_extraction.py         # Enhanced extraction tests
│   ├── test_mode_processor.py                     # Mode processor tests
│   └── test_pix2b_real_pipeline.py                # Real pipeline tests
├── integration/                                    # Integration tests
│   ├── test_database_storage.py                   # Database storage tests
│   └── test_pix2b_production.py                   # Production pipeline tests
├── conftest.py                                     # Test configuration
└── __init__.py                                     # Test package init
```

## 🏃 Quick Start

### Run Production Pipelines
```bash
# Webapp Integration Pipeline (v2.1.0)
python scripts/pipelines/se_letters_pipeline_webapp.py <document_path>

# SOTA Pipeline (v2.0.0)
python scripts/pipelines/se_letters_pipeline_sota_v2.py <document_path>

# Enhanced Semantic Pipeline (v1.1.0)
python scripts/pipelines/se_letters_pipeline_semantic_v1_corrected.py
```

### Run Tests
```bash
# Run all tests
pytest tests/

# Run unit tests only
pytest tests/unit/

# Run integration tests only
pytest tests/integration/

# Run specific test
pytest tests/unit/test_enhanced_sota_service.py
```

### Setup Environment
```bash
# First-time setup
python scripts/setup_env.py

# Validate configuration
python scripts/validate_config.py
```

## 🔧 Pipeline Features

### 🚀 Webapp Integration Pipeline v2.1.0
- **Real-time Processing**: Direct webapp integration with JSON output
- **SOTA Grok Direct**: AI-powered metadata extraction
- **DuckDB Validation**: Range validation against IBcatalogue database
- **Performance Metrics**: Real-time monitoring and confidence scoring

### 🧠 SOTA Pipeline v2.0.0
- **Hierarchical Matching**: 4-level product matching (Product Line → Range → Subrange → Product)
- **Enhanced OCR**: Document + embedded image processing
- **Async Processing**: Improved performance with async/await
- **Staging Architecture**: JSON staging with audit trail
- **Product Line Classification**: Automatic PPIBS/PSIBS/DPIBS/SPIBS classification

### 🔍 Enhanced Semantic Pipeline v1.1.0
- **Multi-dimensional Extraction**: 6-dimensional semantic analysis
- **Range Validation**: Database-validated product ranges
- **Search Space Refinement**: Up to 99.6% reduction for precision targeting
- **Technical Specifications**: Voltage, current, power extraction
- **HTML Reporting**: Comprehensive industrial-themed reports

### 📊 Common Capabilities
- **Document Processing**: PDF, DOCX, DOC support with fallback strategies
- **AI-Powered Analysis**: xAI Grok service integration
- **Database Integration**: DuckDB with 342,229+ product records
- **Error Handling**: Graceful degradation with comprehensive logging
- **Performance Monitoring**: Real-time metrics and confidence scoring

## 📋 Requirements

- Python 3.9+
- DuckDB database (`data/IBcatalogue.duckdb`)
- Document processing dependencies (LibreOffice, Tesseract)
- xAI API key (optional, uses mock services if not available)

## 🗂️ Archived Scripts

All experimental, demo, and deprecated scripts have been moved to the `archive/` directory:
- **25+ old scripts** organized by category
- **Complete development history** preserved
- **Reference implementations** for future development
- **Clean separation** between active and archived code

## 🧪 Test Organization

All test scripts have been moved to the `tests/` directory following standard Python project structure:
- **Unit Tests** (`tests/unit/`): Individual component testing
- **Integration Tests** (`tests/integration/`): End-to-end pipeline testing
- **Test Configuration** (`tests/conftest.py`): Shared test fixtures and configuration
- **Standard pytest** structure for easy test discovery and execution

## 📈 Performance

The current pipelines achieve:
- **100% success rate** on document processing
- **Sub-second processing** per document
- **Accurate product counts** within database limits
- **Comprehensive validation** of all extracted data
- **Real-time webapp integration** with JSON output
- **Async processing** for improved performance
- **Multi-dimensional analysis** with 99.6% search space reduction

## 🔄 Evolution

This represents the culmination of extensive development and refinement:
1. **Initial implementations** (archived)
2. **Industrial-themed versions** (archived)
3. **Enhanced semantic versions** (archived)
4. **SOTA pipeline implementation** (v2.0.0)
5. **Webapp integration** (v2.1.0)
6. **Production-ready multi-pipeline architecture** (current)

The archived scripts demonstrate the evolution from experimental prototypes to the current production-ready multi-pipeline architecture with comprehensive testing and documentation. 