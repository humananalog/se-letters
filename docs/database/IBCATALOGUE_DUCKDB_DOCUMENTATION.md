# Ibcatalogue Duckdb Documentation

**Version: 2.2.0**  
**Author: Alexandre Huther**  
**Date: 2025-07-16**


**Version: 2.2.0
**Author: Alexandre Huther
**Date: 2025-07-16**


**Version**: 1.0.0  
**Created**: 2025-07-14T17:39:00.707437  
**Database Engine**: DuckDB  
**Source**: data/input/letters/IBcatalogue.xlsx

## 📊 Database Overview

The IBcatalogue DuckDB database is a high-performance, optimized version of the original Excel file containing Schneider Electric's complete product catalog.

### Database Statistics
- **Total Products**: 342,229
- **Product Ranges**: 4,067
- **Subranges**: 5,906
- **Brands**: 500
- **Active Products**: 158,457
- **Obsolete Products**: 183,772
- **Database Size**: 81.8 MB

### PL Services Distribution
- **PPIBS**: 157,713 products (46.1%)
- **IDPAS**: 77,768 products (22.7%)
- **IDIBS**: 34,981 products (10.2%)
- **PSIBS**: 27,440 products (8.0%)
- **SPIBS**: 20,830 products (6.1%)
- **DPIBS**: 20,184 products (5.9%)
- **DBIBS**: 3,313 products (1.0%)

## 🏗️ Database Schema

### Products Table
The main `products` table contains all product information with optimized data types:

```sql
CREATE TABLE products (
    product_identifier VARCHAR,      -- Unique product identifier
    product_type VARCHAR,           -- Product type classification
    product_description VARCHAR,    -- Detailed product description
    brand_code VARCHAR,            -- Brand code identifier
    brand_label VARCHAR,           -- Human-readable brand name
    range_code VARCHAR,            -- Range code identifier
    range_label VARCHAR,           -- Human-readable range name
    subrange_code VARCHAR,         -- Subrange code identifier
    subrange_label VARCHAR,        -- Human-readable subrange name
    devicetype_code VARCHAR,       -- Device type code
    devicetype_label VARCHAR,      -- Human-readable device type
    is_schneider_brand BOOLEAN,    -- Whether it's a Schneider brand
    serviceable BOOLEAN,           -- Whether product is serviceable
    traceable BOOLEAN,             -- Whether product is traceable
    commercial_status VARCHAR,     -- Commercial availability status
    end_of_production_date VARCHAR, -- Production end date
    end_of_commercialisation VARCHAR, -- Commercialization end date
    service_obsolescence_date VARCHAR, -- Service obsolescence date
    end_of_service_date VARCHAR,   -- Service end date
    average_life_duration_years INTEGER, -- Expected product lifetime
    service_business_value VARCHAR, -- Service business value
    warranty_duration_months INTEGER, -- Warranty duration
    include_installation_services BOOLEAN, -- Installation services included
    relevant_for_ip_creation BOOLEAN, -- Relevant for IP creation
    pl_services VARCHAR,           -- PL services classification (SPIBS, PPIBS, etc.)
    connectable BOOLEAN,           -- Whether product is connectable
    gdp VARCHAR,                   -- GDP classification
    bu_pm0_node VARCHAR,          -- Business unit PM0 node
    bu_label VARCHAR,             -- Business unit label
    range_label_norm VARCHAR,     -- Normalized range label for searching
    brand_label_norm VARCHAR,     -- Normalized brand label for searching
    product_description_norm VARCHAR, -- Normalized description for searching
    created_at TIMESTAMP,         -- Database creation timestamp
    database_version VARCHAR      -- Database schema version
);
```

## ⚡ Performance Optimization

### Indexes
The database includes comprehensive indexes for optimal query performance:

- **Primary Indexes**: product_identifier, range_label, brand_label
- **Search Indexes**: Normalized versions for case-insensitive searching
- **Composite Indexes**: Multi-column indexes for complex queries
- **Status Indexes**: Commercial status and PL services for filtering

### Performance Benchmarks
- **Range Lookup Ms**: 0.20ms
- **Complex Search Ms**: 1.51ms
- **Aggregation Query Ms**: 0.86ms
- **Full Text Search Ms**: 5.69ms
- **Large Result Set Ms**: 2.17ms

## 🔍 Query Examples

### Basic Product Lookup
```sql
-- Find all Galaxy 6000 products
SELECT * FROM products 
WHERE range_label = 'Galaxy 6000';

-- Find products by normalized range (case-insensitive)
SELECT * FROM products 
WHERE range_label_norm LIKE '%GALAXY%';
```

### Complex Multi-Field Search
```sql
-- Find active Schneider UPS products
SELECT product_identifier, range_label, commercial_status
FROM products 
WHERE product_description_norm LIKE '%UPS%'
  AND is_schneider_brand = true
  AND commercial_status NOT IN ('18-End of commercialisation');
```

### Business Intelligence Queries
```sql
-- PL Services distribution
SELECT pl_services, COUNT(*) as product_count
FROM products 
WHERE pl_services != ''
GROUP BY pl_services 
ORDER BY product_count DESC;

-- Obsolescence analysis by range
SELECT range_label, 
       COUNT(*) as total_products,
       SUM(CASE WHEN commercial_status IN ('18-End of commercialisation', 
                                           '19-end of commercialization block',
                                           '14-End of commerc. announced') 
           THEN 1 ELSE 0 END) as obsolete_products
FROM products 
WHERE range_label != ''
GROUP BY range_label
HAVING COUNT(*) > 10
ORDER BY obsolete_products DESC;
```

## 🚀 Usage in SE Letters Pipeline

### Integration Points
The DuckDB database integrates with several pipeline components:

1. **Product Mapping Service**: Fast product lookups and range matching
2. **Semantic Extraction Engine**: Rapid validation of extracted product ranges
3. **Vector Search Engine**: Efficient similarity searching
4. **SOTA Range Mapping**: Comprehensive product universe mapping

### Performance Benefits
- **100x faster** than Excel file operations
- **Sub-second queries** for complex searches
- **Memory efficient** loading and processing
- **Concurrent access** for web application

## 📈 Migration Performance
- **Excel Load Time**: 30.37s
- **Schema Creation Time**: 1.68s
- **Index Creation Time**: 0.66s

## 🔧 Maintenance

### Backup and Recovery
- Automatic backup created before migration
- Backups stored in: `data/backups/`
- Easy restoration from backup files

### Updates and Versioning
- Database version tracked in schema
- Migration scripts for future updates
- Comprehensive validation on each update

## 📞 Support

### Database Issues
- Check logs for detailed error information
- Validate database integrity using built-in checks
- Contact SE Letters team for assistance

### Performance Issues
- Monitor query execution times
- Check index usage with EXPLAIN
- Review query optimization opportunities

---

**Database Version**: 1.0.0  
**Last Updated**: 2025-07-14T17:39:00.707437  
**Maintainer**: SE Letters Team  
**Location**: `data/IBcatalogue.duckdb`
