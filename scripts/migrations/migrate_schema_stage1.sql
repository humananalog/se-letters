-- STAGE 1 Database Migration Script
-- Enhanced Schema for State-of-the-Art Document Processing Pipeline
-- Author: Alexandre Huther
-- Date: 2025-07-17

-- Drop existing tables if they exist (for fresh start)
DROP TABLE IF EXISTS processing_audit CASCADE;
DROP TABLE IF EXISTS letter_product_matches CASCADE;
DROP TABLE IF EXISTS letter_products CASCADE;
DROP TABLE IF EXISTS letters CASCADE;

-- Drop sequences if they exist
DROP SEQUENCE IF EXISTS letters_id_seq CASCADE;
DROP SEQUENCE IF EXISTS products_id_seq CASCADE;
DROP SEQUENCE IF EXISTS matches_id_seq CASCADE;
DROP SEQUENCE IF EXISTS audit_id_seq CASCADE;

-- Create sequences
CREATE SEQUENCE letters_id_seq START 1;
CREATE SEQUENCE products_id_seq START 1;
CREATE SEQUENCE matches_id_seq START 1;
CREATE SEQUENCE audit_id_seq START 1;

-- Enhanced Letters Table (STAGE 1)
CREATE TABLE letters (
    id INTEGER PRIMARY KEY DEFAULT nextval('letters_id_seq'),
    
    -- Document Identification
    document_name VARCHAR(255) NOT NULL,
    document_type VARCHAR(50),
    document_title VARCHAR(500),
    source_file_path TEXT NOT NULL,
    file_hash VARCHAR(64) NOT NULL,  -- SHA-256 for duplicate detection
    file_size BIGINT NOT NULL,
    
    -- Processing Metadata
    processing_method VARCHAR(100) DEFAULT 'production_pipeline_v2_3',
    processing_time_ms FLOAT,
    extraction_confidence FLOAT DEFAULT 0.0,
    processing_status VARCHAR(50) DEFAULT 'pending',
    
    -- Grok Integration
    grok_metadata JSONB,  -- Complete Grok output
    grok_confidence FLOAT,
    grok_processing_timestamp TIMESTAMP,
    
    -- Business Logic
    has_products BOOLEAN DEFAULT FALSE,  -- Quick check for products
    product_count INTEGER DEFAULT 0,
    is_duplicate BOOLEAN DEFAULT FALSE,
    duplicate_of_id INTEGER,
    
    -- Audit Trail
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    
    -- Validation
    validation_status VARCHAR(50) DEFAULT 'pending',
    validation_errors JSONB,
    
    -- Legacy fields for backward compatibility
    status VARCHAR(50) DEFAULT 'processed',
    raw_grok_json TEXT,
    ocr_supplementary_json TEXT,
    processing_steps_json TEXT,
    validation_details_json TEXT
);

-- Enhanced Letter Products Table (STAGE 1)
CREATE TABLE letter_products (
    id INTEGER PRIMARY KEY DEFAULT nextval('products_id_seq'),
    letter_id INTEGER NOT NULL,
    
    -- Product Identification
    product_identifier VARCHAR(255),  -- From Grok metadata
    range_label VARCHAR(255) NOT NULL,
    subrange_label VARCHAR(255),
    product_line VARCHAR(100),
    
    -- Product Details
    product_description TEXT,
    obsolescence_status VARCHAR(100),
    end_of_service_date VARCHAR(100),
    replacement_suggestions TEXT,
    
    -- Technical Specifications (from Grok)
    voltage_levels JSONB,
    current_ratings JSONB,
    power_ratings JSONB,
    frequencies JSONB,
    
    -- Confidence and Validation
    confidence_score FLOAT DEFAULT 0.0,
    validation_status VARCHAR(50) DEFAULT 'pending',
    grok_extraction_confidence FLOAT,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Letter Product Matches Table (for future STAGE 2)
CREATE TABLE letter_product_matches (
    id INTEGER PRIMARY KEY DEFAULT nextval('matches_id_seq'),
    letter_id INTEGER NOT NULL,
    letter_product_id INTEGER NOT NULL,
    ibcatalogue_product_identifier VARCHAR(255) NOT NULL,
    match_confidence FLOAT NOT NULL,
    match_reason TEXT,
    technical_match_score FLOAT DEFAULT 0.0,
    nomenclature_match_score FLOAT DEFAULT 0.0,
    product_line_match_score FLOAT DEFAULT 0.0,
    match_type VARCHAR(100),
    range_based_matching BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Processing Audit Table (NEW - for STAGE 1)
CREATE TABLE processing_audit (
    id INTEGER PRIMARY KEY DEFAULT nextval('audit_id_seq'),
    letter_id INTEGER,
    
    -- Processing Decision
    processing_decision VARCHAR(50) NOT NULL,  -- 'PROCESS', 'FORCE', 'SKIP', 'REJECT'
    decision_reason TEXT NOT NULL,
    
    -- Request Details
    request_source VARCHAR(100),  -- 'frontend', 'api', 'cli'
    request_user VARCHAR(100),
    request_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Processing Results
    processing_success BOOLEAN,
    processing_duration_ms FLOAT,
    products_found INTEGER DEFAULT 0,
    
    -- Error Handling
    error_message TEXT,
    error_code VARCHAR(100),
    
    -- Audit Trail
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add foreign key constraints
ALTER TABLE letters ADD CONSTRAINT fk_letters_duplicate_of 
    FOREIGN KEY (duplicate_of_id) REFERENCES letters(id) ON DELETE SET NULL;

ALTER TABLE letter_products ADD CONSTRAINT fk_letter_products_letter_id 
    FOREIGN KEY (letter_id) REFERENCES letters(id) ON DELETE CASCADE;

ALTER TABLE letter_product_matches ADD CONSTRAINT fk_letter_product_matches_letter_id 
    FOREIGN KEY (letter_id) REFERENCES letters(id) ON DELETE CASCADE;

ALTER TABLE letter_product_matches ADD CONSTRAINT fk_letter_product_matches_letter_product_id 
    FOREIGN KEY (letter_product_id) REFERENCES letter_products(id) ON DELETE CASCADE;

ALTER TABLE processing_audit ADD CONSTRAINT fk_processing_audit_letter_id 
    FOREIGN KEY (letter_id) REFERENCES letters(id) ON DELETE CASCADE;

-- Performance Indexes
CREATE INDEX idx_letters_file_hash ON letters(file_hash);
CREATE INDEX idx_letters_document_name ON letters(document_name);
CREATE INDEX idx_letters_file_size ON letters(file_size);
CREATE INDEX idx_letters_status ON letters(processing_status);
CREATE INDEX idx_letters_has_products ON letters(has_products);
CREATE INDEX idx_letters_created_at ON letters(created_at);
CREATE INDEX idx_letters_processing_method ON letters(processing_method);

CREATE INDEX idx_letter_products_letter_id ON letter_products(letter_id);
CREATE INDEX idx_letter_products_range_label ON letter_products(range_label);
CREATE INDEX idx_letter_products_product_identifier ON letter_products(product_identifier);
CREATE INDEX idx_letter_products_product_line ON letter_products(product_line);

CREATE INDEX idx_letter_product_matches_letter_id ON letter_product_matches(letter_id);
CREATE INDEX idx_letter_product_matches_product_id ON letter_product_matches(letter_product_id);
CREATE INDEX idx_letter_product_matches_ibcatalogue_id ON letter_product_matches(ibcatalogue_product_identifier);
CREATE INDEX idx_letter_product_matches_confidence ON letter_product_matches(match_confidence);

CREATE INDEX idx_processing_audit_letter_id ON processing_audit(letter_id);
CREATE INDEX idx_processing_audit_decision ON processing_audit(processing_decision);
CREATE INDEX idx_processing_audit_timestamp ON processing_audit(request_timestamp);
CREATE INDEX idx_processing_audit_source ON processing_audit(request_source);

-- Unique constraints for duplicate detection
CREATE UNIQUE INDEX idx_letters_file_hash_unique ON letters(file_hash);
CREATE UNIQUE INDEX idx_letters_document_name_size_unique ON letters(document_name, file_size);

-- Comments for documentation
COMMENT ON TABLE letters IS 'Enhanced letters table for STAGE 1 with duplicate detection and Grok integration';
COMMENT ON TABLE letter_products IS 'Enhanced letter products table with technical specifications from Grok';
COMMENT ON TABLE processing_audit IS 'Processing audit trail for compliance and debugging';
COMMENT ON COLUMN letters.file_hash IS 'SHA-256 hash for duplicate detection';
COMMENT ON COLUMN letters.has_products IS 'Quick boolean check if letter has products';
COMMENT ON COLUMN letters.grok_metadata IS 'Complete Grok processing output in JSONB format';
COMMENT ON COLUMN processing_audit.processing_decision IS 'Decision made: PROCESS, FORCE, SKIP, REJECT';

-- Grant permissions
GRANT ALL PRIVILEGES ON TABLE letters TO ahuther;
GRANT ALL PRIVILEGES ON TABLE letter_products TO ahuther;
GRANT ALL PRIVILEGES ON TABLE letter_product_matches TO ahuther;
GRANT ALL PRIVILEGES ON TABLE processing_audit TO ahuther;

GRANT USAGE, SELECT ON SEQUENCE letters_id_seq TO ahuther;
GRANT USAGE, SELECT ON SEQUENCE products_id_seq TO ahuther;
GRANT USAGE, SELECT ON SEQUENCE matches_id_seq TO ahuther;
GRANT USAGE, SELECT ON SEQUENCE audit_id_seq TO ahuther;

-- Insert migration record
INSERT INTO processing_audit (
    processing_decision, 
    decision_reason, 
    request_source, 
    request_user, 
    processing_success, 
    products_found
) VALUES (
    'MIGRATION',
    'STAGE 1 schema migration completed successfully',
    'system',
    'migration_script',
    true,
    0
);

-- Verify migration
SELECT 
    'Migration completed successfully' as status,
    COUNT(*) as letters_table_count,
    (SELECT COUNT(*) FROM letter_products) as products_table_count,
    (SELECT COUNT(*) FROM processing_audit) as audit_table_count
FROM letters; 