"""Product Modernization Engine for SE Letters Pipeline.

This module provides comprehensive product modernization capabilities including
database schema management, Sakana tree visualization, and product lifecycle tracking.
"""

import json
import sqlite3
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import re

from ..utils.logger import get_logger
from ..core.exceptions import FileProcessingError

logger = get_logger(__name__)


class ProductStatus(Enum):
    """Product lifecycle status enumeration."""
    ACTIVE = "active"
    OBSOLETE = "obsolete"
    DISCONTINUED = "discontinued"
    REPLACED = "replaced"
    MIGRATED = "migrated"
    UNKNOWN = "unknown"


class ModernizationPathType(Enum):
    """Modernization path type enumeration."""
    DIRECT_REPLACEMENT = "direct_replacement"
    FUNCTIONAL_UPGRADE = "functional_upgrade"
    TECHNOLOGY_MIGRATION = "technology_migration"
    SERIES_EVOLUTION = "series_evolution"
    PLATFORM_CHANGE = "platform_change"


@dataclass
class ProductInfo:
    """Product information data structure."""
    product_id: str
    product_code: str
    product_name: str
    product_range: str
    business_unit: str
    status: ProductStatus
    introduction_date: Optional[datetime] = None
    obsolescence_date: Optional[datetime] = None
    service_end_date: Optional[datetime] = None
    replacement_products: List[str] = field(default_factory=list)
    technical_specs: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModernizationPath:
    """Modernization path data structure."""
    path_id: str
    source_product: str
    target_product: str
    path_type: ModernizationPathType
    confidence_score: float
    migration_complexity: str  # "low", "medium", "high"
    business_impact: str  # "minimal", "moderate", "significant"
    technical_changes: List[str] = field(default_factory=list)
    timeline_estimate: Optional[str] = None
    cost_implications: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SakanaNode:
    """Sakana tree node for modernization visualization."""
    node_id: str
    product_info: ProductInfo
    children: List['SakanaNode'] = field(default_factory=list)
    parent: Optional['SakanaNode'] = None
    depth: int = 0
    modernization_paths: List[ModernizationPath] = field(default_factory=list)
    visualization_data: Dict[str, Any] = field(default_factory=dict)


class ProductModernizationEngine:
    """Comprehensive product modernization engine."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize the modernization engine.
        
        Args:
            db_path: Optional path to database file.
        """
        self.db_path = db_path or Path(tempfile.gettempdir()) / "se_letters_modernization.db"
        self.db_path.parent.mkdir(exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Product range patterns for Schneider Electric
        self.product_patterns = {
            "TeSys": {
                "series": ["TeSys D", "TeSys F", "TeSys T", "TeSys B", "TeSys GV"],
                "evolution": ["TeSys D → TeSys F", "TeSys F → TeSys GV4"],
                "business_unit": "Industrial Automation"
            },
            "PIX": {
                "series": ["PIX Compact", "PIX-DC", "PIX SF6", "PIX 36"],
                "evolution": ["PIX Compact → PIX-DC", "PIX SF6 → PIX 36"],
                "business_unit": "Energy Management"
            },
            "Galaxy": {
                "series": ["Galaxy 3000", "Galaxy 6000", "Galaxy PW", "Galaxy 1000"],
                "evolution": ["Galaxy 3000 → Galaxy 6000", "Galaxy 1000 → Galaxy PW"],
                "business_unit": "Secure Power"
            },
            "Sepam": {
                "series": ["Sepam 1000", "Sepam 2000", "Sepam S40", "Sepam 2040"],
                "evolution": ["Sepam 1000 → Sepam 2000", "Sepam S40 → Sepam 2040"],
                "business_unit": "Energy Management"
            }
        }
        
        # Modernization scoring weights
        self.scoring_weights = {
            "technical_compatibility": 0.3,
            "business_continuity": 0.25,
            "cost_efficiency": 0.2,
            "timeline_feasibility": 0.15,
            "support_availability": 0.1
        }
    
    def _init_database(self):
        """Initialize the modernization database schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Products table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    product_id TEXT PRIMARY KEY,
                    product_code TEXT UNIQUE NOT NULL,
                    product_name TEXT NOT NULL,
                    product_range TEXT NOT NULL,
                    business_unit TEXT NOT NULL,
                    status TEXT NOT NULL,
                    introduction_date TEXT,
                    obsolescence_date TEXT,
                    service_end_date TEXT,
                    technical_specs TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Modernization paths table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS modernization_paths (
                    path_id TEXT PRIMARY KEY,
                    source_product TEXT NOT NULL,
                    target_product TEXT NOT NULL,
                    path_type TEXT NOT NULL,
                    confidence_score REAL NOT NULL,
                    migration_complexity TEXT NOT NULL,
                    business_impact TEXT NOT NULL,
                    technical_changes TEXT,
                    timeline_estimate TEXT,
                    cost_implications TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (source_product) REFERENCES products (product_id),
                    FOREIGN KEY (target_product) REFERENCES products (product_id)
                )
            ''')
            
            # Product relationships table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS product_relationships (
                    relationship_id TEXT PRIMARY KEY,
                    parent_product TEXT NOT NULL,
                    child_product TEXT NOT NULL,
                    relationship_type TEXT NOT NULL,
                    confidence_score REAL NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parent_product) REFERENCES products (product_id),
                    FOREIGN KEY (child_product) REFERENCES products (product_id)
                )
            ''')
            
            # Modernization sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS modernization_sessions (
                    session_id TEXT PRIMARY KEY,
                    document_path TEXT NOT NULL,
                    extraction_results TEXT,
                    modernization_data TEXT,
                    sakana_tree_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")
    
    def analyze_modernization_paths(
        self, 
        extraction_results: Dict[str, Any],
        modernization_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze and create modernization paths from extraction results.
        
        Args:
            extraction_results: Document extraction results.
            modernization_data: Optional modernization data from image processing.
            
        Returns:
            Comprehensive modernization analysis.
        """
        logger.info("Analyzing modernization paths from extraction results")
        
        # Extract product information
        products = self._extract_products_from_results(extraction_results, modernization_data)
        
        # Generate modernization paths
        modernization_paths = self._generate_modernization_paths(products)
        
        # Create Sakana tree structure
        sakana_tree = self._create_sakana_tree(products, modernization_paths)
        
        # Calculate modernization scores
        modernization_scores = self._calculate_modernization_scores(modernization_paths)
        
        # Store in database
        session_id = self._store_modernization_session(
            extraction_results, modernization_data, sakana_tree
        )
        
        analysis_result = {
            "session_id": session_id,
            "products_analyzed": len(products),
            "modernization_paths": len(modernization_paths),
            "sakana_tree": sakana_tree,
            "modernization_scores": modernization_scores,
            "business_intelligence": self._generate_business_intelligence(
                products, modernization_paths
            ),
            "recommendations": self._generate_recommendations(modernization_paths),
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Modernization analysis complete: {len(products)} products, {len(modernization_paths)} paths")
        return analysis_result
    
    def _extract_products_from_results(
        self, 
        extraction_results: Dict[str, Any],
        modernization_data: Optional[Dict[str, Any]]
    ) -> List[ProductInfo]:
        """Extract product information from extraction results.
        
        Args:
            extraction_results: Document extraction results.
            modernization_data: Optional modernization data.
            
        Returns:
            List of extracted product information.
        """
        products = []
        
        # Extract from text content
        text_content = extraction_results.get("text", "")
        text_products = self._extract_products_from_text(text_content)
        products.extend(text_products)
        
        # Extract from modernization data if available
        if modernization_data and modernization_data.get("modernization_content"):
            for content in modernization_data["modernization_content"]:
                # Extract from product mappings
                for mapping in content.get("product_mappings", []):
                    obsolete_product = self._create_product_from_mapping(
                        mapping["obsolete_code"], ProductStatus.OBSOLETE
                    )
                    replacement_product = self._create_product_from_mapping(
                        mapping["replacement_code"], ProductStatus.ACTIVE
                    )
                    
                    products.extend([obsolete_product, replacement_product])
                
                # Extract from replacement tables
                for table in content.get("replacement_tables", []):
                    table_products = self._extract_products_from_table(table)
                    products.extend(table_products)
        
        # Remove duplicates and enrich with database data
        unique_products = self._deduplicate_and_enrich_products(products)
        
        return unique_products
    
    def _extract_products_from_text(self, text: str) -> List[ProductInfo]:
        """Extract product information from text content.
        
        Args:
            text: Text content to analyze.
            
        Returns:
            List of extracted products.
        """
        products = []
        
        # Product code patterns
        product_code_patterns = [
            r'\b([A-Z]{2,4}\d{2,6}[A-Z]*)\b',  # Standard SE codes
            r'\b(LC1[A-Z]\d{2,3}[A-Z]*)\b',    # TeSys D codes
            r'\b(PIX[A-Z0-9\-]+)\b',           # PIX codes
            r'\b(SEPAM[A-Z0-9\-]+)\b',         # Sepam codes
            r'\b(GALAXY[A-Z0-9\-]+)\b'         # Galaxy codes
        ]
        
        for pattern in product_code_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                product_code = match.upper()
                product_range = self._determine_product_range(product_code)
                
                if product_range:
                    product = ProductInfo(
                        product_id=f"extracted_{product_code}",
                        product_code=product_code,
                        product_name=f"{product_range} {product_code}",
                        product_range=product_range,
                        business_unit=self._determine_business_unit(product_range),
                        status=ProductStatus.UNKNOWN,
                        metadata={"extraction_source": "text_pattern"}
                    )
                    products.append(product)
        
        return products
    
    def _create_product_from_mapping(self, product_code: str, status: ProductStatus) -> ProductInfo:
        """Create product info from mapping data.
        
        Args:
            product_code: Product code.
            status: Product status.
            
        Returns:
            ProductInfo object.
        """
        product_range = self._determine_product_range(product_code)
        
        return ProductInfo(
            product_id=f"mapping_{product_code}",
            product_code=product_code,
            product_name=f"{product_range} {product_code}" if product_range else product_code,
            product_range=product_range or "Unknown",
            business_unit=self._determine_business_unit(product_range) if product_range else "Unknown",
            status=status,
            metadata={"extraction_source": "product_mapping"}
        )
    
    def _extract_products_from_table(self, table: Dict[str, Any]) -> List[ProductInfo]:
        """Extract products from table data.
        
        Args:
            table: Table data dictionary.
            
        Returns:
            List of extracted products.
        """
        products = []
        
        for row in table.get("rows", []):
            for key, value in row.items():
                if any(keyword in key.lower() for keyword in ["part", "code", "reference", "product"]):
                    if self._is_valid_product_code(value):
                        product_range = self._determine_product_range(value)
                        
                        product = ProductInfo(
                            product_id=f"table_{value}",
                            product_code=value,
                            product_name=f"{product_range} {value}" if product_range else value,
                            product_range=product_range or "Unknown",
                            business_unit=self._determine_business_unit(product_range) if product_range else "Unknown",
                            status=ProductStatus.UNKNOWN,
                            metadata={"extraction_source": "table_data", "table_type": table.get("type")}
                        )
                        products.append(product)
        
        return products
    
    def _determine_product_range(self, product_code: str) -> Optional[str]:
        """Determine product range from product code.
        
        Args:
            product_code: Product code to analyze.
            
        Returns:
            Product range if identified, None otherwise.
        """
        code_upper = product_code.upper()
        
        # Check against known patterns
        for range_name, range_data in self.product_patterns.items():
            for series in range_data["series"]:
                series_pattern = series.replace(" ", "").replace("-", "")
                if series_pattern in code_upper.replace(" ", "").replace("-", ""):
                    return range_name
        
        # Pattern-based detection
        if code_upper.startswith("LC1"):
            return "TeSys"
        elif "PIX" in code_upper:
            return "PIX"
        elif "SEPAM" in code_upper:
            return "Sepam"
        elif "GALAXY" in code_upper:
            return "Galaxy"
        
        return None
    
    def _determine_business_unit(self, product_range: Optional[str]) -> str:
        """Determine business unit from product range.
        
        Args:
            product_range: Product range.
            
        Returns:
            Business unit name.
        """
        if not product_range:
            return "Unknown"
        
        return self.product_patterns.get(product_range, {}).get("business_unit", "Unknown")
    
    def _is_valid_product_code(self, code: str) -> bool:
        """Check if a string is a valid product code.
        
        Args:
            code: String to check.
            
        Returns:
            True if valid product code.
        """
        if not code or len(code) < 3:
            return False
        
        # Basic pattern matching
        patterns = [
            r'^[A-Z]{2,4}\d{2,6}[A-Z]*$',
            r'^LC1[A-Z]\d{2,3}[A-Z]*$',
            r'^PIX[A-Z0-9\-]+$',
            r'^SEPAM[A-Z0-9\-]+$',
            r'^GALAXY[A-Z0-9\-]+$'
        ]
        
        return any(re.match(pattern, code.upper()) for pattern in patterns)
    
    def _deduplicate_and_enrich_products(self, products: List[ProductInfo]) -> List[ProductInfo]:
        """Remove duplicates and enrich with database data.
        
        Args:
            products: List of products to deduplicate.
            
        Returns:
            Deduplicated and enriched products.
        """
        # Group by product code
        product_dict = {}
        for product in products:
            code = product.product_code
            if code not in product_dict:
                product_dict[code] = product
            else:
                # Merge metadata
                existing = product_dict[code]
                existing.metadata.update(product.metadata)
                
                # Update status if more specific
                if product.status != ProductStatus.UNKNOWN:
                    existing.status = product.status
        
        # Enrich with database data
        enriched_products = []
        for product in product_dict.values():
            enriched = self._enrich_product_from_database(product)
            enriched_products.append(enriched)
        
        return enriched_products
    
    def _enrich_product_from_database(self, product: ProductInfo) -> ProductInfo:
        """Enrich product with database information.
        
        Args:
            product: Product to enrich.
            
        Returns:
            Enriched product.
        """
        # This would query the IBcatalogue database in a real implementation
        # For now, we'll simulate enrichment
        
        # Add simulated dates based on product range
        if product.product_range == "TeSys":
            if "D" in product.product_code:
                product.introduction_date = datetime(2010, 1, 1)
                product.obsolescence_date = datetime(2024, 12, 31)
                product.service_end_date = datetime(2029, 12, 31)
            elif "F" in product.product_code:
                product.introduction_date = datetime(2015, 1, 1)
                product.status = ProductStatus.ACTIVE
        
        # Add technical specifications
        product.technical_specs = self._generate_technical_specs(product)
        
        return product
    
    def _generate_technical_specs(self, product: ProductInfo) -> Dict[str, Any]:
        """Generate technical specifications for a product.
        
        Args:
            product: Product to generate specs for.
            
        Returns:
            Technical specifications dictionary.
        """
        specs = {}
        
        if product.product_range == "TeSys":
            specs = {
                "voltage_range": "24V-690V AC",
                "current_range": "9A-95A",
                "control_voltage": "24V DC, 110V AC, 230V AC",
                "protection_class": "IP20",
                "standards": ["IEC 60947-4-1", "UL 508"]
            }
        elif product.product_range == "PIX":
            specs = {
                "voltage_range": "12kV-36kV",
                "current_range": "630A-4000A",
                "insulation_medium": "SF6 / Vacuum",
                "protection_class": "IP3X",
                "standards": ["IEC 62271-200", "IEEE C37.20.2"]
            }
        elif product.product_range == "Galaxy":
            specs = {
                "power_range": "500VA-1500kVA",
                "voltage_range": "120V-480V",
                "efficiency": "up to 96%",
                "topology": "Double conversion",
                "standards": ["IEC 62040-3", "UL 1778"]
            }
        
        return specs
    
    def _generate_modernization_paths(self, products: List[ProductInfo]) -> List[ModernizationPath]:
        """Generate modernization paths between products.
        
        Args:
            products: List of products to analyze.
            
        Returns:
            List of modernization paths.
        """
        paths = []
        
        # Group products by range
        range_groups = {}
        for product in products:
            range_name = product.product_range
            if range_name not in range_groups:
                range_groups[range_name] = []
            range_groups[range_name].append(product)
        
        # Generate paths within each range
        for range_name, range_products in range_groups.items():
            if range_name in self.product_patterns:
                evolution_paths = self.product_patterns[range_name].get("evolution", [])
                
                for evolution in evolution_paths:
                    if "→" in evolution:
                        source_series, target_series = evolution.split("→")
                        source_series = source_series.strip()
                        target_series = target_series.strip()
                        
                        # Find matching products
                        source_products = [p for p in range_products if source_series in p.product_name]
                        target_products = [p for p in range_products if target_series in p.product_name]
                        
                        # Create paths
                        for source in source_products:
                            for target in target_products:
                                path = self._create_modernization_path(source, target)
                                paths.append(path)
        
        return paths
    
    def _create_modernization_path(self, source: ProductInfo, target: ProductInfo) -> ModernizationPath:
        """Create a modernization path between two products.
        
        Args:
            source: Source product.
            target: Target product.
            
        Returns:
            ModernizationPath object.
        """
        path_id = f"path_{source.product_code}_{target.product_code}"
        
        # Determine path type
        path_type = self._determine_path_type(source, target)
        
        # Calculate confidence score
        confidence_score = self._calculate_path_confidence(source, target)
        
        # Determine complexity and impact
        complexity = self._determine_migration_complexity(source, target)
        impact = self._determine_business_impact(source, target)
        
        # Generate technical changes
        technical_changes = self._generate_technical_changes(source, target)
        
        return ModernizationPath(
            path_id=path_id,
            source_product=source.product_id,
            target_product=target.product_id,
            path_type=path_type,
            confidence_score=confidence_score,
            migration_complexity=complexity,
            business_impact=impact,
            technical_changes=technical_changes,
            timeline_estimate=self._estimate_migration_timeline(complexity),
            cost_implications=self._estimate_cost_implications(complexity, impact),
            metadata={
                "source_range": source.product_range,
                "target_range": target.product_range,
                "business_unit": source.business_unit
            }
        )
    
    def _determine_path_type(self, source: ProductInfo, target: ProductInfo) -> ModernizationPathType:
        """Determine modernization path type.
        
        Args:
            source: Source product.
            target: Target product.
            
        Returns:
            ModernizationPathType.
        """
        if source.product_range == target.product_range:
            if "D" in source.product_code and "F" in target.product_code:
                return ModernizationPathType.SERIES_EVOLUTION
            else:
                return ModernizationPathType.DIRECT_REPLACEMENT
        else:
            return ModernizationPathType.TECHNOLOGY_MIGRATION
    
    def _calculate_path_confidence(self, source: ProductInfo, target: ProductInfo) -> float:
        """Calculate confidence score for modernization path.
        
        Args:
            source: Source product.
            target: Target product.
            
        Returns:
            Confidence score (0.0-1.0).
        """
        score = 0.5  # Base score
        
        # Same range increases confidence
        if source.product_range == target.product_range:
            score += 0.3
        
        # Same business unit increases confidence
        if source.business_unit == target.business_unit:
            score += 0.2
        
        # Known evolution paths increase confidence
        if source.product_range in self.product_patterns:
            evolution_paths = self.product_patterns[source.product_range].get("evolution", [])
            for evolution in evolution_paths:
                if source.product_code in evolution and target.product_code in evolution:
                    score += 0.4
                    break
        
        return min(score, 1.0)
    
    def _determine_migration_complexity(self, source: ProductInfo, target: ProductInfo) -> str:
        """Determine migration complexity.
        
        Args:
            source: Source product.
            target: Target product.
            
        Returns:
            Complexity level: "low", "medium", "high".
        """
        if source.product_range == target.product_range:
            return "low"
        elif source.business_unit == target.business_unit:
            return "medium"
        else:
            return "high"
    
    def _determine_business_impact(self, source: ProductInfo, target: ProductInfo) -> str:
        """Determine business impact of migration.
        
        Args:
            source: Source product.
            target: Target product.
            
        Returns:
            Impact level: "minimal", "moderate", "significant".
        """
        if source.product_range == target.product_range:
            return "minimal"
        elif source.business_unit == target.business_unit:
            return "moderate"
        else:
            return "significant"
    
    def _generate_technical_changes(self, source: ProductInfo, target: ProductInfo) -> List[str]:
        """Generate list of technical changes required for migration.
        
        Args:
            source: Source product.
            target: Target product.
            
        Returns:
            List of technical changes.
        """
        changes = []
        
        if source.product_range != target.product_range:
            changes.append(f"Product range change: {source.product_range} → {target.product_range}")
        
        if source.business_unit != target.business_unit:
            changes.append(f"Business unit change: {source.business_unit} → {target.business_unit}")
        
        # Add specific technical changes based on product types
        if source.product_range == "TeSys" and target.product_range == "TeSys":
            if "D" in source.product_code and "F" in target.product_code:
                changes.extend([
                    "Wiring terminal layout changes",
                    "Control voltage compatibility check required",
                    "Mounting dimensions verification needed"
                ])
        
        return changes
    
    def _estimate_migration_timeline(self, complexity: str) -> str:
        """Estimate migration timeline based on complexity.
        
        Args:
            complexity: Migration complexity level.
            
        Returns:
            Timeline estimate.
        """
        timelines = {
            "low": "1-2 weeks",
            "medium": "1-3 months",
            "high": "3-6 months"
        }
        return timelines.get(complexity, "Unknown")
    
    def _estimate_cost_implications(self, complexity: str, impact: str) -> str:
        """Estimate cost implications of migration.
        
        Args:
            complexity: Migration complexity.
            impact: Business impact.
            
        Returns:
            Cost implications description.
        """
        cost_matrix = {
            ("low", "minimal"): "Low cost - primarily product cost difference",
            ("low", "moderate"): "Low to medium cost - some engineering time required",
            ("medium", "minimal"): "Medium cost - engineering and testing required",
            ("medium", "moderate"): "Medium to high cost - significant engineering effort",
            ("high", "moderate"): "High cost - major project with training required",
            ("high", "significant"): "Very high cost - complete system redesign may be needed"
        }
        
        return cost_matrix.get((complexity, impact), "Cost assessment required")
    
    def _create_sakana_tree(self, products: List[ProductInfo], paths: List[ModernizationPath]) -> Dict[str, Any]:
        """Create Sakana tree structure for modernization visualization.
        
        Args:
            products: List of products.
            paths: List of modernization paths.
            
        Returns:
            Sakana tree structure.
        """
        # Create nodes for each product
        nodes = {}
        for product in products:
            node = SakanaNode(
                node_id=product.product_id,
                product_info=product,
                visualization_data={
                    "color": self._get_node_color(product),
                    "size": self._get_node_size(product),
                    "shape": self._get_node_shape(product),
                    "label": product.product_code
                }
            )
            nodes[product.product_id] = node
        
        # Build relationships based on modernization paths
        for path in paths:
            if path.source_product in nodes and path.target_product in nodes:
                source_node = nodes[path.source_product]
                target_node = nodes[path.target_product]
                
                # Add path to source node
                source_node.modernization_paths.append(path)
                
                # Create parent-child relationship
                if path.path_type in [ModernizationPathType.DIRECT_REPLACEMENT, ModernizationPathType.SERIES_EVOLUTION]:
                    target_node.parent = source_node
                    source_node.children.append(target_node)
        
        # Calculate tree structure
        root_nodes = [node for node in nodes.values() if node.parent is None]
        self._calculate_tree_depths(root_nodes)
        
        # Generate tree visualization data
        tree_data = {
            "nodes": [self._serialize_node(node) for node in nodes.values()],
            "edges": [self._serialize_path(path) for path in paths],
            "root_nodes": [node.node_id for node in root_nodes],
            "tree_stats": {
                "total_nodes": len(nodes),
                "total_edges": len(paths),
                "max_depth": max([node.depth for node in nodes.values()], default=0),
                "root_count": len(root_nodes)
            }
        }
        
        return tree_data
    
    def _get_node_color(self, product: ProductInfo) -> str:
        """Get visualization color for product node.
        
        Args:
            product: Product information.
            
        Returns:
            Color code.
        """
        status_colors = {
            ProductStatus.ACTIVE: "#00cc66",
            ProductStatus.OBSOLETE: "#ff3333",
            ProductStatus.DISCONTINUED: "#ff6b35",
            ProductStatus.REPLACED: "#ffcc00",
            ProductStatus.MIGRATED: "#00ff88",
            ProductStatus.UNKNOWN: "#cccccc"
        }
        return status_colors.get(product.status, "#cccccc")
    
    def _get_node_size(self, product: ProductInfo) -> int:
        """Get visualization size for product node.
        
        Args:
            product: Product information.
            
        Returns:
            Node size.
        """
        # Size based on product importance or usage
        if product.status == ProductStatus.ACTIVE:
            return 20
        elif product.status == ProductStatus.OBSOLETE:
            return 15
        else:
            return 10
    
    def _get_node_shape(self, product: ProductInfo) -> str:
        """Get visualization shape for product node.
        
        Args:
            product: Product information.
            
        Returns:
            Node shape.
        """
        range_shapes = {
            "TeSys": "circle",
            "PIX": "square",
            "Galaxy": "triangle",
            "Sepam": "diamond"
        }
        return range_shapes.get(product.product_range, "circle")
    
    def _calculate_tree_depths(self, root_nodes: List[SakanaNode]):
        """Calculate depth for each node in the tree.
        
        Args:
            root_nodes: List of root nodes.
        """
        def calculate_depth(node: SakanaNode, depth: int = 0):
            node.depth = depth
            for child in node.children:
                calculate_depth(child, depth + 1)
        
        for root in root_nodes:
            calculate_depth(root)
    
    def _serialize_node(self, node: SakanaNode) -> Dict[str, Any]:
        """Serialize node for JSON output.
        
        Args:
            node: SakanaNode to serialize.
            
        Returns:
            Serialized node data.
        """
        return {
            "id": node.node_id,
            "product_code": node.product_info.product_code,
            "product_name": node.product_info.product_name,
            "product_range": node.product_info.product_range,
            "business_unit": node.product_info.business_unit,
            "status": node.product_info.status.value,
            "depth": node.depth,
            "parent": node.parent.node_id if node.parent else None,
            "children": [child.node_id for child in node.children],
            "visualization": node.visualization_data,
            "modernization_paths_count": len(node.modernization_paths)
        }
    
    def _serialize_path(self, path: ModernizationPath) -> Dict[str, Any]:
        """Serialize modernization path for JSON output.
        
        Args:
            path: ModernizationPath to serialize.
            
        Returns:
            Serialized path data.
        """
        return {
            "id": path.path_id,
            "source": path.source_product,
            "target": path.target_product,
            "type": path.path_type.value,
            "confidence": path.confidence_score,
            "complexity": path.migration_complexity,
            "impact": path.business_impact,
            "technical_changes": path.technical_changes,
            "timeline": path.timeline_estimate,
            "cost": path.cost_implications
        }
    
    def _calculate_modernization_scores(self, paths: List[ModernizationPath]) -> Dict[str, Any]:
        """Calculate comprehensive modernization scores.
        
        Args:
            paths: List of modernization paths.
            
        Returns:
            Modernization scores and analytics.
        """
        if not paths:
            return {"error": "No modernization paths to analyze"}
        
        # Calculate average scores
        avg_confidence = sum(path.confidence_score for path in paths) / len(paths)
        
        # Complexity distribution
        complexity_dist = {}
        for path in paths:
            complexity = path.migration_complexity
            complexity_dist[complexity] = complexity_dist.get(complexity, 0) + 1
        
        # Impact distribution
        impact_dist = {}
        for path in paths:
            impact = path.business_impact
            impact_dist[impact] = impact_dist.get(impact, 0) + 1
        
        # Path type distribution
        type_dist = {}
        for path in paths:
            path_type = path.path_type.value
            type_dist[path_type] = type_dist.get(path_type, 0) + 1
        
        # Recommendations based on scores
        recommendations = []
        if avg_confidence > 0.8:
            recommendations.append("High confidence paths available - proceed with modernization")
        elif avg_confidence > 0.6:
            recommendations.append("Moderate confidence - additional validation recommended")
        else:
            recommendations.append("Low confidence - detailed analysis required")
        
        return {
            "average_confidence": avg_confidence,
            "total_paths": len(paths),
            "complexity_distribution": complexity_dist,
            "impact_distribution": impact_dist,
            "path_type_distribution": type_dist,
            "recommendations": recommendations,
            "score_breakdown": {
                "high_confidence_paths": len([p for p in paths if p.confidence_score > 0.8]),
                "medium_confidence_paths": len([p for p in paths if 0.6 <= p.confidence_score <= 0.8]),
                "low_confidence_paths": len([p for p in paths if p.confidence_score < 0.6])
            }
        }
    
    def _generate_business_intelligence(
        self, 
        products: List[ProductInfo], 
        paths: List[ModernizationPath]
    ) -> Dict[str, Any]:
        """Generate business intelligence insights.
        
        Args:
            products: List of products.
            paths: List of modernization paths.
            
        Returns:
            Business intelligence data.
        """
        # Product status analysis
        status_counts = {}
        for product in products:
            status = product.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Business unit analysis
        bu_counts = {}
        for product in products:
            bu = product.business_unit
            bu_counts[bu] = bu_counts.get(bu, 0) + 1
        
        # Range analysis
        range_counts = {}
        for product in products:
            range_name = product.product_range
            range_counts[range_name] = range_counts.get(range_name, 0) + 1
        
        # Migration urgency analysis
        obsolete_products = [p for p in products if p.status == ProductStatus.OBSOLETE]
        urgent_migrations = []
        
        for product in obsolete_products:
            if product.service_end_date:
                days_until_eol = (product.service_end_date - datetime.now()).days
                if days_until_eol < 365:  # Less than 1 year
                    urgent_migrations.append({
                        "product_code": product.product_code,
                        "days_until_eol": days_until_eol,
                        "service_end_date": product.service_end_date.isoformat()
                    })
        
        return {
            "product_analysis": {
                "total_products": len(products),
                "status_distribution": status_counts,
                "business_unit_distribution": bu_counts,
                "range_distribution": range_counts
            },
            "migration_analysis": {
                "total_paths": len(paths),
                "urgent_migrations": urgent_migrations,
                "migration_readiness": self._assess_migration_readiness(paths)
            },
            "risk_assessment": {
                "high_risk_products": len([p for p in products if p.status == ProductStatus.OBSOLETE]),
                "products_without_paths": len(products) - len(set(p.source_product for p in paths)),
                "complex_migrations": len([p for p in paths if p.migration_complexity == "high"])
            }
        }
    
    def _assess_migration_readiness(self, paths: List[ModernizationPath]) -> str:
        """Assess overall migration readiness.
        
        Args:
            paths: List of modernization paths.
            
        Returns:
            Migration readiness assessment.
        """
        if not paths:
            return "No migration paths identified"
        
        high_confidence = len([p for p in paths if p.confidence_score > 0.8])
        total_paths = len(paths)
        
        readiness_ratio = high_confidence / total_paths
        
        if readiness_ratio > 0.8:
            return "High readiness - most paths have high confidence"
        elif readiness_ratio > 0.5:
            return "Moderate readiness - some paths need validation"
        else:
            return "Low readiness - detailed analysis required"
    
    def _generate_recommendations(self, paths: List[ModernizationPath]) -> List[Dict[str, Any]]:
        """Generate actionable recommendations.
        
        Args:
            paths: List of modernization paths.
            
        Returns:
            List of recommendations.
        """
        recommendations = []
        
        # High confidence paths
        high_confidence_paths = [p for p in paths if p.confidence_score > 0.8]
        if high_confidence_paths:
            recommendations.append({
                "priority": "High",
                "category": "Quick Wins",
                "title": "Implement High-Confidence Migrations",
                "description": f"Proceed with {len(high_confidence_paths)} high-confidence migration paths",
                "paths": [p.path_id for p in high_confidence_paths[:5]],  # Top 5
                "timeline": "1-3 months",
                "impact": "Immediate risk reduction"
            })
        
        # Low complexity paths
        low_complexity_paths = [p for p in paths if p.migration_complexity == "low"]
        if low_complexity_paths:
            recommendations.append({
                "priority": "Medium",
                "category": "Easy Migrations",
                "title": "Execute Low-Complexity Migrations",
                "description": f"Start with {len(low_complexity_paths)} low-complexity migrations",
                "paths": [p.path_id for p in low_complexity_paths[:3]],
                "timeline": "2-4 weeks",
                "impact": "Quick progress with minimal disruption"
            })
        
        # High impact paths
        high_impact_paths = [p for p in paths if p.business_impact == "significant"]
        if high_impact_paths:
            recommendations.append({
                "priority": "High",
                "category": "Strategic Migrations",
                "title": "Plan Strategic High-Impact Migrations",
                "description": f"Carefully plan {len(high_impact_paths)} high-impact migrations",
                "paths": [p.path_id for p in high_impact_paths[:3]],
                "timeline": "6-12 months",
                "impact": "Major business transformation"
            })
        
        return recommendations
    
    def _store_modernization_session(
        self, 
        extraction_results: Dict[str, Any],
        modernization_data: Optional[Dict[str, Any]],
        sakana_tree: Dict[str, Any]
    ) -> str:
        """Store modernization session in database.
        
        Args:
            extraction_results: Document extraction results.
            modernization_data: Modernization data.
            sakana_tree: Sakana tree structure.
            
        Returns:
            Session ID.
        """
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO modernization_sessions 
                (session_id, document_path, extraction_results, modernization_data, sakana_tree_data)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                session_id,
                extraction_results.get("document_path", "unknown"),
                json.dumps(extraction_results),
                json.dumps(modernization_data) if modernization_data else None,
                json.dumps(sakana_tree)
            ))
            conn.commit()
        
        return session_id
    
    def get_modernization_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get modernization session history.
        
        Args:
            limit: Maximum number of sessions to return.
            
        Returns:
            List of session summaries.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT session_id, document_path, created_at, 
                       json_extract(sakana_tree_data, '$.tree_stats') as tree_stats
                FROM modernization_sessions
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
            
            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    "session_id": row[0],
                    "document_path": row[1],
                    "created_at": row[2],
                    "tree_stats": json.loads(row[3]) if row[3] else {}
                })
            
            return sessions 