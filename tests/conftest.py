"""Pytest configuration and fixtures for the SE Letters project."""

import pytest
from unittest.mock import Mock

from se_letters.core.config import Config, reset_config
from se_letters.models.document import Document
from se_letters.models.letter import Letter, LetterMetadata
from se_letters.models.product import Product, ProductRange


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for tests."""
    return tmp_path


@pytest.fixture
def sample_config(temp_dir):
    """Create a sample configuration for testing."""
    config = Config(
        api=Mock(
            base_url="https://api.test.com",
            model="test-model",
            api_key="test-key",
            max_tokens=1000,
            temperature=0.1,
            timeout=30,
        ),
        data=Mock(
            letters_directory=str(temp_dir / "letters"),
            excel_file=str(temp_dir / "products.xlsx"),
            json_directory=str(temp_dir / "json"),
            excel_output=str(temp_dir / "output.xlsx"),
            temp_directory=str(temp_dir / "temp"),
            logs_directory=str(temp_dir / "logs"),
            supported_formats=[".pdf", ".docx", ".doc"],
            cleanup_on_exit=True,
        ),
        processing=Mock(
            batch_size=5,
            max_workers=2,
            retry_attempts=3,
            retry_delay=1.0,
        ),
        embedding=Mock(
            model_name="test-model",
            vector_dimension=384,
            top_k_similar=10,
            similarity_threshold=0.7,
        ),
        faiss=Mock(
            index_type="IndexFlatL2",
            index_file=str(temp_dir / "index.bin"),
            metadata_file=str(temp_dir / "metadata.json"),
        ),
        ocr=Mock(
            tesseract_config="--oem 3 --psm 6",
            languages=["eng"],
            dpi=300,
        ),
        logging=Mock(
            level="DEBUG",
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            file=str(temp_dir / "test.log"),
            max_bytes=1024000,
            backup_count=3,
        ),
        validation=Mock(
            sample_size=10,
            confidence_threshold=0.8,
            manual_review_threshold=0.6,
        ),
    )
    return config


@pytest.fixture
def sample_document(temp_dir):
    """Create a sample document for testing."""
    file_path = temp_dir / "test_document.pdf"
    file_path.write_text("Test document content")
    
    return Document.from_file(
        file_path=file_path,
        text="This is a test document about product obsolescence.",
        processing_time=1.5,
        metadata={"pages": 1, "format": "pdf"},
    )


@pytest.fixture
def sample_letter_metadata():
    """Create sample letter metadata for testing."""
    return LetterMetadata(
        letter_id="TEST-001",
        ranges=["XYZ-100", "ABC-200"],
        withdrawal_date=None,
        end_of_commercialization=None,
        end_of_services=None,
        modernization_path="Upgrade to new series",
        confidence_score=0.85,
        processing_notes=["High confidence extraction"],
    )


@pytest.fixture
def sample_letter(sample_document, sample_letter_metadata):
    """Create a sample letter for testing."""
    return Letter(
        document=sample_document,
        metadata=sample_letter_metadata,
        similar_ranges=["XYZ-100", "ABC-200", "DEF-300"],
    )


@pytest.fixture
def sample_product_range():
    """Create a sample product range for testing."""
    return ProductRange(
        range_name="XYZ",
        subrange="100",
        description="Test product range",
        metadata={"category": "electrical"},
    )


@pytest.fixture
def sample_product():
    """Create a sample product for testing."""
    return Product(
        range_name="XYZ",
        subrange="100",
        model="A1",
        description="Test product",
        metadata={"category": "electrical"},
        letter_id="TEST-001",
    )


@pytest.fixture
def mock_xai_response():
    """Mock xAI API response for testing."""
    return {
        "letter_id": "TEST-001",
        "ranges": ["XYZ-100", "ABC-200"],
        "withdrawal_date": "2024-12-31",
        "end_of_commercialization": "2025-06-30",
        "end_of_services": "2026-12-31",
        "modernization_path": "Upgrade to EcoFit series",
        "confidence_score": 0.9,
    }


@pytest.fixture(autouse=True)
def reset_global_config():
    """Reset global configuration after each test."""
    yield
    reset_config()


@pytest.fixture
def sample_excel_data():
    """Create sample Excel data for testing."""
    return [
        {
            "Range": "XYZ",
            "Subrange": "100",
            "Model": "A1",
            "Description": "Test product A1",
        },
        {
            "Range": "XYZ",
            "Subrange": "100",
            "Model": "A2",
            "Description": "Test product A2",
        },
        {
            "Range": "ABC",
            "Subrange": "200",
            "Model": "B1",
            "Description": "Test product B1",
        },
    ] 