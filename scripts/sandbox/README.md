# Sandbox Folder - Organized Structure

**Version: 1.0.0**  
**Last Updated: 2025-01-27**  
**Organization: Clean and Well-Structured**

## 📋 Overview

This sandbox folder contains experimental implementations, demos, and analysis tools for the SE Letters project. The folder is organized into logical categories for better maintainability and navigation.

## 📁 Folder Structure

```
sandbox/
├── services/           # Service implementations and core logic
├── demos/              # Demo scripts and testing implementations
├── analysis/           # Analysis scripts and database exploration
├── results/            # All output files (JSON, Excel, TXT)
├── docs/               # Documentation and solution plans
├── utils/              # Utility scripts and helpers
└── README.md           # This file
```

## 🔧 Services (`services/`)

Core service implementations for product matching, discovery, and mapping:

- **intelligent_product_matching_service.py** - Intelligent product matching with Grok integration
- **enhanced_dpibs_cortec_service.py** - Enhanced DPIBS/Cortec service implementation
- **enhanced_product_discovery_service.py** - Advanced product discovery service
- **product_mapping_service_v3.py** - Latest product mapping service (v3)
- **product_mapping_service_v2.py** - Product mapping service (v2)
- **product_mapping_service.py** - Original product mapping service
- **production_ready_product_service.py** - Production-ready product service
- **sota_range_mapping_service.py** - SOTA range mapping service
- **sepam_protection_relay_filter.py** - SEPAM protection relay filter service

## 🎯 Demos (`demos/`)

Demonstration scripts and testing implementations:

- **integrated_intelligent_discovery_demo.py** - Complete intelligent discovery demo
- **pix_discovery_simplified.py** - Simplified PIX discovery demo
- **comprehensive_range_demo.py** - Comprehensive range mapping demo
- **deep_correlation_demo.py** - Deep correlation analysis demo
- **comprehensive_mapping_demo.py** - Comprehensive mapping demo

## 📊 Analysis (`analysis/`)

Analysis scripts and database exploration tools:

- **pix_database_analysis.py** - PIX database analysis and exploration
- **explore_switchgear_families.py** - Switchgear families exploration
- **explore_databases.py** - General database exploration utilities

## 📈 Results (`results/`)

All output files from experiments and analysis:

### JSON Results
- **intelligent_matching_results.json** - Intelligent matching results
- **integrated_intelligent_discovery_results.json** - Discovery results
- **pix_discovery_results_*.json** - PIX discovery results (timestamped)
- **pix2b_enhanced_discovery_*.json** - PIX2B enhanced discovery results
- **sepam_intelligence_results_*.json** - SEPAM intelligence results
- **sota_deep_mapping_*.json** - SOTA deep mapping results (timestamped)
- **sepam_2040_mapping_*.json** - SEPAM 2040 mapping results
- **galaxy_6000_mapping_*.json** - Galaxy 6000 mapping results
- **enhanced_mapping_result_*.json** - Enhanced mapping results
- **mapping_result_*.json** - General mapping results

### Excel Results
- **pix_database_analysis_*.xlsx** - PIX database analysis results
- **psibs_power_systems_*.xlsx** - PSIBS power systems analysis
- **sepam_2040_candidates_*.xlsx** - SEPAM 2040 candidates analysis
- **galaxy_6000_candidates_*.xlsx** - Galaxy 6000 candidates analysis

### Text Results
- **psibs_power_systems_*_summary.txt** - PSIBS power systems summary
- **sepam_2040_summary_*.txt** - SEPAM 2040 summary
- **galaxy_6000_summary_*.txt** - Galaxy 6000 summary

## 📖 Documentation (`docs/`)

Solution plans and documentation:

- **pix_discovery_summary.md** - PIX discovery summary and findings
- **SOTA_RANGE_MAPPING_SOLUTION.md** - SOTA range mapping solution plan
- **PRODUCT_MAPPING_SOLUTION_PLAN.md** - Product mapping solution plan

## 🛠️ Utils (`utils/`)

Utility scripts and helpers:

- **check_schema.py** - Database schema validation utility

## 🚀 Usage Guidelines

### Running Services
```bash
# Navigate to sandbox
cd scripts/sandbox

# Run a service
python services/intelligent_product_matching_service.py

# Run a demo
python demos/integrated_intelligent_discovery_demo.py

# Run analysis
python analysis/pix_database_analysis.py
```

### Adding New Files
When adding new files to the sandbox, follow these guidelines:

1. **Services**: Core implementations go in `services/`
2. **Demos**: Testing and demonstration scripts go in `demos/`
3. **Analysis**: Exploratory and analysis scripts go in `analysis/`
4. **Results**: All output files go in `results/`
5. **Documentation**: Plans and documentation go in `docs/`
6. **Utilities**: Helper scripts go in `utils/`

## 🔍 File Naming Conventions

- **Services**: `*_service.py` or `*_filter.py`
- **Demos**: `*_demo.py` or `*_simplified.py`
- **Analysis**: `*_analysis.py` or `explore_*.py`
- **Results**: Timestamped files with descriptive names
- **Documentation**: Uppercase with underscores (e.g., `SOLUTION_PLAN.md`)
- **Utilities**: `*_util.py` or descriptive names

## 🧹 Maintenance

### Cleaning Up
- Remove old timestamped result files regularly
- Archive outdated service versions
- Update documentation when making changes
- Remove unused demo files

### Version Control
- All files should be tracked in git
- Use proper commit messages
- Follow the project's version control guidelines

## 🎯 Key Features

### Intelligent Product Matching
- Grok-based product matching with confidence scoring
- Multi-level filtering and candidate ranking
- Comprehensive metadata extraction

### Enhanced Discovery
- Multiple discovery strategies
- Search space reduction algorithms
- Confidence-based result ranking

### Product Mapping
- Hierarchical mapping services
- Range-based product organization
- Technical specification matching

### Analysis Tools
- Database exploration utilities
- Statistical analysis scripts
- Performance benchmarking tools

## 📊 Current Status

- **Total Services**: 9 service implementations
- **Total Demos**: 5 demonstration scripts
- **Total Analysis**: 3 analysis tools
- **Total Results**: 25+ result files
- **Total Documentation**: 3 documentation files
- **Total Utilities**: 1 utility script

## 🔮 Future Enhancements

- Automated result cleanup scripts
- Performance benchmarking suite
- Integration testing framework
- Documentation generation tools
- Result visualization dashboards

---

**Organization Status**: ✅ **Clean and Well-Structured**  
**Maintenance**: ✅ **Regular Updates**  
**Documentation**: ✅ **Comprehensive**  
**Version Control**: ✅ **Fully Tracked** 