# LLM API Call Tracking and Raw Content Storage Documentation

**Version: 1.0.0**  
**Author: Alexandre Huther**  
**Date: 2025-07-17**

## 🎯 Overview

This document describes the comprehensive LLM API call tracking and raw content storage system implemented for the SE Letters project. The system captures detailed token usage, performance metrics, and manages raw document content with intelligent duplicate detection based on prompt version control.

## 📋 System Requirements

The implementation addresses two critical requirements:

### Requirement 1: Token Usage Tracking
- **Capture token usage** from each xAI Grok API call using the official xAI SDK
- **Store comprehensive metrics** including prompt/completion tokens, costs, performance
- **Version control** with git commit hashes and prompt versions from `prompts.yaml`
- **Full audit trail** for compliance and cost analysis

### Requirement 2: Raw Content Storage with Duplicate Management
- **Store raw letter content** extracted from documents for future processing
- **Intelligent duplicate detection** based on content hash + prompt version signature
- **Prompt version awareness** - LLM outputs vary with prompt changes, so uniqueness is based on `prompts.yaml` version
- **Efficient processing** - avoid reprocessing same content with same prompt version

## 🗄️ Database Schema

### 1. LLM API Calls Tracking Table

```sql
CREATE TABLE llm_api_calls (
    id INTEGER PRIMARY KEY,
    
    -- Request Identification
    call_id VARCHAR(255) UNIQUE NOT NULL,  -- UUID for each API call
    letter_id INTEGER,  -- FK to letters table (nullable)
    operation_type VARCHAR(100) NOT NULL,  -- 'metadata_extraction', 'product_matching', etc.
    
    -- API Configuration
    api_provider VARCHAR(50) DEFAULT 'xai',
    model_name VARCHAR(100) NOT NULL,  -- 'grok-3-latest', 'grok-4'
    api_version VARCHAR(50),
    base_url VARCHAR(255) NOT NULL,
    
    -- Request Details
    system_prompt_hash VARCHAR(64) NOT NULL,  -- SHA-256 of system prompt
    user_prompt_hash VARCHAR(64) NOT NULL,    -- SHA-256 of user prompt
    prompt_version VARCHAR(50),  -- From prompts.yaml (e.g., "2.2.0")
    prompt_template_name VARCHAR(100),  -- Template name from prompts.yaml
    
    -- Token Usage (from xAI SDK response.usage object)
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
    error_type VARCHAR(100),  -- 'timeout', 'rate_limit', 'authentication'
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    -- Version Control & Audit
    git_commit_hash VARCHAR(40),  -- Current git commit for reproducibility
    pipeline_version VARCHAR(50),  -- SE Letters pipeline version
    config_hash VARCHAR(64),  -- Hash of configuration used
    
    -- Cost Tracking
    estimated_cost_usd DECIMAL(10, 6),  -- Estimated API call cost
    
    -- Processing Context
    document_name VARCHAR(255),
    document_size_bytes BIGINT,
    input_char_count INTEGER,
    output_char_count INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. Raw Letter Content Storage Table

```sql
CREATE TABLE letter_raw_content (
    id INTEGER PRIMARY KEY,
    
    -- Content Identification
    content_hash VARCHAR(64) UNIQUE NOT NULL,  -- SHA-256 of raw content
    letter_id INTEGER NOT NULL,  -- FK to letters table
    
    -- Content Storage
    raw_text TEXT NOT NULL,  -- Original extracted text content
    raw_text_length INTEGER NOT NULL,  -- Character count for quick reference
    encoding VARCHAR(50) DEFAULT 'utf-8',
    
    -- Processing Context
    extraction_method VARCHAR(100) NOT NULL,  -- 'docx_python', 'pdf_pymupdf'
    source_file_path TEXT NOT NULL,
    source_file_size BIGINT NOT NULL,
    source_file_mime_type VARCHAR(100),
    
    -- Prompt Version Management (KEY for duplicate detection)
    prompt_version VARCHAR(50) NOT NULL,  -- From prompts.yaml (e.g., "2.2.0")
    system_prompt_hash VARCHAR(64) NOT NULL,  -- SHA-256 of system prompt
    prompt_config_hash VARCHAR(64) NOT NULL,  -- Hash of entire prompts.yaml
    
    -- Uniqueness Control (content + prompt version = unique processing unit)
    content_prompt_signature VARCHAR(128) UNIQUE NOT NULL,  -- Combined hash
    
    -- Processing Status
    processing_status VARCHAR(50) DEFAULT 'pending',
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
    
    -- Grok Processing Results
    grok_response_id INTEGER,  -- FK to llm_api_calls table
    grok_metadata JSONB,  -- Processed metadata from Grok
    grok_confidence FLOAT,
    products_extracted INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔄 Processing Flow

### 1. Document Processing with Token Tracking

```python
# Enhanced XAI Service automatically tracks all API calls
enhanced_xai_service = EnhancedXAIService(config)

# Process document with comprehensive tracking
result = enhanced_xai_service.extract_comprehensive_metadata_with_tracking(
    text=document_content,
    document_name=file_path.name,
    letter_id=letter_id,  # Optional - links to letters table
    extraction_method="pdf_pymupdf",  # How content was extracted
    source_file_path=str(file_path.resolve()),
    source_file_size=file_path.stat().st_size
)

# Result includes tracking metadata
tracking_info = result.get('tracking_metadata', {})
print(f"Call ID: {tracking_info.get('call_id')}")
print(f"Token usage: {tracking_info.get('token_usage')}")
print(f"Raw content ID: {tracking_info.get('raw_content_id')}")
```

### 2. Duplicate Detection Logic

The system implements intelligent duplicate detection:

```python
def check_duplicate_processing(content_hash: str) -> Optional[Dict]:
    """Check if content has been processed with current prompt version"""
    prompt_version = get_prompt_version()  # From prompts.yaml
    prompt_config_hash = get_config_hash()  # Hash of entire prompts.yaml
    
    # Generate unique signature
    signature = generate_content_prompt_signature(content_hash, prompt_config_hash)
    
    # Check database
    existing = db.query("""
        SELECT * FROM letter_raw_content 
        WHERE content_prompt_signature = %s 
          AND prompt_version = %s 
          AND llm_processed = TRUE
    """, (signature, prompt_version))
    
    return existing[0] if existing else None
```

### 3. Token Usage Capture

Using the official xAI SDK to capture token usage:

```python
# Create chat using official SDK
chat = self.client.chat.create(model=self.model, temperature=0.1)
chat.append(system(system_prompt))
chat.append(user(user_prompt))

# Get response with usage data
response = chat.sample()

# Extract token usage from response.usage object
if hasattr(response, 'usage') and response.usage:
    usage_data = {
        'prompt_tokens': getattr(response.usage, 'prompt_tokens', None),
        'completion_tokens': getattr(response.usage, 'completion_tokens', None),
        'total_tokens': getattr(response.usage, 'total_tokens', None)
    }
    
    # Store in database with comprehensive metadata
    track_api_call(usage_data=usage_data, ...)
```

## 📊 Analytics and Monitoring

### 1. Token Usage Analytics View

```sql
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
```

### 2. Content Processing Analytics View

```sql
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
```

### 3. API Usage Monitoring

Get comprehensive analytics programmatically:

```python
# Get token usage analytics
analytics = enhanced_xai_service.get_token_usage_analytics(days=7)
print(f"Total calls: {analytics['analytics'][0]['total_calls']}")
print(f"Total tokens: {analytics['analytics'][0]['total_tokens']}")
print(f"Total cost: ${analytics['analytics'][0]['total_cost']:.4f}")

# Get content processing summary
summary = enhanced_xai_service.get_content_processing_summary()
print(f"Content records: {summary['content_summary'][0]['total_content']}")
print(f"Processed: {summary['content_summary'][0]['processed_count']}")
```

## 🔧 Configuration Management

### 1. Prompt Version Control

The system uses `prompts.yaml` for version control:

```yaml
# config/prompts.yaml
version: "2.2.0"
last_updated: "2025-01-14"
author: "Alexandre Huther"

prompts:
  unified_metadata_extraction:
    name: "Unified Metadata Extraction"
    version: "2.2.0"
    model: "grok-3-mini"
    system_prompt: |
      You are an expert document analyzer...
    user_prompt_template: |
      Analyze the following document...
```

### 2. Cost Estimation

The system includes cost tracking for budget management:

```python
# Cost calculation (update with actual xAI pricing)
def calculate_estimated_cost(total_tokens: int) -> float:
    cost_per_1k_tokens = 0.002  # $0.002 per 1K tokens (example)
    return (total_tokens / 1000) * cost_per_1k_tokens
```

## 🎯 Key Features

### 1. Comprehensive Tracking
- **Every API call** is tracked with unique UUID
- **Token usage** captured from official xAI SDK `response.usage` object
- **Performance metrics** including response time and confidence scores
- **Error handling** with retry counts and failure reasons

### 2. Intelligent Duplicate Detection
- **Content-based hashing** using SHA-256 for raw content
- **Prompt version awareness** - different prompts = different processing
- **Efficient caching** - avoid reprocessing identical content with same prompts
- **Configurable uniqueness** based on content + prompt configuration signature

### 3. Version Control Integration
- **Git commit tracking** for full reproducibility
- **Prompt version** from `prompts.yaml` for tracking prompt evolution
- **Configuration hashing** to detect config changes
- **Pipeline version** tracking for system evolution

### 4. Production Analytics
- **Cost tracking** for budget management and optimization
- **Performance monitoring** for response time analysis
- **Success rate tracking** for reliability metrics
- **Content quality assessment** for extraction optimization

## 🔍 Usage Examples

### 1. Basic Document Processing with Tracking

```python
from se_letters.services.postgresql_production_pipeline_service_stage1 import (
    PostgreSQLProductionPipelineServiceStage1
)

# Initialize pipeline with enhanced tracking
pipeline = PostgreSQLProductionPipelineServiceStage1()

# Process document
result = pipeline.process_document(
    file_path=Path("data/test/documents/Galaxy_6000_End_of_Life.doc"),
    request_type="PROCESS",
    request_metadata={"source": "api", "user": "analyst"}
)

# Check results with tracking information
print(f"Success: {result['success']}")
print(f"Products found: {result['products_found']}")
print(f"Letter ID: {result['letter_id']}")

# Token usage information
if 'tracking_metadata' in result:
    tracking = result['tracking_metadata']
    print(f"Call ID: {tracking['call_id']}")
    print(f"Token usage: {tracking['token_usage']}")
    print(f"Processing time: {tracking['processing_time_ms']}ms")
```

### 2. Analytics and Monitoring

```python
# Get comprehensive analytics
analytics = pipeline.get_processing_analytics()

# Token usage summary
token_data = analytics['token_usage']
print(f"Period: {analytics['analytics_period']}")
print(f"API calls: {token_data['analytics'][0]['total_calls']}")
print(f"Total tokens: {token_data['analytics'][0]['total_tokens']}")

# Content processing summary
content_data = analytics['content_processing']
for version_data in content_data['content_summary']:
    print(f"Prompt v{version_data['prompt_version']}: "
          f"{version_data['processed_count']} documents processed")

# Processing decisions breakdown
decisions = analytics['processing_decisions']
for decision in decisions:
    print(f"{decision['processing_decision']}: "
          f"{decision['decision_count']} times")
```

### 3. Duplicate Detection Summary

```python
# Get duplicate detection performance
summary = pipeline.get_duplicate_detection_summary()

print(f"Total documents: {summary['total_documents']}")
print(f"Duplicates found: {summary['duplicates_found']}")
print(f"Duplicate rate: {summary['duplicate_rate_percent']:.2f}%")
print(f"Success rate: {summary['success_rate_percent']:.2f}%")
print(f"Average confidence: {summary['avg_confidence']:.3f}")
```

## 🚀 Production Deployment

### 1. Database Migration

```bash
# Apply LLM tracking tables migration
psql -U ahuther -h localhost -d se_letters \
  -f scripts/migrations/create_llm_tracking_tables.sql
```

### 2. Configuration

Ensure proper environment variables:

```bash
export XAI_API_KEY="your_xai_api_key"
export DATABASE_URL="postgresql://ahuther@localhost:5432/se_letters"
```

### 3. Monitoring Setup

Create monitoring dashboard queries:

```sql
-- Daily token usage
SELECT 
    call_date,
    SUM(total_tokens) as daily_tokens,
    SUM(total_estimated_cost_usd) as daily_cost
FROM llm_token_usage_analytics
WHERE call_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY call_date
ORDER BY call_date;

-- Processing efficiency by prompt version
SELECT 
    prompt_version,
    processing_success_rate,
    avg_products_per_document,
    avg_grok_confidence
FROM content_processing_analytics
ORDER BY prompt_version DESC;
```

## 🔒 Security and Compliance

### 1. Data Protection
- **Raw content encryption** at rest (database level)
- **API key security** through environment variables
- **Audit trail** for all API calls and data access

### 2. Cost Control
- **Token usage monitoring** with alerts for unusual usage
- **Rate limiting** through API provider configuration
- **Budget tracking** with estimated cost calculations

### 3. Version Control
- **Git integration** for full reproducibility
- **Configuration versioning** through `prompts.yaml`
- **Schema migrations** with proper rollback capabilities

## 📈 Performance Optimization

### 1. Database Indexing
- **Optimized indexes** on frequently queried fields
- **Compound indexes** for analytics queries
- **Partitioning** consideration for large datasets

### 2. Caching Strategy
- **Content-based caching** to avoid duplicate processing
- **Response caching** for identical prompt + content combinations
- **Intelligent cache invalidation** based on prompt version changes

### 3. Monitoring and Alerting
- **Response time monitoring** for API performance
- **Error rate tracking** for reliability
- **Cost threshold alerts** for budget management

---

**Next Steps**: Implement monitoring dashboards, set up automated alerting, and establish regular analytics reporting for production optimization. 