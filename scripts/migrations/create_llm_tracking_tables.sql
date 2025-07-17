-- LLM API Call Tracking and Raw Content Storage Migration
-- Enhanced Schema for Token Usage Tracking and Raw Content Management
-- Author: Alexandre Huther
-- Date: 2025-07-17
-- Version: 1.0.0

-- ==========================================
-- LLM API CALL TRACKING TABLE
-- ==========================================

-- Drop existing tables if they exist
DROP TABLE IF EXISTS llm_api_calls CASCADE;
DROP TABLE IF EXISTS letter_raw_content CASCADE;

-- Drop sequences if they exist
DROP SEQUENCE IF EXISTS llm_api_calls_id_seq CASCADE;
DROP SEQUENCE IF EXISTS letter_raw_content_id_seq CASCADE;

-- Create sequences
CREATE SEQUENCE llm_api_calls_id_seq START 1;
CREATE SEQUENCE letter_raw_content_id_seq START 1;

-- LLM API Call Tracking Table
CREATE TABLE llm_api_calls (
    id INTEGER PRIMARY KEY DEFAULT nextval('llm_api_calls_id_seq'),
    
    -- Request Identification
    call_id VARCHAR(255) UNIQUE NOT NULL,  -- Unique identifier for each API call
    letter_id INTEGER,  -- FK to letters table (nullable for non-letter processing)
    operation_type VARCHAR(100) NOT NULL,  -- 'metadata_extraction', 'product_matching', 'validation', etc.
    
    -- API Configuration
    api_provider VARCHAR(50) NOT NULL DEFAULT 'xai',  -- 'xai', 'openai', 'anthropic', etc.
    model_name VARCHAR(100) NOT NULL,  -- 'grok-3-latest', 'grok-4', etc.
    api_version VARCHAR(50),  -- API version if available
    base_url VARCHAR(255) NOT NULL,
    
    -- Request Details
    system_prompt_hash VARCHAR(64) NOT NULL,  -- SHA-256 hash of system prompt for caching
    user_prompt_hash VARCHAR(64) NOT NULL,   -- SHA-256 hash of user prompt for caching
    prompt_version VARCHAR(50),  -- Version from prompts.yaml (e.g., "2.2.0")
    prompt_template_name VARCHAR(100),  -- Template name from prompts.yaml
    
    -- Token Usage (from xAI SDK usage object)
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    
    -- Performance Metrics
    response_time_ms FLOAT NOT NULL,
    request_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    response_timestamp TIMESTAMP,
    
    -- Response Quality
    response_success BOOLEAN NOT NULL DEFAULT FALSE,
    response_status_code INTEGER,
    confidence_score FLOAT,  -- Extracted confidence from response
    
    -- Error Handling
    error_type VARCHAR(100),  -- 'timeout', 'rate_limit', 'authentication', 'parsing', etc.
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    -- Version Control & Audit
    git_commit_hash VARCHAR(40),  -- Current git commit for reproducibility
    pipeline_version VARCHAR(50),  -- SE Letters pipeline version
    config_hash VARCHAR(64),  -- Hash of configuration used
    
    -- Cost Tracking (for future pricing analysis)
    estimated_cost_usd DECIMAL(10, 6),  -- Estimated API call cost
    
    -- Processing Context
    document_name VARCHAR(255),
    document_size_bytes BIGINT,
    input_char_count INTEGER,
    output_char_count INTEGER,
    
    -- Indexes
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- RAW LETTER CONTENT STORAGE TABLE
-- ==========================================

-- Letter Raw Content Storage Table
CREATE TABLE letter_raw_content (
    id INTEGER PRIMARY KEY DEFAULT nextval('letter_raw_content_id_seq'),
    
    -- Content Identification
    content_hash VARCHAR(64) UNIQUE NOT NULL,  -- SHA-256 hash of raw content
    letter_id INTEGER NOT NULL,  -- FK to letters table
    
    -- Content Storage
    raw_text TEXT NOT NULL,  -- Original extracted text content
    raw_text_length INTEGER NOT NULL,  -- Character count for quick reference
    encoding VARCHAR(50) DEFAULT 'utf-8',
    
    -- Processing Context
    extraction_method VARCHAR(100) NOT NULL,  -- 'docx_python', 'pdf_pymupdf', 'ocr_tesseract', etc.
    source_file_path TEXT NOT NULL,
    source_file_size BIGINT NOT NULL,
    source_file_mime_type VARCHAR(100),
    
    -- Prompt Version Management (Key for duplicate detection)
    prompt_version VARCHAR(50) NOT NULL,  -- Version from prompts.yaml (e.g., "2.2.0")
    system_prompt_hash VARCHAR(64) NOT NULL,  -- SHA-256 hash of system prompt used
    prompt_config_hash VARCHAR(64) NOT NULL,  -- Hash of entire prompts.yaml config
    
    -- Uniqueness Control (content + prompt version = unique processing unit)
    content_prompt_signature VARCHAR(128) UNIQUE NOT NULL,  -- Concatenated hash for uniqueness
    
    -- Processing Status
    processing_status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'processed', 'failed', 'skipped'
    llm_processed BOOLEAN DEFAULT FALSE,
    last_processed_at TIMESTAMP,
    processing_attempts INTEGER DEFAULT 0,
    
    -- Quality Metrics
    content_quality_score FLOAT,  -- OCR/extraction quality assessment
    language_detected VARCHAR(10),  -- ISO language code
    has_technical_content BOOLEAN DEFAULT FALSE,
    has_tables BOOLEAN DEFAULT FALSE,
    has_images BOOLEAN DEFAULT FALSE,
    
    -- Content Analysis
    word_count INTEGER,
    paragraph_count INTEGER,
    page_count INTEGER,
    
    -- Grok Processing Results (linked to this content version)
    grok_response_id INTEGER,  -- FK to llm_api_calls table
    grok_metadata JSONB,  -- Processed metadata from Grok
    grok_confidence FLOAT,
    products_extracted INTEGER DEFAULT 0,
    
    -- Version Control & Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Archival
    is_archived BOOLEAN DEFAULT FALSE,
    archive_reason TEXT
);

-- ==========================================
-- PERFORMANCE INDEXES
-- ==========================================

-- LLM API Calls Indexes
CREATE INDEX idx_llm_api_calls_letter_id ON llm_api_calls(letter_id);
CREATE INDEX idx_llm_api_calls_operation_type ON llm_api_calls(operation_type);
CREATE INDEX idx_llm_api_calls_model_name ON llm_api_calls(model_name);
CREATE INDEX idx_llm_api_calls_prompt_version ON llm_api_calls(prompt_version);
CREATE INDEX idx_llm_api_calls_timestamp ON llm_api_calls(request_timestamp);
CREATE INDEX idx_llm_api_calls_success ON llm_api_calls(response_success);
CREATE INDEX idx_llm_api_calls_tokens ON llm_api_calls(total_tokens);
CREATE INDEX idx_llm_api_calls_cost ON llm_api_calls(estimated_cost_usd);

-- Raw Content Indexes
CREATE INDEX idx_letter_raw_content_letter_id ON letter_raw_content(letter_id);
CREATE INDEX idx_letter_raw_content_hash ON letter_raw_content(content_hash);
CREATE INDEX idx_letter_raw_content_prompt_version ON letter_raw_content(prompt_version);
CREATE INDEX idx_letter_raw_content_status ON letter_raw_content(processing_status);
CREATE INDEX idx_letter_raw_content_signature ON letter_raw_content(content_prompt_signature);
CREATE INDEX idx_letter_raw_content_processed ON letter_raw_content(llm_processed);
CREATE INDEX idx_letter_raw_content_quality ON letter_raw_content(content_quality_score);
CREATE INDEX idx_letter_raw_content_size ON letter_raw_content(raw_text_length);

-- ==========================================
-- FOREIGN KEY CONSTRAINTS
-- ==========================================

-- Add foreign key constraints
ALTER TABLE llm_api_calls ADD CONSTRAINT fk_llm_api_calls_letter_id 
    FOREIGN KEY (letter_id) REFERENCES letters(id) ON DELETE CASCADE;

ALTER TABLE letter_raw_content ADD CONSTRAINT fk_letter_raw_content_letter_id 
    FOREIGN KEY (letter_id) REFERENCES letters(id) ON DELETE CASCADE;

ALTER TABLE letter_raw_content ADD CONSTRAINT fk_letter_raw_content_grok_response 
    FOREIGN KEY (grok_response_id) REFERENCES llm_api_calls(id) ON DELETE SET NULL;

-- ==========================================
-- TRIGGERS FOR UPDATED_AT
-- ==========================================

-- Create trigger function for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for both tables
CREATE TRIGGER update_llm_api_calls_updated_at BEFORE UPDATE ON llm_api_calls 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_letter_raw_content_updated_at BEFORE UPDATE ON letter_raw_content 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==========================================
-- VIEWS FOR ANALYTICS
-- ==========================================

-- Token Usage Analytics View
CREATE VIEW llm_token_usage_analytics AS
SELECT 
    DATE(request_timestamp) as call_date,
    model_name,
    operation_type,
    prompt_version,
    COUNT(*) as total_calls,
    SUM(prompt_tokens) as total_prompt_tokens,
    SUM(completion_tokens) as total_completion_tokens,
    SUM(total_tokens) as total_tokens,
    AVG(response_time_ms) as avg_response_time_ms,
    SUM(estimated_cost_usd) as total_estimated_cost_usd,
    AVG(confidence_score) as avg_confidence_score,
    COUNT(CASE WHEN response_success THEN 1 END) * 100.0 / COUNT(*) as success_rate_percent
FROM llm_api_calls
GROUP BY DATE(request_timestamp), model_name, operation_type, prompt_version
ORDER BY call_date DESC, total_tokens DESC;

-- Content Processing Analytics View
CREATE VIEW content_processing_analytics AS
SELECT 
    prompt_version,
    extraction_method,
    COUNT(*) as total_content_records,
    COUNT(CASE WHEN llm_processed THEN 1 END) as processed_count,
    AVG(raw_text_length) as avg_content_length,
    AVG(products_extracted) as avg_products_per_document,
    AVG(grok_confidence) as avg_grok_confidence,
    COUNT(CASE WHEN processing_status = 'processed' THEN 1 END) * 100.0 / COUNT(*) as processing_success_rate
FROM letter_raw_content
GROUP BY prompt_version, extraction_method
ORDER BY prompt_version DESC, avg_products_per_document DESC;

-- ==========================================
-- HELPER FUNCTIONS
-- ==========================================

-- Function to generate content-prompt signature
CREATE OR REPLACE FUNCTION generate_content_prompt_signature(
    content_hash_val VARCHAR(64), 
    prompt_config_hash_val VARCHAR(64)
) RETURNS VARCHAR(128) AS $$
BEGIN
    RETURN ENCODE(SHA256((content_hash_val || '::' || prompt_config_hash_val)::bytea), 'hex');
END;
$$ LANGUAGE plpgsql;

-- Function to check for duplicate content processing
CREATE OR REPLACE FUNCTION check_duplicate_processing(
    content_hash_val VARCHAR(64),
    prompt_version_val VARCHAR(50),
    prompt_config_hash_val VARCHAR(64)
) RETURNS BOOLEAN AS $$
DECLARE
    signature VARCHAR(128);
    exists_count INTEGER;
BEGIN
    signature := generate_content_prompt_signature(content_hash_val, prompt_config_hash_val);
    
    SELECT COUNT(*) INTO exists_count
    FROM letter_raw_content
    WHERE content_prompt_signature = signature 
      AND prompt_version = prompt_version_val;
    
    RETURN exists_count > 0;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- COMMENTS AND DOCUMENTATION
-- ==========================================

COMMENT ON TABLE llm_api_calls IS 'Comprehensive tracking of all LLM API calls with token usage, performance metrics, and version control';
COMMENT ON TABLE letter_raw_content IS 'Storage of raw letter content with prompt version-based duplicate detection';

COMMENT ON COLUMN llm_api_calls.call_id IS 'Unique identifier for each API call (UUID recommended)';
COMMENT ON COLUMN llm_api_calls.system_prompt_hash IS 'SHA-256 hash of system prompt for caching and deduplication';
COMMENT ON COLUMN llm_api_calls.prompt_version IS 'Version from prompts.yaml for tracking prompt evolution';
COMMENT ON COLUMN llm_api_calls.total_tokens IS 'Total tokens used (prompt + completion) from xAI SDK usage object';

COMMENT ON COLUMN letter_raw_content.content_prompt_signature IS 'Unique signature combining content hash and prompt config hash for duplicate detection';
COMMENT ON COLUMN letter_raw_content.prompt_version IS 'Version from prompts.yaml - key field for duplicate management';
COMMENT ON COLUMN letter_raw_content.llm_processed IS 'Whether this content has been processed by LLM with current prompt version';

-- Migration completed successfully
INSERT INTO llm_api_calls (call_id, operation_type, model_name, base_url, system_prompt_hash, user_prompt_hash, prompt_version, response_time_ms, response_success, document_name) 
VALUES ('migration-marker-' || EXTRACT(EPOCH FROM NOW()), 'migration', 'schema-migration', 'localhost', 'migration-hash', 'migration-hash', '1.0.0', 0, TRUE, 'schema_migration'); 