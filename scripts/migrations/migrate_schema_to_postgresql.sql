-- Drop existing tables if they exist
DROP TABLE IF EXISTS processing_debug CASCADE;
DROP TABLE IF EXISTS letter_product_matches CASCADE;
DROP TABLE IF EXISTS letter_products CASCADE;
DROP TABLE IF EXISTS letters CASCADE;

-- Drop sequences if they exist
DROP SEQUENCE IF EXISTS letters_id_seq CASCADE;
DROP SEQUENCE IF EXISTS products_id_seq CASCADE;
DROP SEQUENCE IF EXISTS matches_id_seq CASCADE;
DROP SEQUENCE IF EXISTS debug_id_seq CASCADE;

-- Create sequences
CREATE SEQUENCE letters_id_seq;
CREATE SEQUENCE products_id_seq;
CREATE SEQUENCE matches_id_seq;
CREATE SEQUENCE debug_id_seq;

-- letters table (exact match to DuckDB)
CREATE TABLE letters (
    id INTEGER PRIMARY KEY DEFAULT nextval('letters_id_seq'),
    document_name VARCHAR NOT NULL,
    document_type VARCHAR,
    document_title VARCHAR,
    source_file_path VARCHAR NOT NULL,
    file_size INTEGER,
    processing_method VARCHAR DEFAULT 'raw_file_grok',
    processing_time_ms FLOAT,
    extraction_confidence FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR DEFAULT 'processed',
    raw_grok_json VARCHAR,
    ocr_supplementary_json VARCHAR,
    processing_steps_json VARCHAR,
    file_hash VARCHAR,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    validation_details_json VARCHAR
);

-- letter_products table (exact match to DuckDB)
CREATE TABLE letter_products (
    id INTEGER PRIMARY KEY DEFAULT nextval('products_id_seq'),
    letter_id INTEGER NOT NULL,
    product_identifier VARCHAR,
    range_label VARCHAR,
    subrange_label VARCHAR,
    product_line VARCHAR,
    product_description VARCHAR,
    obsolescence_status VARCHAR,
    end_of_service_date VARCHAR,
    replacement_suggestions VARCHAR,
    confidence_score DOUBLE PRECISION DEFAULT 0.0,
    validation_status VARCHAR DEFAULT 'validated'
);

-- letter_product_matches table (exact match to DuckDB)
CREATE TABLE letter_product_matches (
    id INTEGER PRIMARY KEY DEFAULT nextval('matches_id_seq'),
    letter_id INTEGER NOT NULL,
    letter_product_id INTEGER NOT NULL,
    ibcatalogue_product_identifier VARCHAR NOT NULL,
    match_confidence FLOAT NOT NULL,
    match_reason VARCHAR,
    technical_match_score FLOAT DEFAULT 0.0,
    nomenclature_match_score FLOAT DEFAULT 0.0,
    product_line_match_score FLOAT DEFAULT 0.0,
    match_type VARCHAR,
    range_based_matching BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- processing_debug table (exact match to DuckDB)
CREATE TABLE processing_debug (
    id INTEGER PRIMARY KEY DEFAULT nextval('debug_id_seq'),
    letter_id INTEGER NOT NULL,
    processing_step VARCHAR NOT NULL,
    step_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    step_duration_ms FLOAT,
    step_success BOOLEAN DEFAULT TRUE,
    step_details VARCHAR
);

-- Add foreign key constraints
ALTER TABLE letter_products ADD CONSTRAINT fk_letter_products_letter_id 
    FOREIGN KEY (letter_id) REFERENCES letters(id) ON DELETE CASCADE;

ALTER TABLE letter_product_matches ADD CONSTRAINT fk_letter_product_matches_letter_id 
    FOREIGN KEY (letter_id) REFERENCES letters(id) ON DELETE CASCADE;

ALTER TABLE letter_product_matches ADD CONSTRAINT fk_letter_product_matches_letter_product_id 
    FOREIGN KEY (letter_product_id) REFERENCES letter_products(id) ON DELETE CASCADE;

ALTER TABLE processing_debug ADD CONSTRAINT fk_processing_debug_letter_id 
    FOREIGN KEY (letter_id) REFERENCES letters(id) ON DELETE CASCADE;

-- Performance indexes
CREATE INDEX idx_letters_source_path ON letters(source_file_path);
CREATE INDEX idx_letters_status ON letters(status);
CREATE INDEX idx_letters_file_hash ON letters(file_hash);
CREATE INDEX idx_letters_created_at ON letters(created_at);
CREATE INDEX idx_letters_document_name ON letters(document_name);

CREATE INDEX idx_products_letter_id ON letter_products(letter_id);
CREATE INDEX idx_products_range_label ON letter_products(range_label);
CREATE INDEX idx_products_product_identifier ON letter_products(product_identifier);

CREATE INDEX idx_matches_letter_id ON letter_product_matches(letter_id);
CREATE INDEX idx_matches_product_id ON letter_product_matches(letter_product_id);
CREATE INDEX idx_matches_ibcatalogue_id ON letter_product_matches(ibcatalogue_product_identifier);
CREATE INDEX idx_matches_confidence ON letter_product_matches(match_confidence);

CREATE INDEX idx_debug_letter_id ON processing_debug(letter_id);
CREATE INDEX idx_debug_timestamp ON processing_debug(step_timestamp);
CREATE INDEX idx_debug_step ON processing_debug(processing_step); 