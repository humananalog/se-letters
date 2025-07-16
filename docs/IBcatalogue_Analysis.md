# Ibcatalogue Analysis

**Version: 2.2.0**  
**Author: Alexandre Huther**  
**Date: 2025-07-16**


**Version: 2.2.0
**Author: Alexandre Huther
**Date: 2025-07-16**


## Overview

The IBcatalogue.xlsx file is the master referential database containing Schneider Electric's complete product catalog. This document provides a comprehensive analysis of its structure, content, and usage patterns.

## File Characteristics

- **File**: `data/input/letters/IBcatalogue.xlsx`
- **Size**: 45.6 MB
- **Records**: 342,229 products
- **Columns**: 29 data fields
- **Sheets**: 2 ('OIC_out' - main data, 'Sheet2' - secondary)

## Data Structure

### Column Definitions

| # | Column Name | Type | Description | Example Values |
|---|-------------|------|-------------|----------------|
| 1 | `PRODUCT_IDENTIFIER` | String | Unique product identifier | AAA_RM6_NE_IQI, AAA10094 |
| 2 | `PRODUCT_TYPE` | String | Product type code | CR, ST, SY |
| 3 | `PRODUCT_DESCRIPTION` | String | Human-readable product description | "FIX BOM RM6 10kV FRUHAUF NE_IQI" |
| 4 | `BRAND_CODE` | String | Internal brand code | SCHNEIDERELECTRIC, SEMARELECTRIC |
| 5 | `BRAND_LABEL` | String | Brand name | Schneider Electric, Square D |
| 6 | `RANGE_CODE` | Numeric | Internal range code | 967.0, 1234.0 |
| 7 | `RANGE_LABEL` | String | Product range name | RM6, TeSys D, PIX |
| 8 | `SUBRANGE_CODE` | Numeric | Internal subrange code | Often null |
| 9 | `SUBRANGE_LABEL` | String | Subrange name | Often null |
| 10 | `DEVICETYPE_CODE` | String | Device type identifier | DEVTYP000068 |
| 11 | `DEVICETYPE_LABEL` | String | Device type description | "MV equipment - MV ring main unit (RMU)" |
| 12 | `IS_SCHNEIDER_BRAND` | String | Schneider brand flag | Y, N |
| 13 | `SERVICEABLE` | String | Service availability flag | Y, N |
| 14 | `TRACEABLE` | String | Traceability flag | Y, N |
| 15 | `COMMERCIAL_STATUS` | String | Current commercial status | See status codes below |
| 16 | `END_OF_PRODUCTION_DATE` | Date | Production end date | 2022-06-30, 4000-12-31 |
| 17 | `END_OF_COMMERCIALISATION` | Date | Commercialization end date | 2022-09-30, 4000-12-31 |
| 18 | `SERVICE_OBSOLECENSE_DATE` | Date | Service obsolescence date | 2022-09-30, 4000-12-31 |
| 19 | `END_OF_SERVICE_DATE` | Date | Service end date | 2022-10-02, 4000-12-31 |
| 20 | `AVERAGE_LIFE_DURATION_IN_YEARS` | Numeric | Expected product lifespan | 20.0, 15.0 |
| 21 | `SERVICE_BUSINESS_VALUE` | String | Service business value | Low, Medium, High |
| 22 | `WARRANTY_DURATION_IN_MONTHS` | Numeric | Warranty period | Often null |
| 23 | `INCLUDE_INSTALLATION_SERVICES` | String | Installation services flag | Often null |
| 24 | `RELEVANT_FOR_IP_CREATION` | String | IP creation relevance | Y, N |
| 25 | `PL_SERVICES` | String | Product line services | PPIBS, IDPAS, IDIBS |
| 26 | `CONNECTABLE` | String | Connectivity capability | WITH_UPGRADE, NOT_CONNECTABLE |
| 27 | `GDP` | String | GDP identifier | 309519, 30185D |
| 28 | `BU_PM0_NODE` | Numeric | Business unit PM0 node | 190789.0 |
| 29 | `BU_LABEL` | String | Business unit label | POWER SYSTEMS, POWER PRODUCTS |

## Key Data Insights

### Brand Distribution
- **Schneider Electric**: 223,953 products (65.4%)
- **Square D**: 44,719 products (13.1%)
- **HIMEL**: 17,634 products (5.2%)
- **Telemecanique**: 11,838 products (3.5%)
- **APC**: 11,610 products (3.4%)
- **Others**: 32,475 products (9.4%)

### Commercial Status Codes
| Status Code | Description | Count | Percentage |
|-------------|-------------|-------|------------|
| 08-Commercialised | Currently commercialized | 119,532 | 34.9% |
| 18-End of commercialisation | Commercialization ended | 109,358 | 32.0% |
| 19-end of commercialization block | Commercialization blocked | 72,006 | 21.0% |
| 00-Initialisation | In initialization phase | 20,050 | 5.9% |
| 16-Post commercialisation | Post-commercialization | 9,444 | 2.8% |
| 01-Never commercialised | Never commercialized | 5,801 | 1.7% |
| Others | Various other statuses | 6,038 | 1.8% |

### Service Categories (PL_SERVICES)
| Service Code | Description | Count | Percentage |
|--------------|-------------|-------|------------|
| PPIBS | Power Products IBS | 157,713 | 46.1% |
| IDPAS | Industrial Process Automation | 77,768 | 22.7% |
| IDIBS | Industrial IBS | 34,981 | 10.2% |
| PSIBS | Power Systems IBS | 27,440 | 8.0% |
| SPIBS | Secure Power IBS | 20,830 | 6.1% |
| DPIBS | Digital Power IBS | 20,184 | 5.9% |
| DBIBS | Digital Business IBS | 3,313 | 1.0% |

### Business Unit Distribution
| Business Unit | Count | Percentage |
|---------------|-------|------------|
| POWER PRODUCTS | 106,598 | 31.2% |
| IND PROCESS AUTOMATION | 77,816 | 22.7% |
| GLOBAL SERVICES | 33,709 | 9.8% |
| HOME & DISTRIBUTION | 27,268 | 8.0% |
| IND AUTOMATION OPS | 25,339 | 7.4% |
| DIGITAL ENERGY | 19,679 | 5.7% |
| SECURE POWER | 18,618 | 5.4% |
| ENERGY MANAGEMENT | 18,144 | 5.3% |
| POWER SYSTEMS | 14,455 | 4.2% |
| Others | 1,593 | 0.5% |

## PIX Product Range Analysis

The catalog contains **347 products** with "PIX" in their range label:

### PIX Range Breakdown
| Range Label | Count | Description |
|-------------|-------|-------------|
| PIX | 130 | Base PIX range |
| PIX Roll on Floor | 45 | Mobile PIX units |
| PIX 50 kA | 33 | High-current PIX units |
| PIX Easy 17.5 | 29 | Easy-install PIX 17.5kV |
| PIX DBB | 21 | PIX with dead break/make |
| PIX 36 | 14 | PIX 36kV range |
| PIX 2B | 12 | PIX 2B variant |
| PIX-S | 10 | PIX-S series |
| PIX Compact | 10 | Compact PIX units |
| PIX MCC | 9 | PIX Motor Control Centers |

### PIX Commercial Status
- **Active (08-Commercialised)**: 89 products
- **End of commercialization (18)**: 158 products
- **Commercialization blocked (19)**: 89 products
- **Other statuses**: 11 products

## Data Quality Observations

### Null Values
- `SUBRANGE_CODE`: High null percentage (~85%)
- `SUBRANGE_LABEL`: High null percentage (~85%)
- `RANGE_CODE`: Some nulls (~10%)
- `RANGE_LABEL`: Some nulls (~10%)
- `WARRANTY_DURATION_IN_MONTHS`: High null percentage (~90%)

### Date Patterns
- **Future dates (4000-12-31)**: Used for products with no planned end dates
- **Past dates**: Actual end-of-life dates for obsolete products
- **Recent dates**: Current obsolescence activities

### Identifier Patterns
- `PRODUCT_IDENTIFIER`: Alphanumeric, various formats
- `DEVICETYPE_CODE`: Standardized format (DEVTYP######)
- `GDP`: Mixed numeric and alphanumeric

## Usage Recommendations

### For Obsolescence Letter Matching

1. **Primary Matching Fields**:
   - `RANGE_LABEL`: Main product range identification
   - `SUBRANGE_LABEL`: Secondary range identification
   - `PRODUCT_DESCRIPTION`: Full-text matching

2. **Status Filtering**:
   - Focus on status codes 18 and 19 for obsolescence matching
   - Use `END_OF_COMMERCIALISATION` dates for timeline analysis

3. **Brand Filtering**:
   - Filter by `IS_SCHNEIDER_BRAND = 'Y'` for Schneider products
   - Use `BRAND_LABEL` for multi-brand analysis

### For Service Analysis

1. **Service Availability**:
   - `SERVICEABLE = 'Y'` for service-eligible products
   - `SERVICE_OBSOLECENSE_DATE` for service timeline

2. **Business Context**:
   - `PL_SERVICES` for product line categorization
   - `BU_LABEL` for business unit analysis

## Data Processing Notes

### Header Row
- The first row contains actual data, not headers
- Headers are properly defined in the Excel file
- **No need to remove the first row** - it contains valid product data

### Data Types
- Dates are properly formatted as datetime objects
- Numeric codes may contain nulls (handle appropriately)
- String fields may contain special characters

### Encoding
- File uses standard Excel encoding
- No special character encoding issues observed

## Integration with SE Letters Pipeline

### Configuration Updates Needed

```yaml
data:
  excel_file: "data/input/letters/IBcatalogue.xlsx"
  excel_sheet: "OIC_out"
  
  # Column mappings
  columns:
    product_id: "PRODUCT_IDENTIFIER"
    range_name: "RANGE_LABEL"
    subrange_name: "SUBRANGE_LABEL"
    description: "PRODUCT_DESCRIPTION"
    brand: "BRAND_LABEL"
    status: "COMMERCIAL_STATUS"
    end_of_commercialization: "END_OF_COMMERCIALISATION"
```

### Processing Strategy

1. **Load Data**: Use pandas to read the OIC_out sheet
2. **Filter Data**: Focus on Schneider Electric products with relevant status codes
3. **Index Creation**: Build FAISS index on RANGE_LABEL and PRODUCT_DESCRIPTION
4. **Matching Logic**: Use fuzzy matching for product range identification
5. **Status Analysis**: Correlate with obsolescence dates and status codes

This comprehensive analysis provides the foundation for effective integration of the IBcatalogue.xlsx master referential with the SE Letters obsolescence matching pipeline. 