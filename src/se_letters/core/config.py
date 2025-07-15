"""Configuration management for the SE Letters project."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import yaml
from dotenv import load_dotenv

from .exceptions import ConfigurationError


@dataclass
class APIConfig:
    """Configuration for API settings."""

    base_url: str
    model: str
    max_tokens: int = 4096
    temperature: float = 0.1
    timeout: int = 30
    api_key: Optional[str] = None


@dataclass
class DatabaseConfig:
    """Configuration for database settings."""
    
    product_database: str
    letter_database: str


@dataclass
class DataConfig:
    """Configuration for data paths and settings."""

    letters_directory: str
    json_directory: str
    temp_directory: str
    logs_directory: str
    database: DatabaseConfig
    excel_file: Optional[str] = None  # Legacy - backward compatibility
    excel_output: Optional[str] = None  # Legacy - backward compatibility
    supported_formats: List[str] = field(
        default_factory=lambda: [".pdf", ".docx", ".doc"]
    )
    cleanup_on_exit: bool = True


@dataclass
class ProcessingConfig:
    """Configuration for processing settings."""

    batch_size: int = 10
    max_workers: int = 4
    retry_attempts: int = 3
    retry_delay: float = 1.0


@dataclass
class EmbeddingConfig:
    """Configuration for embedding settings."""

    model_name: str = "all-MiniLM-L6-v2"
    vector_dimension: int = 384
    top_k_similar: int = 10
    similarity_threshold: float = 0.7


@dataclass
class FAISSConfig:
    """Configuration for FAISS settings."""

    index_type: str = "IndexFlatL2"
    index_file: str = "data/temp/faiss_index.bin"
    metadata_file: str = "data/temp/faiss_metadata.json"


@dataclass
class OCRConfig:
    """Configuration for OCR settings."""

    tesseract_config: str = "--oem 3 --psm 6"
    languages: List[str] = field(default_factory=lambda: ["eng"])
    dpi: int = 300


@dataclass
class LoggingConfig:
    """Configuration for logging settings."""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str = "logs/se_letters.log"
    max_bytes: int = 10485760  # 10MB
    backup_count: int = 5


@dataclass
class ValidationConfig:
    """Configuration for validation settings."""

    sample_size: int = 50
    confidence_threshold: float = 0.8
    manual_review_threshold: float = 0.6


@dataclass
class Config:
    """Main configuration class."""

    api: APIConfig
    data: DataConfig
    processing: ProcessingConfig
    embedding: EmbeddingConfig
    faiss: FAISSConfig
    ocr: OCRConfig
    logging: LoggingConfig
    validation: ValidationConfig

    @classmethod
    def from_yaml(cls, config_path: Path) -> "Config":
        """Load configuration from YAML file."""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
        except FileNotFoundError:
            raise ConfigurationError(
                f"Configuration file not found: {config_path}"
            )
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML configuration: {e}")

        try:
            # Prepare data config parameters
            data_config_params = {}
            
            # Get paths from data section
            if "input" in config_data["data"]:
                data_config_params.update(config_data["data"]["input"])
            if "output" in config_data["data"]:
                data_config_params.update(config_data["data"]["output"])
            if "temp" in config_data["data"]:
                data_config_params.update(config_data["data"]["temp"])
            
            # Add database configuration
            data_config_params["database"] = DatabaseConfig(
                **config_data["data"]["database"]
            )
            
            return cls(
                api=APIConfig(**config_data["api"]["xai"]),
                data=DataConfig(**data_config_params),
                processing=ProcessingConfig(**config_data["processing"]),
                embedding=EmbeddingConfig(**config_data["embedding"]),
                faiss=FAISSConfig(**config_data["faiss"]),
                ocr=OCRConfig(**config_data["ocr"]),
                logging=LoggingConfig(**config_data["logging"]),
                validation=ValidationConfig(**config_data["validation"]),
            )
        except KeyError as e:
            raise ConfigurationError(f"Missing configuration key: {e}")
        except TypeError as e:
            raise ConfigurationError(f"Invalid configuration value: {e}")

    def load_environment_variables(self) -> None:
        """Load environment variables and override config values."""
        # Load API key from environment
        self.api.api_key = os.getenv("XAI_API_KEY")
        if not self.api.api_key:
            msg = "XAI_API_KEY environment variable is required"
            raise ConfigurationError(msg)

        # Override other settings from environment if present
        if base_url := os.getenv("XAI_BASE_URL"):
            self.api.base_url = base_url
        if model := os.getenv("XAI_MODEL"):
            self.api.model = model
        if log_level := os.getenv("LOG_LEVEL"):
            self.logging.level = log_level

    def validate(self) -> None:
        """Validate configuration settings."""
        if not self.api.api_key:
            raise ConfigurationError("API key is required")
        
        if self.processing.batch_size <= 0:
            raise ConfigurationError("Batch size must be positive")
        
        if self.processing.max_workers <= 0:
            raise ConfigurationError("Max workers must be positive")
        
        if not (0 <= self.api.temperature <= 2):
            raise ConfigurationError("Temperature must be between 0 and 2")
        
        if not (0 <= self.embedding.similarity_threshold <= 1):
            msg = "Similarity threshold must be between 0 and 1"
            raise ConfigurationError(msg)


# Global configuration instance
_config: Optional[Config] = None


def get_config(config_path: Optional[Path] = None) -> Config:
    """Get the global configuration instance.
    
    Args:
        config_path: Path to configuration file. If None, uses default.
        
    Returns:
        Configuration instance.
        
    Raises:
        ConfigurationError: If configuration cannot be loaded.
    """
    global _config
    
    if _config is None:
        # Load environment variables first
        load_dotenv()
        
        # Use default config path if not provided
        if config_path is None:
            config_path = Path("config/config.yaml")
        
        # Load configuration
        _config = Config.from_yaml(config_path)
        _config.load_environment_variables()
        _config.validate()
    
    return _config


def reset_config() -> None:
    """Reset the global configuration instance (mainly for testing)."""
    global _config
    _config = None 