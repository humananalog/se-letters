"""Excel processing service for the SE Letters project."""

import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

from ..core.config import Config
from ..core.exceptions import ProcessingError
from ..models.product import Product, ProductRange
from ..models.letter import Letter
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ExcelService:
    """Service for processing Excel files and managing product data."""

    def __init__(self, config: Config) -> None:
        """Initialize the Excel service.
        
        Args:
            config: Configuration instance.
        """
        self.config = config
        self.excel_data: Optional[pd.DataFrame] = None
        self.products: List[Product] = []
        self.ranges: List[ProductRange] = []

    def load_excel_data(self) -> pd.DataFrame:
        """Load Excel data from the configured file.
        
        Returns:
            DataFrame containing the Excel data.
            
        Raises:
            ProcessingError: If Excel file cannot be loaded.
        """
        excel_path = Path(self.config.data.excel_file)
        
        if not excel_path.exists():
            raise ProcessingError(f"Excel file not found: {excel_path}")
        
        try:
            logger.info(f"Loading Excel file: {excel_path}")
            
            # Read the specific sheet (IBcatalogue uses 'OIC_out' sheet)
            sheet_name = getattr(self.config.data, 'excel_sheet', 'OIC_out')
            
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
            
            logger.info(
                f"Loaded Excel data: {len(df)} rows, {len(df.columns)} columns"
            )
            logger.info(f"Sheet: {sheet_name}")
            
            # Apply filters if configured
            if hasattr(self.config.data, 'filters'):
                df = self._apply_filters(df)
            
            # Store the data
            self.excel_data = df
            
            # Parse products and ranges
            self._parse_products_from_dataframe(df)
            
            return df
            
        except Exception as e:
            raise ProcessingError(f"Failed to load Excel file: {e}") from e

    def _apply_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply configured filters to the DataFrame.
        
        Args:
            df: Original DataFrame.
            
        Returns:
            Filtered DataFrame.
        """
        original_count = len(df)
        filters = self.config.data.filters
        
        # Filter to Schneider Electric products only
        if getattr(filters, 'schneider_only', False):
            if 'IS_SCHNEIDER_BRAND' in df.columns:
                df = df[df['IS_SCHNEIDER_BRAND'] == 'Y']
                logger.info(f"Filtered to Schneider Electric products: {len(df)} rows")
        
        # Filter by obsolescence statuses
        if hasattr(filters, 'obsolescence_statuses') and filters.obsolescence_statuses:
            if 'COMMERCIAL_STATUS' in df.columns:
                df = df[df['COMMERCIAL_STATUS'].isin(filters.obsolescence_statuses)]
                logger.info(f"Filtered by obsolescence status: {len(df)} rows")
        
        logger.info(f"Applied filters: {original_count} -> {len(df)} rows")
        return df

    def _parse_products_from_dataframe(self, df: pd.DataFrame) -> None:
        """Parse products and ranges from the DataFrame.
        
        Args:
            df: DataFrame containing product data.
        """
        logger.info("Parsing products and ranges from Excel data")
        
        # Use column mappings from config
        columns = self.config.data.columns
        
        # Map column names
        range_col = columns.range_name  # RANGE_LABEL
        subrange_col = columns.subrange_name  # SUBRANGE_LABEL
        product_id_col = columns.product_id  # PRODUCT_IDENTIFIER
        description_col = columns.description  # PRODUCT_DESCRIPTION
        brand_col = columns.brand  # BRAND_LABEL
        status_col = columns.status  # COMMERCIAL_STATUS
        
        logger.info(f"Using column mappings: range={range_col}, "
                   f"subrange={subrange_col}, product_id={product_id_col}")
        
        # Parse products
        products = []
        ranges_set = set()
        
        for idx, row in df.iterrows():
            try:
                # Extract values using column mappings
                range_val = str(row.get(range_col, "")).strip()
                subrange_val = str(row.get(subrange_col, "")).strip()
                product_id = str(row.get(product_id_col, "")).strip()
                desc_val = str(row.get(description_col, "")).strip()
                brand_val = str(row.get(brand_col, "")).strip()
                status_val = str(row.get(status_col, "")).strip()
                
                # Skip empty rows
                if not product_id or product_id.lower() in ['nan', 'none', '']:
                    continue
                
                # Clean null values
                range_val = range_val if range_val.lower() not in ['nan', 'none', ''] else None
                subrange_val = subrange_val if subrange_val.lower() not in ['nan', 'none', ''] else None
                desc_val = desc_val if desc_val.lower() not in ['nan', 'none', ''] else None
                brand_val = brand_val if brand_val.lower() not in ['nan', 'none', ''] else None
                status_val = status_val if status_val.lower() not in ['nan', 'none', ''] else None
                
                # Create product
                product = Product(
                    range_name=range_val,
                    subrange=subrange_val,
                    model=product_id,  # Use product ID as model
                    description=desc_val,
                    metadata={
                        "row_index": idx,
                        "source_file": self.config.data.excel_file,
                        "product_id": product_id,
                        "brand": brand_val,
                        "status": status_val,
                        "sheet": getattr(self.config.data, 'excel_sheet', 'OIC_out'),
                    }
                )
                
                products.append(product)
                
                # Add to ranges set
                if range_val:
                    range_key = (range_val, subrange_val)
                    ranges_set.add(range_key)
                
            except Exception as e:
                logger.warning(f"Error parsing row {idx}: {e}")
                continue
        
        # Create ProductRange objects
        ranges = []
        for range_name, subrange in ranges_set:
            # Count products in this range
            product_count = sum(1 for p in products 
                              if p.range_name == range_name and p.subrange == subrange)
            
            product_range = ProductRange(
                range_name=range_name,
                subrange=subrange,
                description=f"Product range {range_name}" + (f" - {subrange}" if subrange else ""),
                metadata={
                    "source_file": self.config.data.excel_file,
                    "product_count": product_count,
                    "sheet": getattr(self.config.data, 'excel_sheet', 'OIC_out'),
                }
            )
            ranges.append(product_range)
        
        self.products = products
        self.ranges = ranges
        
        logger.info(f"Parsed {len(products)} products and {len(ranges)} unique ranges")
        
        # Log some statistics
        if products:
            range_counts = {}
            for product in products:
                range_name = product.range_name or "Unknown"
                range_counts[range_name] = range_counts.get(range_name, 0) + 1
            
            logger.info("Top 10 product ranges by count:")
            for range_name, count in sorted(range_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                logger.info(f"  {range_name}: {count} products")

    def extract_ranges(self, df: Optional[pd.DataFrame] = None) -> List[ProductRange]:
        """Extract unique product ranges from the Excel data.
        
        Args:
            df: Optional DataFrame. If None, uses loaded data.
            
        Returns:
            List of ProductRange objects.
        """
        if df is not None:
            self._parse_products_from_dataframe(df)
        elif not self.ranges:
            if self.excel_data is not None:
                self._parse_products_from_dataframe(self.excel_data)
            else:
                raise ProcessingError("No Excel data loaded")
        
        return self.ranges

    def get_products_by_range(self, range_name: str) -> List[Product]:
        """Get all products for a specific range.
        
        Args:
            range_name: Range name to search for.
            
        Returns:
            List of matching products.
        """
        if not self.products:
            raise ProcessingError("No products loaded")
        
        matching_products = []
        for product in self.products:
            if product.matches_range(range_name):
                matching_products.append(product)
        
        return matching_products

    def match_letters_to_records(self, letters: List[Letter]) -> Dict[str, Any]:
        """Match letters to Excel records based on detected ranges.
        
        Args:
            letters: List of processed letters.
            
        Returns:
            Dictionary containing matching results and statistics.
        """
        start_time = time.time()
        
        if not self.products:
            raise ProcessingError("No products loaded")
        
        logger.info(f"Matching {len(letters)} letters to {len(self.products)} products")
        
        matched_products = []
        unmatched_products = []
        letter_stats = {}
        
        # Create a mapping of products by range for faster lookup
        range_to_products = {}
        for product in self.products:
            ranges_to_check = [
                product.range_name,
                product.full_range,
                product.full_name
            ]
            
            for range_key in ranges_to_check:
                if range_key not in range_to_products:
                    range_to_products[range_key] = []
                range_to_products[range_key].append(product)
        
        # Match each letter
        for letter in letters:
            letter_matches = 0
            
            for detected_range in letter.ranges:
                # Find matching products
                matching_products = range_to_products.get(detected_range, [])
                
                # Update products with letter ID
                for product in matching_products:
                    if not product.letter_id:  # Don't overwrite existing assignments
                        product.letter_id = letter.letter_id
                        matched_products.append(product)
                        letter_matches += 1
            
            letter_stats[letter.letter_id] = {
                "ranges_detected": len(letter.ranges),
                "products_matched": letter_matches,
                "confidence": letter.metadata.confidence_score,
            }
        
        # Identify unmatched products
        for product in self.products:
            if not product.letter_id:
                unmatched_products.append(product)
        
        processing_time = time.time() - start_time
        
        results = {
            "total_documents": len(letters),
            "total_letters": len(letters),
            "total_products": len(self.products),
            "matched_records": len(matched_products),
            "unmatched_records": len(unmatched_products),
            "processing_time": processing_time,
            "letter_statistics": letter_stats,
            "matched_products": matched_products,
            "unmatched_products": unmatched_products,
        }
        
        logger.info(
            f"Matching completed: {len(matched_products)} matched, "
            f"{len(unmatched_products)} unmatched in {processing_time:.2f}s"
        )
        
        return results

    def save_results(self, results: Dict[str, Any], output_path: Path) -> None:
        """Save matching results to Excel file.
        
        Args:
            results: Results from match_letters_to_records.
            output_path: Path to save the output Excel file.
        """
        try:
            logger.info(f"Saving results to: {output_path}")
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create DataFrame from products with letter assignments
            data_rows = []
            
            for product in self.products:
                row = {
                    "Range": product.range_name,
                    "Subrange": product.subrange or "",
                    "Model": product.model or "",
                    "Description": product.description or "",
                    "Full_Range": product.full_range,
                    "Full_Name": product.full_name,
                    "Letter_ID": product.letter_id or "",
                    "Has_Letter": "Yes" if product.letter_id else "No",
                }
                
                # Add metadata
                if product.metadata:
                    for key, value in product.metadata.items():
                        if key not in row:
                            row[f"Meta_{key}"] = value
                
                data_rows.append(row)
            
            # Create DataFrame
            df_output = pd.DataFrame(data_rows)
            
            # Create summary statistics
            summary_data = [
                ["Total Products", len(self.products)],
                ["Matched Products", results["matched_records"]],
                ["Unmatched Products", results["unmatched_records"]],
                ["Total Letters", results["total_letters"]],
                ["Processing Time (s)", f"{results['processing_time']:.2f}"],
            ]
            
            df_summary = pd.DataFrame(summary_data, columns=["Metric", "Value"])
            
            # Save to Excel with multiple sheets
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                df_output.to_excel(writer, sheet_name='Products_with_Letters', index=False)
                df_summary.to_excel(writer, sheet_name='Summary', index=False)
                
                # Add letter statistics if available
                if results.get("letter_statistics"):
                    letter_stats_data = []
                    for letter_id, stats in results["letter_statistics"].items():
                        letter_stats_data.append({
                            "Letter_ID": letter_id,
                            "Ranges_Detected": stats["ranges_detected"],
                            "Products_Matched": stats["products_matched"],
                            "Confidence": stats["confidence"],
                        })
                    
                    df_letter_stats = pd.DataFrame(letter_stats_data)
                    df_letter_stats.to_excel(writer, sheet_name='Letter_Statistics', index=False)
            
            logger.info(f"Results saved successfully to {output_path}")
            
        except Exception as e:
            raise ProcessingError(f"Failed to save results: {e}") from e

    def get_excel_info(self) -> Dict[str, Any]:
        """Get information about the loaded Excel file.
        
        Returns:
            Dictionary with Excel file information.
        """
        excel_path = Path(self.config.data.excel_file)
        
        info = {
            "file_path": str(excel_path),
            "exists": excel_path.exists(),
            "loaded": self.excel_data is not None,
        }
        
        if excel_path.exists():
            info["file_size"] = excel_path.stat().st_size
            
            try:
                xl_file = pd.ExcelFile(excel_path)
                info["sheets"] = xl_file.sheet_names
                info["sheet_count"] = len(xl_file.sheet_names)
            except Exception as e:
                info["error"] = f"Could not read Excel structure: {e}"
        
        if self.excel_data is not None:
            info["rows"] = len(self.excel_data)
            info["columns"] = len(self.excel_data.columns)
            info["column_names"] = list(self.excel_data.columns)
        
        if self.products:
            info["products_parsed"] = len(self.products)
            info["ranges_parsed"] = len(self.ranges)
        
        return info 