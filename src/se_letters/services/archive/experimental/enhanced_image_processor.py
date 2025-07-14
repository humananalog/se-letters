"""Enhanced Image Processor for SE Letters Pipeline.

This module provides comprehensive image extraction and OCR processing
specifically designed for Schneider Electric obsolescence letters that
contain embedded modernization path tables and diagrams.
"""

import base64
import io
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import re

# Third-party imports
try:
    import pytesseract
    from PIL import Image, ImageEnhance, ImageFilter
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

try:
    from docx import Document as DocxDocument
    from docx.document import Document as DocxDoc
    from docx.oxml.table import CT_Tbl
    from docx.oxml.text.paragraph import CT_P
    from docx.table import _Cell, Table
    from docx.text.paragraph import Paragraph
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

from ..utils.logger import get_logger
from ..core.exceptions import FileProcessingError

logger = get_logger(__name__)


class ModernizationPathExtractor:
    """Specialized extractor for modernization path tables and diagrams."""
    
    def __init__(self):
        self.table_keywords = [
            "modernization", "replacement", "migration", "upgrade",
            "obsolete", "new", "current", "recommended", "alternative",
            "part number", "reference", "catalog", "equivalent"
        ]
        
        self.diagram_keywords = [
            "path", "flow", "diagram", "chart", "roadmap", "timeline",
            "lifecycle", "transition", "evolution", "mapping"
        ]
        
        # OCR configuration for table extraction
        self.ocr_config = {
            'table': r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz |-.,()[]/',
            'diagram': r'--oem 3 --psm 11 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz |-.,()[]→←↓↑',
            'general': r'--oem 3 --psm 6'
        }

    def extract_modernization_content(self, text: str, confidence: float = 0.7) -> Dict[str, Any]:
        """Extract and structure modernization path information from OCR text.
        
        Args:
            text: OCR extracted text.
            confidence: Minimum confidence threshold.
            
        Returns:
            Structured modernization path data.
        """
        result = {
            "modernization_paths": [],
            "product_mappings": [],
            "replacement_tables": [],
            "confidence": confidence,
            "extraction_method": "ocr_table_analysis"
        }
        
        # Extract product mappings (old -> new)
        mappings = self._extract_product_mappings(text)
        result["product_mappings"] = mappings
        
        # Extract structured tables
        tables = self._extract_table_structures(text)
        result["replacement_tables"] = tables
        
        # Extract modernization paths
        paths = self._extract_modernization_paths(text)
        result["modernization_paths"] = paths
        
        return result
    
    def _extract_product_mappings(self, text: str) -> List[Dict[str, str]]:
        """Extract product code mappings from text."""
        mappings = []
        
        # Pattern for product code mappings
        patterns = [
            r'(\w+\d+\w*)\s*[-→→]\s*(\w+\d+\w*)',  # LC1D09 → LC1D09BD
            r'(\w+\d+\w*)\s+replaced\s+by\s+(\w+\d+\w*)',  # LC1D09 replaced by LC1D09BD
            r'(\w+\d+\w*)\s*\|\s*(\w+\d+\w*)',  # LC1D09 | LC1D09BD
            r'Old:\s*(\w+\d+\w*)\s*New:\s*(\w+\d+\w*)',  # Old: LC1D09 New: LC1D09BD
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for old_code, new_code in matches:
                mappings.append({
                    "obsolete_code": old_code.strip(),
                    "replacement_code": new_code.strip(),
                    "mapping_type": "direct_replacement"
                })
        
        return mappings
    
    def _extract_table_structures(self, text: str) -> List[Dict[str, Any]]:
        """Extract table-like structures from OCR text."""
        tables = []
        
        # Split text into potential table rows
        lines = text.split('\n')
        current_table = []
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_table:
                    # Process completed table
                    table_data = self._process_table_rows(current_table)
                    if table_data:
                        tables.append(table_data)
                    current_table = []
                continue
            
            # Check if line looks like a table row (contains separators)
            if any(sep in line for sep in ['|', '\t', '  ']):
                current_table.append(line)
        
        # Process final table if exists
        if current_table:
            table_data = self._process_table_rows(current_table)
            if table_data:
                tables.append(table_data)
        
        return tables
    
    def _process_table_rows(self, rows: List[str]) -> Optional[Dict[str, Any]]:
        """Process table rows into structured data."""
        if len(rows) < 2:  # Need at least header and one data row
            return None
        
        # Detect separator
        separator = '|' if '|' in rows[0] else '\t' if '\t' in rows[0] else '  '
        
        # Parse header
        header = [col.strip() for col in rows[0].split(separator)]
        
        # Parse data rows
        data_rows = []
        for row in rows[1:]:
            cols = [col.strip() for col in row.split(separator)]
            if len(cols) == len(header):
                row_data = dict(zip(header, cols))
                data_rows.append(row_data)
        
        if not data_rows:
            return None
        
        # Determine table type
        table_type = self._classify_table_type(header, data_rows)
        
        return {
            "type": table_type,
            "headers": header,
            "rows": data_rows,
            "row_count": len(data_rows),
            "column_count": len(header)
        }
    
    def _classify_table_type(self, headers: List[str], rows: List[Dict[str, str]]) -> str:
        """Classify the type of table based on headers and content."""
        header_text = ' '.join(headers).lower()
        
        if any(keyword in header_text for keyword in ['obsolete', 'replacement', 'new', 'old']):
            return "replacement_table"
        elif any(keyword in header_text for keyword in ['modernization', 'migration', 'upgrade']):
            return "modernization_table"
        elif any(keyword in header_text for keyword in ['part', 'reference', 'catalog']):
            return "product_catalog_table"
        else:
            return "general_table"
    
    def _extract_modernization_paths(self, text: str) -> List[Dict[str, Any]]:
        """Extract modernization path information."""
        paths = []
        
        # Look for path descriptions
        path_patterns = [
            r'(\w+\s+\w+)\s+→\s+(\w+\s+\w+)\s+→\s+(\w+\s+\w+)',  # Multi-step path
            r'(\w+\s+\w+)\s+→\s+(\w+\s+\w+)',  # Single-step path
            r'migrate\s+from\s+(\w+\s+\w+)\s+to\s+(\w+\s+\w+)',  # Migration description
        ]
        
        for pattern in path_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match) == 3:  # Multi-step
                    paths.append({
                        "type": "multi_step",
                        "steps": [match[0], match[1], match[2]],
                        "description": f"Migration path: {match[0]} → {match[1]} → {match[2]}"
                    })
                elif len(match) == 2:  # Single-step
                    paths.append({
                        "type": "single_step",
                        "from": match[0],
                        "to": match[1],
                        "description": f"Migration path: {match[0]} → {match[1]}"
                    })
        
        return paths


class EnhancedImageProcessor:
    """Enhanced image processor for embedded images in Word documents."""
    
    def __init__(self):
        self.modernization_extractor = ModernizationPathExtractor()
        self.temp_dir = Path(tempfile.gettempdir()) / "se_letters_images"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Image processing settings
        self.image_settings = {
            "min_width": 100,
            "min_height": 100,
            "max_size": (2000, 2000),
            "enhance_contrast": True,
            "denoise": True,
            "sharpen": True
        }
    
    def extract_embedded_images(self, file_path: Path) -> Dict[str, Any]:
        """Extract embedded images from Word document with OCR processing.
        
        Args:
            file_path: Path to Word document.
            
        Returns:
            Dictionary with extracted images and OCR results.
        """
        if not DOCX_AVAILABLE:
            raise FileProcessingError("python-docx not available for image extraction")
        
        if not OCR_AVAILABLE:
            raise FileProcessingError("OCR dependencies not available")
        
        result = {
            "total_images": 0,
            "processed_images": 0,
            "modernization_content": [],
            "image_details": [],
            "extraction_errors": []
        }
        
        try:
            # Extract images from DOCX
            images = self._extract_docx_images(file_path)
            result["total_images"] = len(images)
            
            # Process each image
            for i, image_data in enumerate(images):
                try:
                    processed = self._process_image_with_ocr(image_data, f"image_{i}")
                    result["image_details"].append(processed)
                    result["processed_images"] += 1
                    
                    # Extract modernization content if detected
                    if processed.get("contains_modernization_content"):
                        modernization_data = self.modernization_extractor.extract_modernization_content(
                            processed["ocr_text"], 
                            processed["ocr_confidence"]
                        )
                        result["modernization_content"].append(modernization_data)
                        
                except Exception as e:
                    error_msg = f"Failed to process image {i}: {e}"
                    result["extraction_errors"].append(error_msg)
                    logger.warning(error_msg)
            
            return result
            
        except Exception as e:
            raise FileProcessingError(f"Image extraction failed: {e}")
    
    def _extract_docx_images(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract images from DOCX file.
        
        Args:
            file_path: Path to DOCX file.
            
        Returns:
            List of image data dictionaries.
        """
        images = []
        
        try:
            # Open DOCX as ZIP file to access images
            with zipfile.ZipFile(file_path, 'r') as docx_zip:
                # Find image files in the media folder
                image_files = [f for f in docx_zip.namelist() if f.startswith('word/media/')]
                
                for img_file in image_files:
                    try:
                        # Extract image data
                        img_data = docx_zip.read(img_file)
                        
                        # Create PIL Image
                        img = Image.open(io.BytesIO(img_data))
                        
                        # Get image info
                        img_info = {
                            "filename": img_file,
                            "format": img.format,
                            "size": img.size,
                            "mode": img.mode,
                            "image_data": img_data,
                            "pil_image": img
                        }
                        
                        # Filter out very small images (likely decorative)
                        if (img.width >= self.image_settings["min_width"] and 
                            img.height >= self.image_settings["min_height"]):
                            images.append(img_info)
                            
                    except Exception as e:
                        logger.warning(f"Failed to process image {img_file}: {e}")
                        continue
            
            # Also try to extract images using python-docx relationships
            doc = DocxDocument(file_path)
            docx_images = self._extract_docx_relationship_images(doc)
            
            # Merge results (avoid duplicates)
            existing_sizes = [(img["size"]) for img in images]
            for docx_img in docx_images:
                if docx_img["size"] not in existing_sizes:
                    images.append(docx_img)
            
            logger.info(f"Extracted {len(images)} images from {file_path.name}")
            return images
            
        except Exception as e:
            logger.error(f"Failed to extract images from {file_path}: {e}")
            return []
    
    def _extract_docx_relationship_images(self, doc: DocxDoc) -> List[Dict[str, Any]]:
        """Extract images using python-docx relationships.
        
        Args:
            doc: python-docx Document object.
            
        Returns:
            List of image data dictionaries.
        """
        images = []
        
        try:
            # Access document relationships
            for rel in doc.part.rels.values():
                if "image" in rel.target_ref:
                    try:
                        # Get image data
                        img_data = rel.target_part.blob
                        
                        # Create PIL Image
                        img = Image.open(io.BytesIO(img_data))
                        
                        img_info = {
                            "filename": rel.target_ref,
                            "format": img.format,
                            "size": img.size,
                            "mode": img.mode,
                            "image_data": img_data,
                            "pil_image": img,
                            "relationship_id": rel.rId
                        }
                        
                        # Filter out small images
                        if (img.width >= self.image_settings["min_width"] and 
                            img.height >= self.image_settings["min_height"]):
                            images.append(img_info)
                            
                    except Exception as e:
                        logger.warning(f"Failed to process relationship image {rel.target_ref}: {e}")
                        continue
            
            return images
            
        except Exception as e:
            logger.warning(f"Failed to extract images via relationships: {e}")
            return []
    
    def _process_image_with_ocr(self, image_data: Dict[str, Any], image_id: str) -> Dict[str, Any]:
        """Process image with OCR and content analysis.
        
        Args:
            image_data: Image data dictionary.
            image_id: Unique image identifier.
            
        Returns:
            Processed image results.
        """
        result = {
            "image_id": image_id,
            "filename": image_data["filename"],
            "original_size": image_data["size"],
            "format": image_data["format"],
            "ocr_text": "",
            "ocr_confidence": 0.0,
            "contains_modernization_content": False,
            "processing_method": "enhanced_ocr",
            "image_type": "unknown"
        }
        
        try:
            # Get PIL image
            img = image_data["pil_image"]
            
            # Enhance image for better OCR
            enhanced_img = self._enhance_image_for_ocr(img)
            
            # Classify image type
            image_type = self._classify_image_type(enhanced_img)
            result["image_type"] = image_type
            
            # Choose OCR configuration based on image type
            if image_type == "table":
                ocr_config = self.modernization_extractor.ocr_config["table"]
            elif image_type == "diagram":
                ocr_config = self.modernization_extractor.ocr_config["diagram"]
            else:
                ocr_config = self.modernization_extractor.ocr_config["general"]
            
            # Perform OCR
            ocr_result = pytesseract.image_to_data(
                enhanced_img, 
                config=ocr_config,
                output_type=pytesseract.Output.DICT
            )
            
            # Extract text and calculate confidence
            words = []
            confidences = []
            
            for i, word in enumerate(ocr_result['text']):
                if word.strip():
                    words.append(word)
                    confidences.append(ocr_result['conf'][i])
            
            result["ocr_text"] = ' '.join(words)
            result["ocr_confidence"] = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Check for modernization content
            result["contains_modernization_content"] = self._contains_modernization_content(result["ocr_text"])
            
            # Save processed image for debugging
            if logger.level <= 10:  # DEBUG level
                debug_path = self.temp_dir / f"{image_id}_enhanced.png"
                enhanced_img.save(debug_path)
                result["debug_image_path"] = str(debug_path)
            
            logger.info(f"OCR processed {image_id}: {len(words)} words, {result['ocr_confidence']:.1f}% confidence")
            
            return result
            
        except Exception as e:
            result["processing_error"] = str(e)
            logger.error(f"OCR processing failed for {image_id}: {e}")
            return result
    
    def _enhance_image_for_ocr(self, img: Image.Image) -> Image.Image:
        """Enhance image for better OCR results.
        
        Args:
            img: PIL Image object.
            
        Returns:
            Enhanced PIL Image.
        """
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize if too large
        if img.size[0] > self.image_settings["max_size"][0] or img.size[1] > self.image_settings["max_size"][1]:
            img.thumbnail(self.image_settings["max_size"], Image.Resampling.LANCZOS)
        
        # Enhance contrast
        if self.image_settings["enhance_contrast"]:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.5)
        
        # Sharpen
        if self.image_settings["sharpen"]:
            img = img.filter(ImageFilter.SHARPEN)
        
        # Convert to grayscale for OCR
        img = img.convert('L')
        
        # Additional enhancement with OpenCV if available
        if CV2_AVAILABLE:
            img = self._opencv_enhance(img)
        
        return img
    
    def _opencv_enhance(self, img: Image.Image) -> Image.Image:
        """Additional image enhancement using OpenCV.
        
        Args:
            img: PIL Image object.
            
        Returns:
            Enhanced PIL Image.
        """
        try:
            # Convert PIL to OpenCV
            cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            
            # Denoise
            cv_img = cv2.fastNlMeansDenoising(cv_img)
            
            # Adaptive threshold for better text detection
            cv_img = cv2.adaptiveThreshold(
                cv_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Convert back to PIL
            return Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))
            
        except Exception as e:
            logger.warning(f"OpenCV enhancement failed: {e}")
            return img
    
    def _classify_image_type(self, img: Image.Image) -> str:
        """Classify image type based on visual characteristics.
        
        Args:
            img: PIL Image object.
            
        Returns:
            Image type string.
        """
        width, height = img.size
        aspect_ratio = width / height
        
        # Basic classification based on aspect ratio and size
        if aspect_ratio > 2.0:  # Wide images are likely tables
            return "table"
        elif 0.5 < aspect_ratio < 2.0 and width > 300 and height > 300:  # Square-ish larger images
            return "diagram"
        elif aspect_ratio < 0.5:  # Tall images
            return "list"
        else:
            return "general"
    
    def _contains_modernization_content(self, text: str) -> bool:
        """Check if text contains modernization-related content.
        
        Args:
            text: OCR extracted text.
            
        Returns:
            True if modernization content is detected.
        """
        text_lower = text.lower()
        
        # Check for modernization keywords
        modernization_keywords = self.modernization_extractor.table_keywords + self.modernization_extractor.diagram_keywords
        
        keyword_count = sum(1 for keyword in modernization_keywords if keyword in text_lower)
        
        # Check for product codes (pattern matching)
        product_code_pattern = r'\b[A-Z]{2,4}\d{1,4}[A-Z]*\b'
        product_codes = re.findall(product_code_pattern, text)
        
        # Consider it modernization content if:
        # 1. Has multiple modernization keywords, OR
        # 2. Has product codes and at least one modernization keyword
        return keyword_count >= 2 or (len(product_codes) >= 2 and keyword_count >= 1)
    
    def create_modernization_summary(self, extraction_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create a comprehensive summary of modernization content.
        
        Args:
            extraction_results: Results from extract_embedded_images.
            
        Returns:
            Modernization summary.
        """
        summary = {
            "total_images_processed": extraction_results["processed_images"],
            "images_with_modernization_content": len(extraction_results["modernization_content"]),
            "all_product_mappings": [],
            "all_replacement_tables": [],
            "all_modernization_paths": [],
            "confidence_score": 0.0,
            "extraction_quality": "unknown"
        }
        
        # Aggregate all modernization content
        for content in extraction_results["modernization_content"]:
            summary["all_product_mappings"].extend(content.get("product_mappings", []))
            summary["all_replacement_tables"].extend(content.get("replacement_tables", []))
            summary["all_modernization_paths"].extend(content.get("modernization_paths", []))
        
        # Calculate overall confidence
        if extraction_results["modernization_content"]:
            confidences = [content.get("confidence", 0.0) for content in extraction_results["modernization_content"]]
            summary["confidence_score"] = sum(confidences) / len(confidences)
        
        # Determine extraction quality
        if summary["confidence_score"] > 0.8:
            summary["extraction_quality"] = "high"
        elif summary["confidence_score"] > 0.6:
            summary["extraction_quality"] = "medium"
        else:
            summary["extraction_quality"] = "low"
        
        return summary 