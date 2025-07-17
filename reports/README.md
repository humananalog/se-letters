# Database Reports

This directory contains tools for generating comprehensive reports from the SE Letters database.

## 📊 Database Report Generator

The `database_report_generator.py` script provides comprehensive reporting capabilities for the SE Letters pipeline database.

### Features

- **Summary Statistics**: Database overview, processing statistics, status distribution
- **Detailed Tables**: Letters, products, and matches in tabular format
- **Multiple Export Formats**: Console, file, CSV, Excel
- **Real-time Data**: Connects directly to PostgreSQL database
- **Professional Formatting**: Nice tabular output with proper formatting

### Usage

#### Basic Console Report
```bash
python reports/database_report_generator.py --format console
```

#### Save to Text File
```bash
python reports/database_report_generator.py --format file
```

#### Export to CSV Files
```bash
python reports/database_report_generator.py --format csv
```
Generates separate CSV files:
- `database_report_letters_YYYYMMDD_HHMMSS.csv`
- `database_report_products_YYYYMMDD_HHMMSS.csv`
- `database_report_matches_YYYYMMDD_HHMMSS.csv`

#### Export to Excel
```bash
python reports/database_report_generator.py --format excel
```
Generates a single Excel file with multiple sheets:
- Summary statistics
- Letters data
- Products data
- Matches data
- Status distribution
- Document type distribution

#### Generate All Formats
```bash
python reports/database_report_generator.py --format all
```

#### Custom Database Connection
```bash
python reports/database_report_generator.py --format console --connection "postgresql://user:pass@host:port/db"
```

#### Custom Output Directory
```bash
python reports/database_report_generator.py --format excel --output-dir /path/to/reports
```

### Report Contents

#### Summary Report
- Database overview (total counts)
- Processing statistics (time, confidence)
- Status distribution
- Document type distribution
- Date range

#### Letters Table
- Document information
- Processing metrics
- File details
- Timestamps

#### Products Table
- Product identifiers
- Range and subrange labels
- Product lines
- Confidence scores
- Validation status

#### Matches Table
- Product matching results
- IBcatalogue identifiers
- Match confidence scores
- Match types

### Output Files

All generated files are saved in the `reports/output/` directory with timestamps:

```
reports/output/
├── database_report_YYYYMMDD_HHMMSS.txt          # Text report
├── database_report_YYYYMMDD_HHMMSS.xlsx         # Excel report
├── database_report_letters_YYYYMMDD_HHMMSS.csv  # Letters CSV
├── database_report_products_YYYYMMDD_HHMMSS.csv # Products CSV
└── database_report_matches_YYYYMMDD_HHMMSS.csv  # Matches CSV
```

### Requirements

- Python 3.9+
- PostgreSQL database access
- Required packages: `psycopg2`, `pandas`, `tabulate`, `openpyxl`

### Configuration

The script uses the following configuration sources (in order of priority):
1. `--connection` command line argument
2. `DATABASE_URL` environment variable
3. Default connection string: `postgresql://ahuther:bender1980@localhost:5432/se_letters_dev`

### Examples

#### Quick Database Overview
```bash
python reports/database_report_generator.py --format console
```

#### Export for Analysis
```bash
python reports/database_report_generator.py --format excel
```

#### Generate CSV for Data Processing
```bash
python reports/database_report_generator.py --format csv
```

### Troubleshooting

#### Connection Issues
- Verify database is running
- Check connection string
- Ensure user has read permissions

#### Missing Data
- Check if tables exist
- Verify column names match schema
- Ensure data has been processed

#### Export Errors
- Check write permissions for output directory
- Ensure required packages are installed
- Verify sufficient disk space

### Author

**Alexandre Huther**  
Date: 2025-07-17  
Version: 1.0.0 