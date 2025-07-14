"""Advanced Preview Service for SE Letters Pipeline.

This service provides advanced side-by-side document preview with annotation overlay,
modernization path highlighting, and interactive visualization capabilities.
"""

import base64
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import io
import subprocess

# Third-party imports
try:
    from PIL import Image, ImageDraw, ImageFont
    from pdf2image import convert_from_path
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

from ..utils.logger import get_logger
from ..core.exceptions import PreviewGenerationError

logger = get_logger(__name__)


class AdvancedPreviewService:
    """Advanced preview service with side-by-side visualization and annotation overlay."""
    
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "se_letters_advanced_preview"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Industrial monochromatic color scheme
        self.color_scheme = {
            "primary": "#1a1a1a",      # Dark charcoal
            "secondary": "#2d2d2d",    # Medium gray
            "accent": "#00ff88",       # Bright green accent
            "warning": "#ff6b35",      # Orange warning
            "error": "#ff3333",        # Red error
            "success": "#00cc66",      # Green success
            "text": "#ffffff",         # White text
            "text_secondary": "#cccccc", # Light gray text
            "background": "#0f0f0f",   # Almost black background
            "border": "#404040"        # Border gray
        }
        
        # Annotation settings
        self.annotation_settings = {
            "font_size": 12,
            "line_width": 2,
            "highlight_opacity": 0.3,
            "annotation_padding": 5,
            "modernization_highlight_color": "#00ff88",
            "replacement_highlight_color": "#ff6b35",
            "obsolete_highlight_color": "#ff3333"
        }
    
    def create_advanced_side_by_side_preview(
        self, 
        document_path: Path, 
        extraction_results: Dict[str, Any],
        modernization_data: Optional[Dict[str, Any]] = None,
        output_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Create advanced side-by-side preview with annotations and modernization highlighting.
        
        Args:
            document_path: Path to the document file.
            extraction_results: Document extraction results.
            modernization_data: Modernization path data from image processing.
            output_path: Optional output path for HTML file.
            
        Returns:
            Preview generation results.
        """
        if not PIL_AVAILABLE:
            raise PreviewGenerationError("PIL/Pillow not available for advanced preview")
        
        try:
            logger.info(f"Creating advanced side-by-side preview for {document_path.name}")
            
            # Generate document images with annotations
            annotated_images = self._generate_annotated_images(
                document_path, extraction_results, modernization_data
            )
            
            # Create side-by-side HTML with industrial UI
            html_content = self._create_advanced_html_preview(
                document_path, annotated_images, extraction_results, modernization_data
            )
            
            # Save HTML file
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = self.temp_dir / f"advanced_preview_{timestamp}.html"
            
            output_path.write_text(html_content, encoding='utf-8')
            
            result = {
                "success": True,
                "output_path": str(output_path),
                "preview_type": "advanced_side_by_side",
                "total_pages": len(annotated_images),
                "annotations_count": sum(len(img.get("annotations", [])) for img in annotated_images),
                "modernization_highlights": sum(len(img.get("modernization_highlights", [])) for img in annotated_images),
                "file_size": output_path.stat().st_size
            }
            
            logger.info(f"Advanced preview created: {result['total_pages']} pages, {result['annotations_count']} annotations")
            return result
            
        except Exception as e:
            raise PreviewGenerationError(f"Advanced preview generation failed: {e}")
    
    def _generate_annotated_images(
        self, 
        document_path: Path, 
        extraction_results: Dict[str, Any],
        modernization_data: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate document images with annotations and modernization highlighting.
        
        Args:
            document_path: Path to the document file.
            extraction_results: Document extraction results.
            modernization_data: Modernization path data.
            
        Returns:
            List of annotated image data.
        """
        # Convert document to images
        base_images = self._convert_document_to_images(document_path)
        
        annotated_images = []
        for i, image_data in enumerate(base_images):
            # Create annotated version
            annotated_image = self._annotate_image(
                image_data, extraction_results, modernization_data, i
            )
            annotated_images.append(annotated_image)
        
        return annotated_images
    
    def _convert_document_to_images(self, document_path: Path) -> List[Dict[str, Any]]:
        """Convert document to high-quality images for annotation.
        
        Args:
            document_path: Path to the document file.
            
        Returns:
            List of image data dictionaries.
        """
        suffix = document_path.suffix.lower()
        
        if suffix == ".pdf":
            return self._convert_pdf_to_images(document_path)
        elif suffix in [".docx", ".doc"]:
            return self._convert_doc_to_images(document_path)
        else:
            raise PreviewGenerationError(f"Unsupported document format: {suffix}")
    
    def _convert_pdf_to_images(self, file_path: Path) -> List[Dict[str, Any]]:
        """Convert PDF to high-quality images."""
        images = convert_from_path(file_path, dpi=200, fmt='PNG')
        
        image_data = []
        for i, image in enumerate(images):
            # Convert to base64
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            image_data.append({
                "page_number": i + 1,
                "image_data": img_base64,
                "image_format": "PNG",
                "size": image.size,
                "pil_image": image
            })
        
        return image_data
    
    def _convert_doc_to_images(self, file_path: Path) -> List[Dict[str, Any]]:
        """Convert DOC/DOCX to images via LibreOffice."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Convert to PDF first
            result = subprocess.run([
                "/Applications/LibreOffice.app/Contents/MacOS/soffice",
                "--headless",
                "--convert-to", "pdf",
                "--outdir", str(temp_path),
                str(file_path)
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                raise PreviewGenerationError(f"LibreOffice conversion failed: {result.stderr}")
            
            pdf_files = list(temp_path.glob("*.pdf"))
            if not pdf_files:
                raise PreviewGenerationError("No PDF file produced")
            
            return self._convert_pdf_to_images(pdf_files[0])
    
    def _annotate_image(
        self, 
        image_data: Dict[str, Any], 
        extraction_results: Dict[str, Any],
        modernization_data: Optional[Dict[str, Any]],
        page_index: int
    ) -> Dict[str, Any]:
        """Add annotations and modernization highlights to image.
        
        Args:
            image_data: Base image data.
            extraction_results: Document extraction results.
            modernization_data: Modernization path data.
            page_index: Page index for multi-page documents.
            
        Returns:
            Annotated image data.
        """
        pil_image = image_data["pil_image"].copy()
        draw = ImageDraw.Draw(pil_image)
        
        annotations = []
        modernization_highlights = []
        
        # Add text extraction annotations
        if extraction_results.get("success"):
            annotations.extend(self._add_text_annotations(draw, extraction_results, pil_image.size))
        
        # Add modernization path highlights
        if modernization_data and modernization_data.get("modernization_content"):
            modernization_highlights.extend(
                self._add_modernization_highlights(draw, modernization_data, pil_image.size)
            )
        
        # Add embedded image annotations if available
        if extraction_results.get("metadata", {}).get("embedded_images"):
            annotations.extend(
                self._add_embedded_image_annotations(draw, extraction_results, pil_image.size)
            )
        
        # Convert annotated image to base64
        buffer = io.BytesIO()
        pil_image.save(buffer, format='PNG')
        annotated_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return {
            "page_number": image_data["page_number"],
            "original_image": image_data["image_data"],
            "annotated_image": annotated_base64,
            "annotations": annotations,
            "modernization_highlights": modernization_highlights,
            "size": pil_image.size
        }
    
    def _add_text_annotations(
        self, 
        draw: ImageDraw.Draw, 
        extraction_results: Dict[str, Any], 
        image_size: Tuple[int, int]
    ) -> List[Dict[str, Any]]:
        """Add text extraction annotations to image.
        
        Args:
            draw: PIL ImageDraw object.
            extraction_results: Document extraction results.
            image_size: Image dimensions.
            
        Returns:
            List of annotation data.
        """
        annotations = []
        
        # Add extraction method indicator
        method_used = extraction_results.get("method_used", "unknown")
        method_color = self.color_scheme["success"] if extraction_results.get("success") else self.color_scheme["error"]
        
        # Draw method indicator in top-left corner
        draw.rectangle(
            [(10, 10), (200, 40)],
            fill=method_color,
            outline=self.color_scheme["border"]
        )
        draw.text(
            (15, 20),
            f"Method: {method_used}",
            fill=self.color_scheme["text"]
        )
        
        annotations.append({
            "type": "extraction_method",
            "text": f"Extraction Method: {method_used}",
            "position": (10, 10),
            "color": method_color
        })
        
        # Add confidence indicator if available
        if "confidence" in extraction_results.get("metadata", {}):
            confidence = extraction_results["metadata"]["confidence"]
            confidence_color = self._get_confidence_color(confidence)
            
            draw.rectangle(
                [(10, 50), (200, 80)],
                fill=confidence_color,
                outline=self.color_scheme["border"]
            )
            draw.text(
                (15, 60),
                f"Confidence: {confidence:.1f}%",
                fill=self.color_scheme["text"]
            )
            
            annotations.append({
                "type": "confidence_score",
                "text": f"Confidence: {confidence:.1f}%",
                "position": (10, 50),
                "color": confidence_color
            })
        
        return annotations
    
    def _add_modernization_highlights(
        self, 
        draw: ImageDraw.Draw, 
        modernization_data: Dict[str, Any], 
        image_size: Tuple[int, int]
    ) -> List[Dict[str, Any]]:
        """Add modernization path highlights to image.
        
        Args:
            draw: PIL ImageDraw object.
            modernization_data: Modernization path data.
            image_size: Image dimensions.
            
        Returns:
            List of modernization highlight data.
        """
        highlights = []
        
        # This is a simplified version - in a full implementation, you would
        # use OCR coordinate data to precisely locate text regions
        
        # Add modernization indicator in top-right corner
        if modernization_data.get("modernization_content"):
            modernization_count = len(modernization_data["modernization_content"])
            
            draw.rectangle(
                [(image_size[0] - 250, 10), (image_size[0] - 10, 40)],
                fill=self.color_scheme["accent"],
                outline=self.color_scheme["border"]
            )
            draw.text(
                (image_size[0] - 240, 20),
                f"Modernization Content: {modernization_count}",
                fill=self.color_scheme["text"]
            )
            
            highlights.append({
                "type": "modernization_indicator",
                "text": f"Modernization Content Found: {modernization_count}",
                "position": (image_size[0] - 250, 10),
                "color": self.color_scheme["accent"]
            })
        
        return highlights
    
    def _add_embedded_image_annotations(
        self, 
        draw: ImageDraw.Draw, 
        extraction_results: Dict[str, Any], 
        image_size: Tuple[int, int]
    ) -> List[Dict[str, Any]]:
        """Add embedded image annotations to image.
        
        Args:
            draw: PIL ImageDraw object.
            extraction_results: Document extraction results.
            image_size: Image dimensions.
            
        Returns:
            List of annotation data.
        """
        annotations = []
        
        embedded_images = extraction_results.get("metadata", {}).get("embedded_images", {})
        if embedded_images.get("processed_images", 0) > 0:
            processed_count = embedded_images["processed_images"]
            modernization_count = embedded_images.get("modernization_images", 0)
            
            # Add embedded image indicator
            draw.rectangle(
                [(10, image_size[1] - 80), (300, image_size[1] - 10)],
                fill=self.color_scheme["secondary"],
                outline=self.color_scheme["border"]
            )
            draw.text(
                (15, image_size[1] - 70),
                f"Embedded Images: {processed_count}",
                fill=self.color_scheme["text"]
            )
            draw.text(
                (15, image_size[1] - 50),
                f"With Modernization: {modernization_count}",
                fill=self.color_scheme["accent"]
            )
            
            annotations.append({
                "type": "embedded_images",
                "text": f"Embedded Images: {processed_count} (Modernization: {modernization_count})",
                "position": (10, image_size[1] - 80),
                "color": self.color_scheme["secondary"]
            })
        
        return annotations
    
    def _get_confidence_color(self, confidence: float) -> str:
        """Get color based on confidence score.
        
        Args:
            confidence: Confidence score (0-100).
            
        Returns:
            Color hex code.
        """
        if confidence >= 80:
            return self.color_scheme["success"]
        elif confidence >= 60:
            return self.color_scheme["warning"]
        else:
            return self.color_scheme["error"]
    
    def _create_advanced_html_preview(
        self, 
        document_path: Path, 
        annotated_images: List[Dict[str, Any]], 
        extraction_results: Dict[str, Any],
        modernization_data: Optional[Dict[str, Any]]
    ) -> str:
        """Create advanced HTML preview with industrial UI.
        
        Args:
            document_path: Path to the document file.
            annotated_images: List of annotated image data.
            extraction_results: Document extraction results.
            modernization_data: Modernization path data.
            
        Returns:
            HTML content string.
        """
        # Extract key information
        document_name = document_path.name
        extraction_method = extraction_results.get("method_used", "unknown")
        success_status = extraction_results.get("success", False)
        
        # Modernization summary
        modernization_summary = ""
        if modernization_data and modernization_data.get("modernization_content"):
            summary_data = self._create_modernization_summary(modernization_data)
            modernization_summary = json.dumps(summary_data, indent=2)
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Advanced Preview - {document_name}</title>
    <style>
        :root {{
            --primary-color: {self.color_scheme["primary"]};
            --secondary-color: {self.color_scheme["secondary"]};
            --accent-color: {self.color_scheme["accent"]};
            --warning-color: {self.color_scheme["warning"]};
            --error-color: {self.color_scheme["error"]};
            --success-color: {self.color_scheme["success"]};
            --text-color: {self.color_scheme["text"]};
            --text-secondary: {self.color_scheme["text_secondary"]};
            --background-color: {self.color_scheme["background"]};
            --border-color: {self.color_scheme["border"]};
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, var(--background-color) 0%, var(--primary-color) 100%);
            color: var(--text-color);
            min-height: 100vh;
            overflow-x: hidden;
        }}
        
        .header {{
            background: linear-gradient(90deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            padding: 20px;
            border-bottom: 2px solid var(--accent-color);
            box-shadow: 0 4px 20px rgba(0, 255, 136, 0.1);
        }}
        
        .header h1 {{
            color: var(--accent-color);
            font-size: 2.5em;
            font-weight: 300;
            text-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
            margin-bottom: 10px;
        }}
        
        .header .subtitle {{
            color: var(--text-secondary);
            font-size: 1.2em;
            font-weight: 300;
        }}
        
        .status-bar {{
            background: var(--secondary-color);
            padding: 15px 20px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .status-item {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .status-indicator {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: var(--success-color);
            box-shadow: 0 0 10px rgba(0, 204, 102, 0.5);
        }}
        
        .status-indicator.error {{
            background: var(--error-color);
            box-shadow: 0 0 10px rgba(255, 51, 51, 0.5);
        }}
        
        .main-container {{
            display: flex;
            height: calc(100vh - 140px);
        }}
        
        .preview-panel {{
            flex: 1;
            background: var(--primary-color);
            border-right: 1px solid var(--border-color);
            overflow-y: auto;
            padding: 20px;
        }}
        
        .info-panel {{
            flex: 0 0 400px;
            background: var(--secondary-color);
            overflow-y: auto;
            padding: 20px;
        }}
        
        .page-container {{
            margin-bottom: 30px;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        }}
        
        .page-header {{
            background: var(--secondary-color);
            padding: 10px 15px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .page-title {{
            color: var(--accent-color);
            font-weight: 600;
        }}
        
        .page-stats {{
            color: var(--text-secondary);
            font-size: 0.9em;
        }}
        
        .image-container {{
            position: relative;
            background: #fff;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 400px;
        }}
        
        .document-image {{
            max-width: 100%;
            max-height: 800px;
            border-radius: 4px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
        }}
        
        .toggle-container {{
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(0, 0, 0, 0.8);
            border-radius: 4px;
            padding: 5px;
        }}
        
        .toggle-btn {{
            background: var(--accent-color);
            color: var(--primary-color);
            border: none;
            padding: 8px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9em;
            transition: all 0.3s ease;
        }}
        
        .toggle-btn:hover {{
            background: var(--success-color);
            transform: translateY(-2px);
        }}
        
        .info-section {{
            background: var(--primary-color);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            margin-bottom: 20px;
            overflow: hidden;
        }}
        
        .info-section h3 {{
            background: var(--secondary-color);
            color: var(--accent-color);
            padding: 15px;
            margin: 0;
            border-bottom: 1px solid var(--border-color);
        }}
        
        .info-content {{
            padding: 15px;
        }}
        
        .modernization-item {{
            background: var(--secondary-color);
            border-left: 4px solid var(--accent-color);
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
        }}
        
        .product-mapping {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid var(--border-color);
        }}
        
        .product-mapping:last-child {{
            border-bottom: none;
        }}
        
        .obsolete-code {{
            color: var(--error-color);
            font-weight: 600;
        }}
        
        .replacement-code {{
            color: var(--success-color);
            font-weight: 600;
        }}
        
        .arrow {{
            color: var(--accent-color);
            font-size: 1.2em;
        }}
        
        pre {{
            background: var(--background-color);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            padding: 15px;
            overflow-x: auto;
            font-size: 0.9em;
            line-height: 1.4;
        }}
        
        .glow {{
            animation: glow 2s ease-in-out infinite alternate;
        }}
        
        @keyframes glow {{
            from {{
                box-shadow: 0 0 5px var(--accent-color);
            }}
            to {{
                box-shadow: 0 0 20px var(--accent-color), 0 0 30px var(--accent-color);
            }}
        }}
        
        .fade-in {{
            animation: fadeIn 0.5s ease-in;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        ::-webkit-scrollbar {{
            width: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: var(--primary-color);
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: var(--accent-color);
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: var(--success-color);
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>⚡ Advanced Document Preview</h1>
        <div class="subtitle">Schneider Electric Obsolescence Letter Analysis</div>
    </div>
    
    <div class="status-bar">
        <div class="status-item">
            <div class="status-indicator {'error' if not success_status else ''}"></div>
            <span>Document: {document_name}</span>
        </div>
        <div class="status-item">
            <span>Extraction Method: {extraction_method}</span>
        </div>
        <div class="status-item">
            <span>Pages: {len(annotated_images)}</span>
        </div>
    </div>
    
    <div class="main-container">
        <div class="preview-panel">
            {''.join(self._create_page_html(img_data, i) for i, img_data in enumerate(annotated_images))}
        </div>
        
        <div class="info-panel">
            <div class="info-section fade-in">
                <h3>🔍 Extraction Results</h3>
                <div class="info-content">
                    <p><strong>Method:</strong> {extraction_method}</p>
                    <p><strong>Status:</strong> {'✅ Success' if success_status else '❌ Failed'}</p>
                    <p><strong>Text Length:</strong> {len(extraction_results.get('text', ''))} characters</p>
                </div>
            </div>
            
            {self._create_modernization_info_html(modernization_data) if modernization_data else ''}
            
            <div class="info-section fade-in">
                <h3>📊 Processing Details</h3>
                <div class="info-content">
                    <pre>{json.dumps(extraction_results.get('metadata', {}), indent=2)}</pre>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Toggle between original and annotated images
        function toggleImage(pageNum) {{
            const img = document.getElementById('page-' + pageNum);
            const btn = document.getElementById('toggle-' + pageNum);
            
            if (img.dataset.mode === 'original') {{
                img.src = 'data:image/png;base64,' + img.dataset.annotated;
                img.dataset.mode = 'annotated';
                btn.textContent = 'Show Original';
                img.classList.add('glow');
            }} else {{
                img.src = 'data:image/png;base64,' + img.dataset.original;
                img.dataset.mode = 'original';
                btn.textContent = 'Show Annotations';
                img.classList.remove('glow');
            }}
        }}
        
        // Add fade-in animation to elements
        document.addEventListener('DOMContentLoaded', function() {{
            const elements = document.querySelectorAll('.fade-in');
            elements.forEach((el, index) => {{
                setTimeout(() => {{
                    el.style.opacity = '1';
                    el.style.transform = 'translateY(0)';
                }}, index * 100);
            }});
        }});
    </script>
</body>
</html>
        """
        
        return html_content
    
    def _create_page_html(self, image_data: Dict[str, Any], index: int) -> str:
        """Create HTML for a single page with annotations.
        
        Args:
            image_data: Image data with annotations.
            index: Page index.
            
        Returns:
            HTML string for the page.
        """
        page_num = image_data["page_number"]
        annotations_count = len(image_data.get("annotations", []))
        highlights_count = len(image_data.get("modernization_highlights", []))
        
        return f"""
        <div class="page-container fade-in">
            <div class="page-header">
                <div class="page-title">Page {page_num}</div>
                <div class="page-stats">
                    Annotations: {annotations_count} | Highlights: {highlights_count}
                </div>
            </div>
            <div class="image-container">
                <img id="page-{page_num}" 
                     class="document-image"
                     src="data:image/png;base64,{image_data['original_image']}"
                     data-original="{image_data['original_image']}"
                     data-annotated="{image_data['annotated_image']}"
                     data-mode="original"
                     alt="Document Page {page_num}">
                <div class="toggle-container">
                    <button id="toggle-{page_num}" 
                            class="toggle-btn" 
                            onclick="toggleImage({page_num})">
                        Show Annotations
                    </button>
                </div>
            </div>
        </div>
        """
    
    def _create_modernization_info_html(self, modernization_data: Dict[str, Any]) -> str:
        """Create HTML for modernization information panel.
        
        Args:
            modernization_data: Modernization path data.
            
        Returns:
            HTML string for modernization info.
        """
        if not modernization_data or not modernization_data.get("modernization_content"):
            return ""
        
        # Extract modernization summary
        summary = self._create_modernization_summary(modernization_data)
        
        html = """
        <div class="info-section fade-in">
            <h3>🔄 Modernization Paths</h3>
            <div class="info-content">
        """
        
        # Add product mappings
        if summary.get("all_product_mappings"):
            html += "<h4>Product Replacements:</h4>"
            for mapping in summary["all_product_mappings"][:5]:  # Show first 5
                html += f"""
                <div class="product-mapping">
                    <span class="obsolete-code">{mapping['obsolete_code']}</span>
                    <span class="arrow">→</span>
                    <span class="replacement-code">{mapping['replacement_code']}</span>
                </div>
                """
            
            if len(summary["all_product_mappings"]) > 5:
                html += f"<p><em>... and {len(summary['all_product_mappings']) - 5} more mappings</em></p>"
        
        # Add modernization paths
        if summary.get("all_modernization_paths"):
            html += "<h4>Migration Paths:</h4>"
            for path in summary["all_modernization_paths"][:3]:  # Show first 3
                html += f"""
                <div class="modernization-item">
                    {path['description']}
                </div>
                """
        
        # Add quality info
        html += f"""
            <div class="modernization-item">
                <strong>Extraction Quality:</strong> {summary.get('extraction_quality', 'unknown').upper()}<br>
                <strong>Confidence:</strong> {summary.get('confidence_score', 0):.1f}%
            </div>
        """
        
        html += """
            </div>
        </div>
        """
        
        return html
    
    def _create_modernization_summary(self, modernization_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of modernization data.
        
        Args:
            modernization_data: Modernization path data.
            
        Returns:
            Modernization summary.
        """
        summary = {
            "all_product_mappings": [],
            "all_replacement_tables": [],
            "all_modernization_paths": [],
            "confidence_score": 0.0,
            "extraction_quality": "unknown"
        }
        
        # Aggregate all modernization content
        for content in modernization_data.get("modernization_content", []):
            summary["all_product_mappings"].extend(content.get("product_mappings", []))
            summary["all_replacement_tables"].extend(content.get("replacement_tables", []))
            summary["all_modernization_paths"].extend(content.get("modernization_paths", []))
        
        # Calculate overall confidence
        if modernization_data.get("modernization_content"):
            confidences = [
                content.get("confidence", 0.0) 
                for content in modernization_data["modernization_content"]
            ]
            summary["confidence_score"] = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Determine extraction quality
        if summary["confidence_score"] > 80:
            summary["extraction_quality"] = "high"
        elif summary["confidence_score"] > 60:
            summary["extraction_quality"] = "medium"
        else:
            summary["extraction_quality"] = "low"
        
        return summary 