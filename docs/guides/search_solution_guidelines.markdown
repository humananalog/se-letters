# State-of-the-Art Search Solution Guidelines for Schneider Electric Equipment

## Objective

Develop a robust search solution for a PostgreSQL database containing Schneider Electric equipment data extracted from obsolescence letters. The solution must handle vague descriptions, support range-based queries (e.g., voltage, power ratings), and return a comprehensive list of candidate products, including fuzzy matches.

## Prerequisites

- **Database Schema Review**: Before implementing the search solution, thoroughly review the PostgreSQL database schema to confirm the structure of the product data. Key tables and columns to identify include:
  - Product identifiers (e.g., `product_id`, `model_number`, `part_number`).
  - Descriptive fields (e.g., `product_name`, `description`, `category`).
  - Technical specifications (e.g., `voltage`, `power_rating`, `frequency`).
  - Obsolescence metadata (e.g., `obsolescence_status`, `letter_date`).
  - Ensure foreign key relationships and indexes are documented to optimize query performance.
- **PostgreSQL Version**: Verify the PostgreSQL version to ensure compatibility with extensions like `pg_trgm` and `pgvector`.
- **Data Quality**: Assess the data for inconsistencies (e.g., misspellings, incomplete descriptions) to determine preprocessing needs.

## Proposed Search Solution

The search solution combines three complementary techniques to handle vague descriptions and range-based queries:

### 1. Fuzzy Text Search with `pg_trgm`

- **Purpose**: Enable fuzzy matching for vague or misspelled product descriptions (e.g., "circuit breaker" vs. "circuit braker").
- **Implementation**:
  - Install the `pg_trgm` extension in PostgreSQL for trigram-based similarity search.
  - Create a GIN index on descriptive columns (e.g., `product_name`, `description`) to optimize fuzzy search performance.
  - Use the `similarity()` function or `%` operator to compute trigram similarity between user input and database entries.
  - Set a similarity threshold (e.g., 0.3) to balance precision and recall, adjustable based on testing.
- **Example Query**:

  ```sql
  SELECT product_id, product_name, description, similarity(product_name, 'circuit braker') AS sim_score
  FROM products
  WHERE product_name % 'circuit braker'
  ORDER BY sim_score DESC
  LIMIT 50;
  ```
- **Considerations**:
  - Preprocess user input to normalize case and remove special characters.
  - Test similarity thresholds to ensure relevant matches without excessive noise.

### 2. Vector-Based Semantic Search with `pgvector`

- **Purpose**: Capture semantic relationships in product descriptions (e.g., "breaker" and "switch" may be related) using embeddings.
- **Implementation**:
  - Install the `pgvector` extension to store and query vector embeddings.
  - Use a pre-trained language model (e.g., `sentence-transformers/all-MiniLM-L6-v2` via Hugging Face) to generate embeddings for product descriptions.
  - Store embeddings in a `vector` column in the products table.
  - Create an IVFFlat or HNSW index on the vector column to optimize nearest-neighbor searches.
  - Compute cosine similarity between the user query's embedding and stored embeddings to retrieve semantically similar products.
- **Example Query**:

  ```sql
  SELECT product_id, product_name, description
  FROM products
  ORDER BY embedding <=> (SELECT embedding FROM query_embeddings WHERE query = 'circuit breaker')
  LIMIT 50;
  ```
- **Considerations**:
  - Embeddings require preprocessing of descriptions to remove noise (e.g., boilerplate text from obsolescence letters).
  - Periodically update embeddings if product data changes.
  - Use a Python script with libraries like `sentence-transformers` and `psycopg2` to generate and store embeddings.

### 3. Range-Based Filtering for Specifications

- **Purpose**: Support queries involving numerical ranges (e.g., voltage between 200V and 400V).
- **Implementation**:
  - Identify numerical columns in the schema (e.g., `voltage`, `power_rating`) and ensure they are stored as appropriate data types (e.g., `NUMERIC` or `INTEGER`).
  - Create B-tree indexes on these columns for efficient range queries.
  - Allow users to specify ranges in queries, with fallback to default ranges if input is vague.
- **Example Query**:

  ```sql
  SELECT product_id, product_name, voltage
  FROM products
  WHERE voltage BETWEEN 200 AND 400
  AND power_rating >= 1000;
  ```
- **Considerations**:
  - Validate user-provided ranges to prevent SQL injection.
  - Handle missing or null values in specification fields with appropriate defaults.

### 4. Hybrid Search Approach

- **Purpose**: Combine fuzzy text search, semantic search, and range-based filtering for comprehensive results.
- **Implementation**:
  - Develop a scoring mechanism to rank candidates based on:
    - Fuzzy match similarity score (`pg_trgm`).
    - Semantic similarity score (`pgvector`).
    - Relevance of range-based matches (e.g., weight exact matches higher).
  - Use a weighted sum or machine learning model to combine scores, adjustable based on user feedback.
  - Return a ranked list of candidates, including metadata like `product_id`, `product_name`, `description`, and matched specifications.
- **Example Query**:

  ```sql
  SELECT 
      p.product_id, 
      p.product_name, 
      p.description, 
      p.voltage,
      similarity(p.product_name, 'circuit breaker') AS fuzzy_score,
      (p.embedding <=> (SELECT embedding FROM query_embeddings WHERE query = 'circuit breaker')) AS semantic_score
  FROM products p
  WHERE (p.product_name % 'circuit breaker' OR p.description % 'circuit breaker')
      AND p.voltage BETWEEN 200 AND 400
  ORDER BY (0.4 * similarity(p.product_name, 'circuit breaker') + 
            0.6 * (1 - (p.embedding <=> (SELECT embedding FROM query_embeddings WHERE query = 'circuit breaker')))) DESC
  LIMIT 50;
  ```
- **Considerations**:
  - Fine-tune weights for fuzzy and semantic scores based on testing.
  - Cache frequently searched queries to improve performance.

## Development Guidelines

- **Schema Confirmation**:
  - Review the database schema to map relevant tables and columns (e.g., `products`, `specifications`, `obsolescence_letters`).
  - Verify data types, indexes, and relationships to ensure compatibility with proposed queries.
- **Preprocessing**:
  - Clean product descriptions by removing boilerplate text, normalizing case, and handling special characters.
  - Extract and standardize numerical specifications from obsolescence letters.
- **Indexing**:
  - Create GIN indexes for `pg_trgm` on text columns.
  - Create IVFFlat or HNSW indexes for `pgvector` on embedding columns.
  - Create B-tree indexes for numerical columns used in range queries.
- **Performance Optimization**:
  - Use `EXPLAIN ANALYZE` to optimize query performance.
  - Implement pagination for large result sets (e.g., `LIMIT` and `OFFSET`).
  - Cache embeddings and frequent query results using PostgreSQL materialized views or an external cache like Redis.
- **Security**:
  - Use parameterized queries to prevent SQL injection.
  - Validate and sanitize user inputs, especially for range queries.
- **Testing**:
  - Test with a variety of vague descriptions (e.g., misspellings, synonyms) and range inputs.
  - Evaluate recall and precision of search results, adjusting similarity thresholds and score weights as needed.
- **Integration**:
  - Develop a Python-based API (e.g., using FastAPI or Flask) to interface with the PostgreSQL database.
  - Integrate with the existing `enhanced_product_mapping_service_v3.py` to ensure compatibility.
- **Dependencies**:
  - Install `pg_trgm` and `pgvector` extensions in PostgreSQL.
  - Use Python libraries: `psycopg2` for database connectivity, `sentence-transformers` for embeddings.
- **Documentation**:
  - Document the search API endpoints, query parameters, and response formats.
  - Provide examples of supported queries (e.g., vague text, ranges).

## Next Steps

1. Set up `pg_trgm` and `pgvector` extensions in the PostgreSQL environment.
2. Prototype the fuzzy and semantic search components using sample data.
3. Test range-based filtering with real-world queries from obsolescence letters pipeline
4. Integrate the hybrid search solution into the existing pipeline