"""Document preview service for side-by-side visualization."""

import time
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import json
import base64

from pdf2image import convert_from_path
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF

from ..core.config import Config
from ..core.exceptions import PreviewGenerationError
from ..utils.logger import get_logger

logger = get_logger(__name__)


class PreviewService:
    """Service for generating document previews and side-by-side comparisons."""

    def __init__(self, config: Config) -> None:
        """Initialize the preview service.
        
        Args:
            config: Configuration instance.
        """
        self.config = config
        self.preview_dir = Path("data/previews")
        self.preview_dir.mkdir(parents=True, exist_ok=True)
        
        # Preview settings
        self.dpi = 150
        self.image_quality = 85
        self.max_width = 800
        self.max_height = 1200
        
        # LibreOffice path for macOS
        self.libreoffice_path = "/Applications/LibreOffice.app/Contents/MacOS/soffice"

    def generate_document_preview(self, file_path: Path, output_dir: Path = None) -> Dict[str, Any]:
        """Generate preview images for a document.
        
        Args:
            file_path: Path to document file.
            output_dir: Directory to save preview images.
            
        Returns:
            Dictionary with preview generation results.
        """
        start_time = time.time()
        
        if output_dir is None:
            output_dir = self.preview_dir / file_path.stem
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            logger.info(f"Generating preview for: {file_path}")
            
            suffix = file_path.suffix.lower()
            
            if suffix == ".pdf":
                result = self._generate_pdf_preview(file_path, output_dir)
            elif suffix in [".docx", ".doc"]:
                result = self._generate_doc_preview(file_path, output_dir)
            else:
                raise PreviewGenerationError(f"Unsupported format: {suffix}")
            
            processing_time = time.time() - start_time
            
            result.update({
                "processing_time": processing_time,
                "file_path": str(file_path),
                "output_dir": str(output_dir),
                "success": True
            })
            
            logger.info(
                f"Generated {len(result.get('image_paths', []))} preview images "
                f"for {file_path.name} in {processing_time:.2f}s"
            )
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Preview generation failed for {file_path}: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "processing_time": processing_time,
                "file_path": str(file_path),
                "output_dir": str(output_dir),
                "image_paths": []
            }

    def _generate_pdf_preview(self, file_path: Path, output_dir: Path) -> Dict[str, Any]:
        """Generate preview images for PDF files.
        
        Args:
            file_path: Path to PDF file.
            output_dir: Output directory.
            
        Returns:
            Preview generation results.
        """
        try:
            # Convert PDF to images
            images = convert_from_path(
                file_path, 
                dpi=self.dpi,
                first_page=1,
                last_page=5  # Limit to first 5 pages
            )
            
            image_paths = []
            
            for i, image in enumerate(images):
                # Resize if needed
                if image.width > self.max_width or image.height > self.max_height:
                    image.thumbnail((self.max_width, self.max_height), Image.Resampling.LANCZOS)
                
                # Save image
                image_path = output_dir / f"page_{i+1}.jpg"
                image.save(image_path, "JPEG", quality=self.image_quality)
                image_paths.append(image_path)
            
            return {
                "format": "pdf",
                "pages": len(images),
                "image_paths": image_paths,
                "method": "pdf2image"
            }
            
        except Exception as e:
            raise PreviewGenerationError(f"PDF preview generation failed: {e}")

    def _generate_doc_preview(self, file_path: Path, output_dir: Path) -> Dict[str, Any]:
        """Generate preview images for DOC/DOCX files.
        
        Args:
            file_path: Path to DOC/DOCX file.
            output_dir: Output directory.
            
        Returns:
            Preview generation results.
        """
        try:
            # Convert DOC/DOCX to PDF first
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Convert to PDF using LibreOffice
                result = subprocess.run([
                    self.libreoffice_path,
                    "--headless",
                    "--convert-to", "pdf",
                    "--outdir", str(temp_path),
                    str(file_path)
                ], capture_output=True, text=True, timeout=60)
                
                if result.returncode != 0:
                    raise PreviewGenerationError(f"LibreOffice conversion failed: {result.stderr}")
                
                # Find the converted PDF
                pdf_files = list(temp_path.glob("*.pdf"))
                if not pdf_files:
                    raise PreviewGenerationError("No PDF file produced")
                
                pdf_path = pdf_files[0]
                
                # Generate preview from PDF
                pdf_result = self._generate_pdf_preview(pdf_path, output_dir)
                pdf_result.update({
                    "format": file_path.suffix.lower(),
                    "method": "libreoffice_pdf_conversion"
                })
                
                return pdf_result
                
        except subprocess.TimeoutExpired:
            raise PreviewGenerationError("LibreOffice conversion timeout")
        except Exception as e:
            raise PreviewGenerationError(f"DOC preview generation failed: {e}")

    def create_side_by_side_preview(
        self, 
        document_path: Path, 
        extraction_result: Dict[str, Any],
        output_path: Path = None
    ) -> Dict[str, Any]:
        """Create side-by-side preview with document images and extraction results.
        
        Args:
            document_path: Path to document file.
            extraction_result: Extraction results from XAI service.
            output_path: Output path for side-by-side preview.
            
        Returns:
            Side-by-side preview generation results.
        """
        try:
            logger.info(f"Creating side-by-side preview for: {document_path}")
            
            # Generate document preview
            preview_result = self.generate_document_preview(document_path)
            
            if not preview_result["success"]:
                raise PreviewGenerationError(f"Document preview failed: {preview_result['error']}")
            
            # Create side-by-side HTML
            if output_path is None:
                output_path = self.preview_dir / f"{document_path.stem}_side_by_side.html"
            
            html_content = self._create_side_by_side_html(
                document_path,
                preview_result["image_paths"],
                extraction_result
            )
            
            # Write HTML file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return {
                "success": True,
                "html_path": str(output_path),
                "preview_images": len(preview_result["image_paths"]),
                "document_name": document_path.name,
                "extraction_confidence": extraction_result.get("extraction_metadata", {}).get("confidence", 0)
            }
            
        except Exception as e:
            logger.error(f"Side-by-side preview creation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "html_path": None
            }

    def _create_side_by_side_html(
        self, 
        document_path: Path, 
        image_paths: List[Path], 
        extraction_result: Dict[str, Any]
    ) -> str:
        """Create HTML for side-by-side preview.
        
        Args:
            document_path: Path to document file.
            image_paths: List of preview image paths.
            extraction_result: Extraction results.
            
        Returns:
            HTML content string.
        """
        # Convert images to base64 for embedding
        image_data = []
        for img_path in image_paths:
            try:
                with open(img_path, 'rb') as f:
                    img_base64 = base64.b64encode(f.read()).decode('utf-8')
                    image_data.append({
                        "path": str(img_path),
                        "data": img_base64,
                        "page": len(image_data) + 1
                    })
            except Exception as e:
                logger.warning(f"Failed to encode image {img_path}: {e}")
        
        # Extract key information for display
        product_info = extraction_result.get("product_identification", {})
        extraction_meta = extraction_result.get("extraction_metadata", {})
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Side-by-Side Preview: {document_path.name}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: #fff;
            min-height: 100vh;
        }}
        
        .header {{
            background: rgba(0, 0, 0, 0.2);
            padding: 1rem;
            text-align: center;
            border-bottom: 2px solid rgba(255, 255, 255, 0.1);
        }}
        
        .header h1 {{
            font-size: 1.8rem;
            margin-bottom: 0.5rem;
        }}
        
        .header .meta {{
            font-size: 0.9rem;
            opacity: 0.8;
        }}
        
        .container {{
            display: flex;
            height: calc(100vh - 100px);
            gap: 1rem;
            padding: 1rem;
        }}
        
        .left-panel {{
            flex: 1;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 1rem;
            overflow-y: auto;
            backdrop-filter: blur(10px);
        }}
        
        .right-panel {{
            flex: 1;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 1rem;
            overflow-y: auto;
            backdrop-filter: blur(10px);
        }}
        
        .panel-title {{
            font-size: 1.4rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid rgba(255, 255, 255, 0.2);
        }}
        
        .document-preview {{
            text-align: center;
        }}
        
        .page-image {{
            max-width: 100%;
            margin-bottom: 1rem;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        }}
        
        .page-label {{
            font-size: 0.9rem;
            margin-bottom: 0.5rem;
            opacity: 0.8;
        }}
        
        .extraction-section {{
            margin-bottom: 1.5rem;
        }}
        
        .section-title {{
            font-size: 1.1rem;
            margin-bottom: 0.5rem;
            color: #ffd700;
        }}
        
        .confidence-bar {{
            width: 100%;
            height: 20px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            overflow: hidden;
            margin-bottom: 1rem;
        }}
        
        .confidence-fill {{
            height: 100%;
            background: linear-gradient(90deg, #ff6b6b, #ffd93d, #6bcf7f);
            border-radius: 10px;
            transition: width 0.3s ease;
        }}
        
        .confidence-text {{
            text-align: center;
            font-size: 0.9rem;
            margin-top: 0.5rem;
        }}
        
        .info-list {{
            list-style: none;
            padding: 0;
        }}
        
        .info-item {{
            background: rgba(255, 255, 255, 0.1);
            margin-bottom: 0.5rem;
            padding: 0.5rem;
            border-radius: 5px;
            font-size: 0.9rem;
        }}
        
        .debug-section {{
            background: rgba(0, 0, 0, 0.3);
            padding: 1rem;
            border-radius: 8px;
            margin-top: 1rem;
        }}
        
        .debug-title {{
            color: #ff6b6b;
            font-size: 1rem;
            margin-bottom: 0.5rem;
        }}
        
        .debug-json {{
            background: rgba(0, 0, 0, 0.5);
            padding: 1rem;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            font-size: 0.8rem;
            white-space: pre-wrap;
            max-height: 300px;
            overflow-y: auto;
        }}
        
        .no-data {{
            text-align: center;
            opacity: 0.6;
            font-style: italic;
        }}
        
        @media (max-width: 768px) {{
            .container {{
                flex-direction: column;
                height: auto;
            }}
            
            .left-panel, .right-panel {{
                flex: none;
                height: auto;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📄 Document Analysis Preview</h1>
        <div class="meta">
            <strong>{document_path.name}</strong> | 
            Generated: {time.strftime("%Y-%m-%d %H:%M:%S")} | 
            Confidence: {extraction_meta.get('confidence', 0):.2f}
        </div>
    </div>
    
    <div class="container">
        <div class="left-panel">
            <div class="panel-title">📖 Document Preview</div>
            <div class="document-preview">
"""
        
        # Add document images
        if image_data:
            for img in image_data:
                html_content += f"""
                <div class="page-label">Page {img['page']}</div>
                <img src="data:image/jpeg;base64,{img['data']}" 
                     alt="Page {img['page']}" 
                     class="page-image">
"""
        else:
            html_content += """
                <div class="no-data">
                    ⚠️ No preview images available<br>
                    Document could not be converted to images
                </div>
"""
        
        html_content += """
            </div>
        </div>
        
        <div class="right-panel">
            <div class="panel-title">🤖 AI Extraction Results</div>
            
            <!-- Confidence Score -->
            <div class="extraction-section">
                <div class="section-title">Confidence Score</div>
                <div class="confidence-bar">
"""
        
        confidence = extraction_meta.get('confidence', 0)
        confidence_percent = confidence * 100
        
        html_content += f"""
                    <div class="confidence-fill" style="width: {confidence_percent}%"></div>
                </div>
                <div class="confidence-text">{confidence_percent:.1f}% Confidence</div>
            </div>
"""
        
        # Product Identification
        ranges = product_info.get('ranges', [])
        if ranges:
            html_content += """
            <div class="extraction-section">
                <div class="section-title">🏭 Product Ranges</div>
                <ul class="info-list">
"""
            for range_name in ranges:
                html_content += f'<li class="info-item">{range_name}</li>'
            html_content += """
                </ul>
            </div>
"""
        
        # Product Codes
        codes = product_info.get('product_codes', [])
        if codes:
            html_content += """
            <div class="extraction-section">
                <div class="section-title">🔢 Product Codes</div>
                <ul class="info-list">
"""
            for code in codes:
                html_content += f'<li class="info-item">{code}</li>'
            html_content += """
                </ul>
            </div>
"""
        
        # Technical Specs
        tech_specs = extraction_result.get('technical_specs', {})
        voltage_levels = tech_specs.get('voltage_levels', [])
        if voltage_levels:
            html_content += """
            <div class="extraction-section">
                <div class="section-title">⚡ Voltage Levels</div>
                <ul class="info-list">
"""
            for voltage in voltage_levels:
                html_content += f'<li class="info-item">{voltage}</li>'
            html_content += """
                </ul>
            </div>
"""
        
        # Business Context
        business_context = extraction_result.get('business_context', {})
        customer_impact = business_context.get('customer_impact', [])
        if customer_impact:
            html_content += """
            <div class="extraction-section">
                <div class="section-title">👥 Customer Impact</div>
                <ul class="info-list">
"""
            for impact in customer_impact:
                html_content += f'<li class="info-item">{impact}</li>'
            html_content += """
                </ul>
            </div>
"""
        
        # Debug Console (Raw JSON)
        html_content += f"""
            <div class="debug-section">
                <div class="debug-title">🔍 Debug Console - Raw Metadata JSON</div>
                <div class="debug-json">{json.dumps(extraction_result, indent=2)}</div>
            </div>
        </div>
    </div>
</body>
</html>"""
        
        return html_content

    def create_annotation_overlay(
        self, 
        image_path: Path, 
        annotations: List[Dict[str, Any]], 
        output_path: Path = None
    ) -> Path:
        """Create an annotated version of a document image.
        
        Args:
            image_path: Path to original image.
            annotations: List of annotations to overlay.
            output_path: Output path for annotated image.
            
        Returns:
            Path to annotated image.
        """
        try:
            if output_path is None:
                output_path = image_path.parent / f"{image_path.stem}_annotated{image_path.suffix}"
            
            # Open the image
            image = Image.open(image_path)
            draw = ImageDraw.Draw(image)
            
            # Try to load a font (fallback to default if not available)
            try:
                font = ImageFont.truetype("arial.ttf", 20)
            except:
                font = ImageFont.load_default()
            
            # Draw annotations
            for i, annotation in enumerate(annotations):
                # Draw bounding box
                if "bbox" in annotation:
                    bbox = annotation["bbox"]
                    draw.rectangle(bbox, outline="red", width=2)
                
                # Draw label
                if "label" in annotation:
                    label = annotation["label"]
                    x, y = annotation.get("position", (10, 10 + i * 30))
                    
                    # Draw background for text
                    bbox = draw.textbbox((x, y), label, font=font)
                    draw.rectangle(bbox, fill="red")
                    draw.text((x, y), label, fill="white", font=font)
            
            # Save annotated image
            image.save(output_path)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Annotation overlay failed: {e}")
            return image_path

    def get_preview_status(self, document_path: Path) -> Dict[str, Any]:
        """Get the status of preview generation for a document.
        
        Args:
            document_path: Path to document file.
            
        Returns:
            Preview status information.
        """
        preview_dir = self.preview_dir / document_path.stem
        
        status = {
            "document_name": document_path.name,
            "preview_dir": str(preview_dir),
            "preview_exists": preview_dir.exists(),
            "image_count": 0,
            "html_preview": None
        }
        
        if preview_dir.exists():
            # Count preview images
            image_files = list(preview_dir.glob("*.jpg")) + list(preview_dir.glob("*.png"))
            status["image_count"] = len(image_files)
            
            # Check for HTML preview
            html_files = list(preview_dir.glob("*_side_by_side.html"))
            if html_files:
                status["html_preview"] = str(html_files[0])
        
        return status

    def clear_previews(self, document_path: Path = None) -> Dict[str, Any]:
        """Clear preview files for a document or all documents.
        
        Args:
            document_path: Specific document path (optional).
            
        Returns:
            Cleanup results.
        """
        try:
            if document_path:
                # Clear specific document previews
                preview_dir = self.preview_dir / document_path.stem
                if preview_dir.exists():
                    import shutil
                    shutil.rmtree(preview_dir)
                    return {"success": True, "cleared": str(preview_dir)}
            else:
                # Clear all previews
                if self.preview_dir.exists():
                    import shutil
                    shutil.rmtree(self.preview_dir)
                    self.preview_dir.mkdir(parents=True, exist_ok=True)
                    return {"success": True, "cleared": "all previews"}
            
            return {"success": True, "cleared": "none"}
            
        except Exception as e:
            logger.error(f"Preview cleanup failed: {e}")
            return {"success": False, "error": str(e)} 