# Models Documentation

**Version: 2.2.0**  
**Author: Alexandre Huther**  
**Date: 2025-07-16**

## Overview

The models layer defines the data structures and schemas used throughout the SE Letters pipeline. All models are designed with type safety, validation, and serialization in mind, ensuring data integrity and consistency across the application.

## Core Data Models

### 1. Document Models (`document.py`)

#### 1.1 Document
**Purpose**: Represents a document being processed by the pipeline.

```python
@dataclass
class Document:
    """Represents a document in the processing pipeline."""
    
    # Core properties
    id: str
    file_path: Path
    file_name: str
    file_size: int
    file_type: str
    
    # Processing metadata
    upload_date: datetime
    processing_date: Optional[datetime] = None
    status: DocumentStatus = DocumentStatus.PENDING
    
    # Content
    text_content: Optional[str] = None
    extracted_text: Optional[str] = None
    page_count: Optional[int] = None
    
    # Validation
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)
    
    # Processing results
    confidence_score: Optional[float] = None
    processing_time: Optional[float] = None
```

**Key Features**:
- **Type Safety**: Full type hints for all properties
- **Validation**: Built-in validation for document properties
- **Serialization**: JSON serialization support
- **Status Tracking**: Document processing status management

#### 1.2 DocumentStatus
**Purpose**: Enumeration of document processing states.

```python
class DocumentStatus(Enum):
    """Document processing status enumeration."""
    
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    VALIDATED = "validated"
    EXTRACTED = "extracted"
    MATCHED = "matched"
```

#### 1.3 DocumentResult
**Purpose**: Result of document processing operations.

```python
@dataclass
class DocumentResult:
    """Result of document processing operation."""
    
    success: bool
    document: Optional[Document] = None
    error_message: Optional[str] = None
    processing_time: float = 0.0
    confidence_score: Optional[float] = None
    
    # Processing metadata
    extracted_text: Optional[str] = None
    page_count: Optional[int] = None
    ocr_used: bool = False
    
    # Validation results
    validation_errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
```

### 2. Letter Models (`letter.py`)

#### 2.1 Letter
**Purpose**: Represents an obsolescence letter with extracted metadata.

```python
@dataclass
class Letter:
    """Represents an obsolescence letter with extracted metadata."""
    
    # Core identification
    id: str
    document_id: str
    document_name: str
    
    # Processing metadata
    processing_date: datetime
    extraction_date: datetime
    confidence_score: float
    
    # Extracted metadata
    product_ranges: List[ProductRange]
    affected_products: List[AffectedProduct]
    business_impact: BusinessImpact
    
    # Document content
    summary: str
    key_points: List[str]
    recommendations: List[str]
    
    # Customer information
    customer_impact: CustomerImpact
    migration_guidance: MigrationGuidance
    
    # Technical details
    technical_specifications: TechnicalSpecifications
    service_information: ServiceInformation
    
    # Validation
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)
```

#### 2.2 ProductRange
**Purpose**: Represents a product range mentioned in the letter.

```python
@dataclass
class ProductRange:
    """Represents a product range from the letter."""
    
    name: str
    description: str
    brand: str
    business_unit: str
    
    # Product details
    device_type: Optional[str] = None
    voltage_level: Optional[str] = None
    current_rating: Optional[str] = None
    
    # Commercial status
    obsolescence_date: Optional[date] = None
    end_of_life_date: Optional[date] = None
    last_order_date: Optional[date] = None
    
    # Confidence
    confidence_score: float
    extraction_method: str
    
    # Validation
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)
```

#### 2.3 AffectedProduct
**Purpose**: Represents specific products affected by obsolescence.

```python
@dataclass
class AffectedProduct:
    """Represents a specific product affected by obsolescence."""
    
    product_id: str
    product_name: str
    product_description: str
    
    # Product specifications
    specifications: Dict[str, Any]
    technical_parameters: Dict[str, Any]
    
    # Commercial information
    commercial_status: str
    obsolescence_timeline: ObsolescenceTimeline
    
    # Service information
    service_availability: ServiceAvailability
    spare_parts_availability: SparePartsAvailability
    
    # Modernization
    modernization_paths: List[ModernizationPath]
    replacement_products: List[ReplacementProduct]
```

#### 2.4 BusinessImpact
**Purpose**: Represents the business impact of the obsolescence.

```python
@dataclass
class BusinessImpact:
    """Represents the business impact of product obsolescence."""
    
    impact_level: ImpactLevel
    affected_customers: int
    affected_installations: int
    
    # Financial impact
    revenue_impact: Optional[float] = None
    cost_impact: Optional[float] = None
    
    # Timeline
    immediate_impact: bool
    short_term_impact: bool
    long_term_impact: bool
    
    # Risk assessment
    risk_level: RiskLevel
    mitigation_strategies: List[str]
```

### 3. Product Models (`product.py`)

#### 3.1 Product
**Purpose**: Represents a product from the IBcatalogue database.

```python
@dataclass
class Product:
    """Represents a product from the IBcatalogue database."""
    
    # Core identification
    product_id: str
    product_name: str
    product_description: str
    
    # Classification
    range_name: str
    subrange_name: Optional[str] = None
    device_type: str
    brand: str
    business_unit: str
    
    # Technical specifications
    voltage_level: Optional[str] = None
    current_rating: Optional[str] = None
    power_rating: Optional[str] = None
    frequency: Optional[str] = None
    
    # Commercial status
    commercial_status: CommercialStatus
    production_status: ProductionStatus
    service_status: ServiceStatus
    
    # Dates
    production_start_date: Optional[date] = None
    production_end_date: Optional[date] = None
    commercialization_start_date: Optional[date] = None
    commercialization_end_date: Optional[date] = None
    service_start_date: Optional[date] = None
    service_end_date: Optional[date] = None
    
    # Service information
    serviceable: bool
    traceable: bool
    spare_parts_available: bool
    
    # Modernization
    modernization_paths: List[ModernizationPath]
    replacement_products: List[ReplacementProduct]
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    version: str
```

#### 3.2 CommercialStatus
**Purpose**: Enumeration of product commercial statuses.

```python
class CommercialStatus(Enum):
    """Product commercial status enumeration."""
    
    ACTIVE = "active"
    OBSOLETE = "obsolete"
    DISCONTINUED = "discontinued"
    END_OF_LIFE = "end_of_life"
    PHASE_OUT = "phase_out"
    LIMITED_AVAILABILITY = "limited_availability"
```

#### 3.3 ModernizationPath
**Purpose**: Represents a modernization path for obsolete products.

```python
@dataclass
class ModernizationPath:
    """Represents a modernization path for obsolete products."""
    
    path_id: str
    source_product_id: str
    target_product_id: str
    
    # Path details
    path_type: ModernizationType
    complexity: ComplexityLevel
    estimated_cost: Optional[float] = None
    estimated_time: Optional[str] = None
    
    # Benefits
    benefits: List[str]
    improvements: List[str]
    
    # Requirements
    requirements: List[str]
    prerequisites: List[str]
    
    # Validation
    is_valid: bool = True
    confidence_score: float = 1.0
```

### 4. Product Matching Models (`product_matching.py`)

#### 4.1 ProductMatch
**Purpose**: Represents a match between letter content and products.

```python
@dataclass
class ProductMatch:
    """Represents a match between letter content and products."""
    
    # Match identification
    match_id: str
    letter_id: str
    product_id: str
    
    # Match details
    match_type: MatchType
    confidence_score: float
    similarity_score: float
    
    # Matching criteria
    matching_criteria: List[MatchingCriterion]
    matched_fields: Dict[str, Any]
    
    # Validation
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)
    
    # Business context
    business_relevance: float
    customer_impact: CustomerImpact
```

#### 4.2 MatchType
**Purpose**: Enumeration of product matching types.

```python
class MatchType(Enum):
    """Product matching type enumeration."""
    
    EXACT = "exact"
    SEMANTIC = "semantic"
    RANGE_BASED = "range_based"
    FUZZY = "fuzzy"
    AI_GENERATED = "ai_generated"
    MANUAL = "manual"
```

#### 4.3 MatchingCriterion
**Purpose**: Represents a specific matching criterion.

```python
@dataclass
class MatchingCriterion:
    """Represents a specific matching criterion."""
    
    criterion_type: CriterionType
    field_name: str
    field_value: Any
    weight: float
    confidence: float
    
    # Validation
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)
```

## Data Validation

### 1. Pydantic Integration
All models use Pydantic for validation:

```python
from pydantic import BaseModel, Field, validator

class DocumentModel(BaseModel):
    """Pydantic model for document validation."""
    
    id: str = Field(..., description="Unique document identifier")
    file_name: str = Field(..., min_length=1, max_length=255)
    file_size: int = Field(..., gt=0)
    file_type: str = Field(..., regex=r'^\.(pdf|docx|doc)$')
    
    @validator('file_size')
    def validate_file_size(cls, v):
        if v > 100 * 1024 * 1024:  # 100MB limit
            raise ValueError('File size exceeds maximum limit')
        return v
    
    class Config:
        extra = "forbid"
        validate_assignment = True
```

### 2. Custom Validators
Custom validation logic for business rules:

```python
@dataclass
class Letter:
    # ... other fields ...
    
    def validate(self) -> ValidationResult:
        """Validate letter data against business rules."""
        errors = []
        
        # Validate product ranges
        if not self.product_ranges:
            errors.append("At least one product range must be specified")
        
        # Validate confidence score
        if not 0.0 <= self.confidence_score <= 1.0:
            errors.append("Confidence score must be between 0.0 and 1.0")
        
        # Validate dates
        if self.processing_date > datetime.now():
            errors.append("Processing date cannot be in the future")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
```

### 3. Schema Validation
JSON schema validation for API endpoints:

```python
from pydantic import BaseModel

class LetterCreateRequest(BaseModel):
    """Request model for creating a new letter."""
    
    document_id: str
    document_name: str
    product_ranges: List[ProductRangeCreate]
    business_impact: BusinessImpactCreate
    
    class Config:
        schema_extra = {
            "example": {
                "document_id": "doc_123",
                "document_name": "PIX2B_Phase_out_Letter.pdf",
                "product_ranges": [
                    {
                        "name": "PIX Double Bus Bar",
                        "description": "Medium voltage switchgear",
                        "brand": "Schneider Electric"
                    }
                ]
            }
        }
```

## Serialization and Deserialization

### 1. JSON Serialization
All models support JSON serialization:

```python
import json
from dataclasses import asdict

class Letter:
    # ... fields ...
    
    def to_json(self) -> str:
        """Serialize letter to JSON string."""
        return json.dumps(asdict(self), default=str, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Letter':
        """Deserialize letter from JSON string."""
        data = json.loads(json_str)
        return cls(**data)
```

### 2. Database Serialization
Database-specific serialization for storage:

```python
class Letter:
    # ... fields ...
    
    def to_database_dict(self) -> Dict[str, Any]:
        """Convert to database-compatible dictionary."""
        return {
            'id': self.id,
            'document_id': self.document_id,
            'document_name': self.document_name,
            'processing_date': self.processing_date.isoformat(),
            'confidence_score': self.confidence_score,
            'product_ranges': json.dumps([pr.to_dict() for pr in self.product_ranges]),
            'business_impact': json.dumps(self.business_impact.to_dict()),
            'created_at': datetime.now().isoformat()
        }
    
    @classmethod
    def from_database_dict(cls, data: Dict[str, Any]) -> 'Letter':
        """Create letter from database dictionary."""
        return cls(
            id=data['id'],
            document_id=data['document_id'],
            document_name=data['document_name'],
            processing_date=datetime.fromisoformat(data['processing_date']),
            confidence_score=data['confidence_score'],
            product_ranges=[ProductRange.from_dict(pr) for pr in json.loads(data['product_ranges'])],
            business_impact=BusinessImpact.from_dict(json.loads(data['business_impact']))
        )
```

## Type Safety

### 1. Type Hints
Comprehensive type hints for all models:

```python
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
from pathlib import Path

@dataclass
class Document:
    id: str
    file_path: Path
    file_name: str
    file_size: int
    file_type: str
    upload_date: datetime
    processing_date: Optional[datetime] = None
    status: DocumentStatus = DocumentStatus.PENDING
    text_content: Optional[str] = None
    confidence_score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### 2. Generic Types
Generic types for reusable components:

```python
from typing import Generic, TypeVar, List

T = TypeVar('T')

@dataclass
class PaginatedResult(Generic[T]):
    """Generic paginated result container."""
    
    items: List[T]
    total_count: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool

@dataclass
class SearchResult(Generic[T]):
    """Generic search result container."""
    
    items: List[T]
    query: str
    total_count: int
    search_time: float
    confidence_threshold: float
```

## Performance Considerations

### 1. Lazy Loading
Lazy loading for large data structures:

```python
from typing import Optional
from functools import cached_property

class Letter:
    # ... other fields ...
    
    @cached_property
    def product_count(self) -> int:
        """Lazy load product count."""
        return len(self.affected_products)
    
    @cached_property
    def total_impact_score(self) -> float:
        """Lazy load calculated impact score."""
        return sum(product.impact_score for product in self.affected_products)
```

### 2. Memory Optimization
Memory-efficient data structures:

```python
from dataclasses import field
from typing import List

@dataclass
class ProductDatabase:
    """Memory-efficient product database."""
    
    products: Dict[str, Product] = field(default_factory=dict)
    index: Dict[str, List[str]] = field(default_factory=dict)
    
    def add_product(self, product: Product) -> None:
        """Add product with indexing."""
        self.products[product.product_id] = product
        
        # Index by range name for fast lookup
        if product.range_name not in self.index:
            self.index[product.range_name] = []
        self.index[product.range_name].append(product.product_id)
```

### 3. Immutable Data
Immutable data structures where appropriate:

```python
from dataclasses import dataclass, frozen=True

@frozen
class ProductIdentifier:
    """Immutable product identifier."""
    
    product_id: str
    range_name: str
    brand: str
    business_unit: str
```

## Testing Support

### 1. Factory Methods
Factory methods for test data creation:

```python
class DocumentFactory:
    """Factory for creating test documents."""
    
    @staticmethod
    def create_test_document(
        file_name: str = "test_document.pdf",
        file_size: int = 1024,
        status: DocumentStatus = DocumentStatus.PENDING
    ) -> Document:
        """Create a test document with default values."""
        return Document(
            id=f"doc_{uuid.uuid4().hex[:8]}",
            file_path=Path(f"/tmp/{file_name}"),
            file_name=file_name,
            file_size=file_size,
            file_type=".pdf",
            upload_date=datetime.now(),
            status=status
        )
    
    @staticmethod
    def create_processed_document() -> Document:
        """Create a processed test document."""
        return DocumentFactory.create_test_document(
            status=DocumentStatus.COMPLETED,
            text_content="This is test content for processing.",
            confidence_score=0.95
        )
```

### 2. Mock Data
Mock data generators for testing:

```python
class MockDataGenerator:
    """Generate mock data for testing."""
    
    @staticmethod
    def generate_product_ranges(count: int = 5) -> List[ProductRange]:
        """Generate mock product ranges."""
        ranges = []
        for i in range(count):
            ranges.append(ProductRange(
                name=f"Test Range {i+1}",
                description=f"Test range description {i+1}",
                brand="Schneider Electric",
                business_unit="Power Systems",
                confidence_score=0.9 + (i * 0.02)
            ))
        return ranges
    
    @staticmethod
    def generate_products(count: int = 10) -> List[Product]:
        """Generate mock products."""
        products = []
        for i in range(count):
            products.append(Product(
                product_id=f"PROD_{i+1:06d}",
                product_name=f"Test Product {i+1}",
                product_description=f"Test product description {i+1}",
                range_name=f"Test Range {(i % 5) + 1}",
                device_type="Circuit Breaker",
                brand="Schneider Electric",
                business_unit="Power Systems",
                commercial_status=CommercialStatus.ACTIVE,
                production_status=ProductionStatus.ACTIVE,
                service_status=ServiceStatus.ACTIVE,
                serviceable=True,
                traceable=True,
                spare_parts_available=True,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                version="2.2.0"
            ))
        return products
```

## Future Enhancements

### 1. GraphQL Integration
- **Schema Definition**: GraphQL schema for models
- **Resolver Implementation**: Data fetching resolvers
- **Type Generation**: Automatic TypeScript type generation
- **Real-time Updates**: Subscription support

### 2. Advanced Validation
- **Cross-field Validation**: Complex validation rules
- **Business Rule Engine**: Configurable business rules
- **Validation Caching**: Performance optimization
- **Custom Validators**: Domain-specific validation

### 3. Data Versioning
- **Model Versioning**: Schema evolution support
- **Migration Tools**: Automatic data migration
- **Backward Compatibility**: Version compatibility
- **Audit Trail**: Change tracking and history

## Conclusion

The models layer provides a robust, type-safe, and performant foundation for data management in the SE Letters pipeline. The comprehensive validation, serialization, and testing support ensure data integrity and maintainability across the application. 