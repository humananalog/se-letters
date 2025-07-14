#!/usr/bin/env python3
"""
PSIBS Power Systems Intelligence Filter
Advanced intelligence engine for PSIBS (Power Systems) medium voltage equipment classification

Specializes in:
- Medium Voltage Switchgear (PIX, RM6, SM6, etc.)
- Voltage Classification (6kV, 12kV, 15kV, 17.5kV, 24kV, 36kV)
- Current Ratings and Power Handling
- Switchgear Technology (Ring Main Units, Gas Insulated, Air Insulated)
- Application Types (Distribution, Industrial, Utility)
- Modernization Path Intelligence

Data Source: PIX2B_Phase_out_Letter grok_metadata.json
Product Line: PSIBS (Power Systems)
Test Case: PIX Double Bus Bar (PIX 2B) - Medium Voltage Switchgear

Version: 1.0.0
Author: SE Letters Team - PSIBS Intelligence
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import re

from loguru import logger


class PSIBSVoltageClass(Enum):
    """PSIBS voltage classifications for medium voltage equipment"""
    LOW_MV = "6-12kV"      # Low Medium Voltage
    MID_MV = "12-17.5kV"   # Mid Medium Voltage  
    HIGH_MV = "17.5-24kV"  # High Medium Voltage
    EXTENDED_MV = "24-36kV" # Extended Medium Voltage


class PSIBSProductFamily(Enum):
    """PSIBS product families in power systems"""
    PIX = "PIX"                    # Double Bus Bar Switchgear
    RM6 = "RM6"                    # Ring Main Units
    SM6 = "SM6"                    # Compact Switchgear
    FLUOFIX = "FLUOFIX"            # Gas Insulated Switchgear
    NEXUS = "NEXUS"                # Air Insulated Switchgear
    EVOLIS = "EVOLIS"              # Distribution Switchgear
    OKAIKEN = "OKAIKEN"            # Compact Switchgear
    XIRIA = "XIRIA"                # Ring Main Units


class PSIBSApplicationType(Enum):
    """PSIBS application types"""
    DISTRIBUTION = "Distribution"           # Electrical distribution
    INDUSTRIAL = "Industrial"              # Industrial applications
    UTILITY = "Utility"                    # Utility networks
    COMMERCIAL = "Commercial"              # Commercial buildings
    INFRASTRUCTURE = "Infrastructure"       # Critical infrastructure
    RENEWABLE = "Renewable"                # Renewable energy


class PSIBSTechnology(Enum):
    """PSIBS switchgear technologies"""
    AIR_INSULATED = "Air Insulated"        # AIS - Air Insulated Switchgear
    GAS_INSULATED = "Gas Insulated"        # GIS - Gas Insulated Switchgear  
    VACUUM_CIRCUIT = "Vacuum Circuit"      # Vacuum circuit breakers
    SF6_INSULATED = "SF6 Insulated"        # SF6 gas insulated
    SOLID_INSULATED = "Solid Insulated"    # Solid insulation technology


@dataclass
class PSIBSClassificationResult:
    """PSIBS product classification result"""
    product_identifier: str
    product_family: PSIBSProductFamily
    voltage_class: PSIBSVoltageClass
    application_type: PSIBSApplicationType
    technology_type: PSIBSTechnology
    current_rating: str
    power_rating: Optional[str]
    frequency: str
    configuration: str
    modernization_path: str
    confidence_score: float
    classification_details: Dict[str, Any]


@dataclass
class PSIBSIntelligenceResult:
    """Complete PSIBS intelligence analysis result"""
    total_products: int
    psibs_products: List[PSIBSClassificationResult]
    voltage_distribution: Dict[str, int]
    family_distribution: Dict[str, int]
    application_distribution: Dict[str, int]
    technology_distribution: Dict[str, int]
    modernization_recommendations: List[Dict[str, Any]]
    processing_time_ms: float
    avg_confidence: float
    high_confidence_rate: float


class PSIBSPowerSystemsFilter:
    """
    Advanced PSIBS Power Systems Intelligence Filter
    
    Provides comprehensive classification and analysis of PSIBS medium voltage equipment
    including switchgear, distribution equipment, and modernization intelligence.
    """
    
    def __init__(self):
        """Initialize PSIBS Power Systems Intelligence Filter"""
        logger.info("🔋 Initializing PSIBS Power Systems Intelligence Filter")
        
        # PSIBS Product Family Intelligence Database
        self.product_family_patterns = {
            PSIBSProductFamily.PIX: {
                "patterns": [r"PIX\s*(?:2B|DB|Double\s*Bus)", r"PIX\s*Double\s*Bus\s*Bar"],
                "keywords": ["pix", "double bus bar", "2b", "db"],
                "voltage_range": ["12kV", "17.5kV", "24kV"],
                "applications": [PSIBSApplicationType.DISTRIBUTION, PSIBSApplicationType.UTILITY],
                "technology": PSIBSTechnology.AIR_INSULATED,
                "description": "Double Bus Bar Switchgear for reliable power distribution"
            },
            PSIBSProductFamily.RM6: {
                "patterns": [r"RM6", r"Ring\s*Main\s*Unit"],
                "keywords": ["rm6", "ring main", "compact switchgear"],
                "voltage_range": ["12kV", "17.5kV", "24kV"],
                "applications": [PSIBSApplicationType.DISTRIBUTION, PSIBSApplicationType.COMMERCIAL],
                "technology": PSIBSTechnology.GAS_INSULATED,
                "description": "Compact Ring Main Units for urban distribution"
            },
            PSIBSProductFamily.SM6: {
                "patterns": [r"SM6", r"Compact\s*Switchgear"],
                "keywords": ["sm6", "compact", "modular"],
                "voltage_range": ["6kV", "12kV", "17.5kV"],
                "applications": [PSIBSApplicationType.INDUSTRIAL, PSIBSApplicationType.COMMERCIAL],
                "technology": PSIBSTechnology.GAS_INSULATED,
                "description": "Modular Compact Switchgear for industrial applications"
            },
            PSIBSProductFamily.FLUOFIX: {
                "patterns": [r"FLUOFIX", r"Gas\s*Insulated"],
                "keywords": ["fluofix", "gas insulated", "sf6"],
                "voltage_range": ["12kV", "17.5kV", "24kV", "36kV"],
                "applications": [PSIBSApplicationType.UTILITY, PSIBSApplicationType.INFRASTRUCTURE],
                "technology": PSIBSTechnology.SF6_INSULATED,
                "description": "SF6 Gas Insulated Switchgear for critical applications"
            },
            PSIBSProductFamily.NEXUS: {
                "patterns": [r"NEXUS", r"Air\s*Insulated"],
                "keywords": ["nexus", "air insulated", "outdoor"],
                "voltage_range": ["12kV", "17.5kV", "24kV", "36kV"],
                "applications": [PSIBSApplicationType.UTILITY, PSIBSApplicationType.INDUSTRIAL],
                "technology": PSIBSTechnology.AIR_INSULATED,
                "description": "Air Insulated Switchgear for outdoor installations"
            }
        }
        
        # Voltage Classification Intelligence
        self.voltage_classifiers = {
            PSIBSVoltageClass.LOW_MV: {
                "range": (6.0, 12.0),
                "typical_values": ["6kV", "7.2kV", "11kV", "12kV"],
                "applications": ["Industrial", "Commercial"],
                "description": "Low Medium Voltage for industrial and commercial applications"
            },
            PSIBSVoltageClass.MID_MV: {
                "range": (12.0, 17.5),
                "typical_values": ["12kV", "13.8kV", "15kV", "17.5kV"],
                "applications": ["Distribution", "Utility"],
                "description": "Mid Medium Voltage for distribution networks"
            },
            PSIBSVoltageClass.HIGH_MV: {
                "range": (17.5, 24.0),
                "typical_values": ["20kV", "22kV", "24kV"],
                "applications": ["Utility", "Infrastructure"],
                "description": "High Medium Voltage for utility networks"
            },
            PSIBSVoltageClass.EXTENDED_MV: {
                "range": (24.0, 36.0),
                "typical_values": ["27kV", "33kV", "36kV"],
                "applications": ["Transmission", "Utility"],
                "description": "Extended Medium Voltage for transmission applications"
            }
        }
        
        # Current Rating Classifications
        self.current_ratings = {
            "Low": {"range": (0, 630), "typical": "up to 630A", "applications": ["Commercial", "Small Industrial"]},
            "Medium": {"range": (630, 1250), "typical": "630-1250A", "applications": ["Industrial", "Distribution"]},
            "High": {"range": (1250, 2500), "typical": "1250-2500A", "applications": ["Utility", "Large Industrial"]},
            "Extra High": {"range": (2500, 5000), "typical": "2500-5000A", "applications": ["Transmission", "Major Utility"]}
        }
        
        # Modernization Intelligence Database
        self.modernization_paths = {
            PSIBSProductFamily.PIX: {
                "current_generation": "PIX 2B (Withdrawn)",
                "recommended_replacement": "EcoStruxure Power",
                "migration_complexity": "Medium",
                "migration_timeline": "12-18 months",
                "key_benefits": ["Digital connectivity", "Predictive maintenance", "Enhanced safety"],
                "technical_compatibility": "Direct replacement with enhanced features"
            },
            PSIBSProductFamily.RM6: {
                "current_generation": "RM6 Series",
                "recommended_replacement": "RM AirSeT or FlexSeT",
                "migration_complexity": "Low",
                "migration_timeline": "6-12 months",
                "key_benefits": ["SF6-free technology", "Improved environmental impact", "Same footprint"],
                "technical_compatibility": "Drop-in replacement"
            },
            PSIBSProductFamily.SM6: {
                "current_generation": "SM6 Series",
                "recommended_replacement": "SM AirSeT",
                "migration_complexity": "Medium",
                "migration_timeline": "12-18 months",
                "key_benefits": ["SF6-free operation", "Digital ready", "Reduced maintenance"],
                "technical_compatibility": "Compatible with existing infrastructure"
            }
        }
        
        logger.info("✅ PSIBS Power Systems Filter initialized with comprehensive intelligence")
    
    def classify_psibs_product(self, product_data: Dict[str, Any]) -> Optional[PSIBSClassificationResult]:
        """Classify a single PSIBS product with advanced intelligence"""
        try:
            product_id = product_data.get('product_identifier', '')
            range_label = product_data.get('range_label', '')
            description = product_data.get('product_description', '')
            product_line = product_data.get('product_line', '')
            
            # Check if this is a PSIBS product
            if 'PSIBS' not in product_line and 'Power Systems' not in product_line:
                return None
            
            # Classify product family
            product_family = self._classify_product_family(product_id, range_label, description)
            if not product_family:
                return None
            
            # Extract technical specifications
            voltage_class = self._classify_voltage(product_data)
            current_rating = self._extract_current_rating(product_data)
            power_rating = self._extract_power_rating(product_data)
            frequency = self._extract_frequency(product_data)
            
            # Determine application type
            application_type = self._determine_application_type(product_family, voltage_class, description)
            
            # Identify technology type
            technology_type = self._identify_technology_type(product_family, description)
            
            # Generate configuration details
            configuration = self._analyze_configuration(product_id, range_label, description)
            
            # Generate modernization path
            modernization_path = self._generate_modernization_path(product_family, voltage_class)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(product_data, product_family)
            
            # Generate classification details
            classification_details = {
                "family_match_confidence": 0.95 if product_family else 0.0,
                "voltage_extraction_method": "technical_specifications",
                "current_rating_source": "specifications",
                "modernization_reasoning": f"Based on {product_family.value} family analysis",
                "psibs_indicators": self._extract_psibs_indicators(product_data)
            }
            
            return PSIBSClassificationResult(
                product_identifier=product_id,
                product_family=product_family,
                voltage_class=voltage_class,
                application_type=application_type,
                technology_type=technology_type,
                current_rating=current_rating,
                power_rating=power_rating,
                frequency=frequency,
                configuration=configuration,
                modernization_path=modernization_path,
                confidence_score=confidence_score,
                classification_details=classification_details
            )
            
        except Exception as e:
            logger.error(f"❌ Error classifying PSIBS product: {e}")
            return None
    
    def _classify_product_family(self, product_id: str, range_label: str, description: str) -> Optional[PSIBSProductFamily]:
        """Classify PSIBS product family using pattern matching"""
        text_to_analyze = f"{product_id} {range_label} {description}".lower()
        
        best_match = None
        best_score = 0.0
        
        for family, config in self.product_family_patterns.items():
            score = 0.0
            
            # Pattern matching
            for pattern in config["patterns"]:
                if re.search(pattern, text_to_analyze, re.IGNORECASE):
                    score += 0.5
            
            # Keyword matching
            for keyword in config["keywords"]:
                if keyword in text_to_analyze:
                    score += 0.3
            
            if score > best_score:
                best_score = score
                best_match = family
        
        return best_match if best_score > 0.3 else None
    
    def _classify_voltage(self, product_data: Dict[str, Any]) -> PSIBSVoltageClass:
        """Classify voltage level from technical specifications"""
        # Check technical specifications first
        tech_specs = product_data.get('technical_specifications', {})
        voltage_levels = tech_specs.get('voltage_levels', [])
        
        if voltage_levels:
            # Extract voltage value from first voltage level
            voltage_str = voltage_levels[0]
            voltage_value = self._extract_voltage_value(voltage_str)
            
            for voltage_class, config in self.voltage_classifiers.items():
                min_voltage, max_voltage = config["range"]
                if min_voltage <= voltage_value <= max_voltage:
                    return voltage_class
        
        # Fallback to description analysis
        description = product_data.get('product_description', '')
        if 'medium voltage' in description.lower():
            return PSIBSVoltageClass.MID_MV
        
        return PSIBSVoltageClass.MID_MV  # Default for PSIBS
    
    def _extract_voltage_value(self, voltage_str: str) -> float:
        """Extract numerical voltage value from string"""
        # Handle ranges like "12 – 17.5kV"
        voltage_match = re.search(r'(\d+(?:\.\d+)?)', voltage_str)
        if voltage_match:
            return float(voltage_match.group(1))
        return 12.0  # Default
    
    def _extract_current_rating(self, product_data: Dict[str, Any]) -> str:
        """Extract current rating from technical specifications"""
        tech_specs = product_data.get('technical_specifications', {})
        current_ratings = tech_specs.get('current_ratings', [])
        
        if current_ratings:
            return current_ratings[0]
        
        # Try to extract from description
        description = product_data.get('product_description', '')
        current_match = re.search(r'(\d+(?:,\d+)?)\s*A', description)
        if current_match:
            return f"{current_match.group(1)}A"
        
        return "Not specified"
    
    def _extract_power_rating(self, product_data: Dict[str, Any]) -> Optional[str]:
        """Extract power rating from technical specifications"""
        tech_specs = product_data.get('technical_specifications', {})
        power_ratings = tech_specs.get('power_ratings', [])
        
        if power_ratings:
            return power_ratings[0]
        
        return None
    
    def _extract_frequency(self, product_data: Dict[str, Any]) -> str:
        """Extract frequency from technical specifications"""
        tech_specs = product_data.get('technical_specifications', {})
        frequencies = tech_specs.get('frequencies', [])
        
        if frequencies:
            return frequencies[0]
        
        return "50/60Hz"  # Standard default
    
    def _determine_application_type(self, family: PSIBSProductFamily, voltage: PSIBSVoltageClass, description: str) -> PSIBSApplicationType:
        """Determine application type based on family and voltage"""
        family_config = self.product_family_patterns.get(family, {})
        typical_applications = family_config.get("applications", [])
        
        if typical_applications:
            return typical_applications[0]  # Primary application
        
        # Fallback based on voltage level
        if voltage in [PSIBSVoltageClass.LOW_MV]:
            return PSIBSApplicationType.INDUSTRIAL
        elif voltage in [PSIBSVoltageClass.MID_MV]:
            return PSIBSApplicationType.DISTRIBUTION
        else:
            return PSIBSApplicationType.UTILITY
    
    def _identify_technology_type(self, family: PSIBSProductFamily, description: str) -> PSIBSTechnology:
        """Identify technology type based on family and description"""
        family_config = self.product_family_patterns.get(family, {})
        return family_config.get("technology", PSIBSTechnology.AIR_INSULATED)
    
    def _analyze_configuration(self, product_id: str, range_label: str, description: str) -> str:
        """Analyze product configuration"""
        config_indicators = []
        
        text = f"{product_id} {range_label} {description}".lower()
        
        if 'double bus' in text or '2b' in text:
            config_indicators.append("Double Bus Bar Configuration")
        
        if 'ring main' in text:
            config_indicators.append("Ring Main Unit Configuration")
        
        if 'compact' in text:
            config_indicators.append("Compact Design")
        
        if 'modular' in text:
            config_indicators.append("Modular Architecture")
        
        if 'outdoor' in text:
            config_indicators.append("Outdoor Installation")
        
        if 'indoor' in text:
            config_indicators.append("Indoor Installation")
        
        return "; ".join(config_indicators) if config_indicators else "Standard Configuration"
    
    def _generate_modernization_path(self, family: PSIBSProductFamily, voltage: PSIBSVoltageClass) -> str:
        """Generate modernization recommendation"""
        modernization_config = self.modernization_paths.get(family, {})
        
        if modernization_config:
            replacement = modernization_config.get("recommended_replacement", "EcoStruxure Power")
            complexity = modernization_config.get("migration_complexity", "Medium")
            timeline = modernization_config.get("migration_timeline", "12-18 months")
            
            return f"Migrate to {replacement} ({complexity} complexity, {timeline})"
        
        return "Evaluate EcoStruxure Power modernization options"
    
    def _calculate_confidence_score(self, product_data: Dict[str, Any], family: Optional[PSIBSProductFamily]) -> float:
        """Calculate confidence score for PSIBS classification"""
        confidence = 0.0
        
        # Base PSIBS identification
        product_line = product_data.get('product_line', '')
        if 'PSIBS' in product_line:
            confidence += 0.3
        if 'Power Systems' in product_line:
            confidence += 0.2
        
        # Product family identification
        if family:
            confidence += 0.3
        
        # Technical specifications availability
        tech_specs = product_data.get('technical_specifications', {})
        if tech_specs.get('voltage_levels'):
            confidence += 0.1
        if tech_specs.get('current_ratings'):
            confidence += 0.05
        if tech_specs.get('frequencies'):
            confidence += 0.05
        
        # Description quality
        description = product_data.get('product_description', '')
        if len(description) > 50:
            confidence += 0.1
        if 'medium voltage' in description.lower():
            confidence += 0.05
        
        return min(confidence, 1.0)
    
    def _extract_psibs_indicators(self, product_data: Dict[str, Any]) -> List[str]:
        """Extract PSIBS-specific indicators"""
        indicators = []
        
        product_line = product_data.get('product_line', '')
        if 'PSIBS' in product_line:
            indicators.append("PSIBS Product Line")
        if 'Power Systems' in product_line:
            indicators.append("Power Systems Division")
        
        description = product_data.get('product_description', '').lower()
        if 'medium voltage' in description:
            indicators.append("Medium Voltage Equipment")
        if 'switchgear' in description:
            indicators.append("Switchgear Technology")
        if 'bus bar' in description:
            indicators.append("Bus Bar System")
        
        return indicators
    
    def analyze_grok_metadata(self, grok_file_path: str) -> PSIBSIntelligenceResult:
        """Analyze grok metadata file for PSIBS intelligence"""
        start_time = time.time()
        
        try:
            # Load grok metadata
            with open(grok_file_path, 'r') as f:
                grok_data = json.load(f)
            
            logger.info(f"📊 Analyzing PSIBS products from: {grok_file_path}")
            
            # Extract products
            products = grok_data.get('products', [])
            total_products = len(products)
            
            logger.info(f"📦 Found {total_products} products to analyze")
            
            # Classify each product
            psibs_products = []
            for product in products:
                result = self.classify_psibs_product(product)
                if result:
                    psibs_products.append(result)
                    logger.info(f"✅ PSIBS Product: {result.product_identifier} ({result.product_family.value})")
            
            # Generate distribution analytics
            voltage_distribution = {}
            family_distribution = {}
            application_distribution = {}
            technology_distribution = {}
            
            for product in psibs_products:
                # Voltage distribution
                voltage_key = product.voltage_class.value
                voltage_distribution[voltage_key] = voltage_distribution.get(voltage_key, 0) + 1
                
                # Family distribution
                family_key = product.product_family.value
                family_distribution[family_key] = family_distribution.get(family_key, 0) + 1
                
                # Application distribution
                app_key = product.application_type.value
                application_distribution[app_key] = application_distribution.get(app_key, 0) + 1
                
                # Technology distribution
                tech_key = product.technology_type.value
                technology_distribution[tech_key] = technology_distribution.get(tech_key, 0) + 1
            
            # Generate modernization recommendations
            modernization_recommendations = []
            for product in psibs_products:
                modernization_config = self.modernization_paths.get(product.product_family, {})
                if modernization_config:
                    recommendation = {
                        "product": product.product_identifier,
                        "current_status": "Obsolete/Withdrawn",
                        "recommended_replacement": modernization_config.get("recommended_replacement"),
                        "migration_complexity": modernization_config.get("migration_complexity"),
                        "timeline": modernization_config.get("migration_timeline"),
                        "key_benefits": modernization_config.get("key_benefits", [])
                    }
                    modernization_recommendations.append(recommendation)
            
            # Calculate performance metrics
            processing_time_ms = (time.time() - start_time) * 1000
            avg_confidence = sum(p.confidence_score for p in psibs_products) / len(psibs_products) if psibs_products else 0.0
            high_confidence_rate = len([p for p in psibs_products if p.confidence_score >= 0.8]) / len(psibs_products) if psibs_products else 0.0
            
            logger.info(f"⚡ PSIBS Analysis completed in {processing_time_ms:.2f}ms")
            logger.info(f"📊 PSIBS Products: {len(psibs_products)}/{total_products}")
            logger.info(f"🎯 Average Confidence: {avg_confidence:.1%}")
            
            return PSIBSIntelligenceResult(
                total_products=total_products,
                psibs_products=psibs_products,
                voltage_distribution=voltage_distribution,
                family_distribution=family_distribution,
                application_distribution=application_distribution,
                technology_distribution=technology_distribution,
                modernization_recommendations=modernization_recommendations,
                processing_time_ms=processing_time_ms,
                avg_confidence=avg_confidence,
                high_confidence_rate=high_confidence_rate
            )
            
        except Exception as e:
            logger.error(f"❌ PSIBS analysis failed: {e}")
            raise
    
    def save_results(self, result: PSIBSIntelligenceResult, output_dir: str = ".") -> Dict[str, str]:
        """Save PSIBS analysis results to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"psibs_power_systems_{timestamp}"
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        files_created = {}
        
        try:
            # Save detailed JSON results
            json_file = output_path / f"{base_name}.json"
            with open(json_file, 'w') as f:
                json.dump(asdict(result), f, indent=2, default=str)
            files_created['json'] = str(json_file)
            
            # Save summary text report
            summary_file = output_path / f"{base_name}_summary.txt"
            with open(summary_file, 'w') as f:
                f.write("PSIBS POWER SYSTEMS INTELLIGENCE ANALYSIS\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Processing Time: {result.processing_time_ms:.2f}ms\n")
                f.write(f"Total Products Analyzed: {result.total_products}\n")
                f.write(f"PSIBS Products Found: {len(result.psibs_products)}\n")
                f.write(f"Average Confidence: {result.avg_confidence:.1%}\n")
                f.write(f"High Confidence Rate: {result.high_confidence_rate:.1%}\n\n")
                
                f.write("VOLTAGE CLASS DISTRIBUTION:\n")
                f.write("-" * 30 + "\n")
                for voltage, count in result.voltage_distribution.items():
                    percentage = (count / len(result.psibs_products)) * 100 if result.psibs_products else 0
                    f.write(f"{voltage}: {count} products ({percentage:.1f}%)\n")
                
                f.write("\nPRODUCT FAMILY DISTRIBUTION:\n")
                f.write("-" * 30 + "\n")
                for family, count in result.family_distribution.items():
                    percentage = (count / len(result.psibs_products)) * 100 if result.psibs_products else 0
                    f.write(f"{family}: {count} products ({percentage:.1f}%)\n")
                
                f.write("\nMODERNIZATION RECOMMENDATIONS:\n")
                f.write("-" * 30 + "\n")
                for i, rec in enumerate(result.modernization_recommendations, 1):
                    f.write(f"{i}. {rec['product']}\n")
                    f.write(f"   → Replace with: {rec['recommended_replacement']}\n")
                    f.write(f"   → Complexity: {rec['migration_complexity']}\n")
                    f.write(f"   → Timeline: {rec['timeline']}\n\n")
            
            files_created['summary'] = str(summary_file)
            
            # Save Excel report if pandas available
            try:
                import pandas as pd
                
                excel_file = output_path / f"{base_name}.xlsx"
                with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                    # Products sheet
                    products_data = []
                    for product in result.psibs_products:
                        products_data.append({
                            'Product ID': product.product_identifier,
                            'Family': product.product_family.value,
                            'Voltage Class': product.voltage_class.value,
                            'Application': product.application_type.value,
                            'Technology': product.technology_type.value,
                            'Current Rating': product.current_rating,
                            'Configuration': product.configuration,
                            'Modernization Path': product.modernization_path,
                            'Confidence': f"{product.confidence_score:.1%}"
                        })
                    
                    products_df = pd.DataFrame(products_data)
                    products_df.to_excel(writer, sheet_name='PSIBS Products', index=False)
                    
                    # Summary sheet
                    summary_data = {
                        'Metric': ['Total Products', 'PSIBS Products', 'Average Confidence', 'High Confidence Rate', 'Processing Time'],
                        'Value': [
                            result.total_products,
                            len(result.psibs_products),
                            f"{result.avg_confidence:.1%}",
                            f"{result.high_confidence_rate:.1%}",
                            f"{result.processing_time_ms:.2f}ms"
                        ]
                    }
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                files_created['excel'] = str(excel_file)
                
            except ImportError:
                logger.warning("📊 Pandas not available, skipping Excel export")
            
            logger.info(f"💾 PSIBS results saved: {len(files_created)} files created")
            return files_created
            
        except Exception as e:
            logger.error(f"❌ Failed to save PSIBS results: {e}")
            return {}


def main():
    """Test PSIBS Power Systems Filter with PIX data"""
    
    # Initialize filter
    filter_engine = PSIBSPowerSystemsFilter()
    
    # Test with PIX2B grok metadata
    grok_file = "../../data/output/json_outputs/PIX2B_Phase_out_Letter_22/20250714_213459/grok_metadata.json"
    
    if not Path(grok_file).exists():
        logger.error(f"❌ Grok metadata file not found: {grok_file}")
        return
    
    logger.info(f"🔍 Testing PSIBS Filter with: {grok_file}")
    
    # Analyze the file
    result = filter_engine.analyze_grok_metadata(grok_file)
    
    # Display results
    logger.info("📊 PSIBS POWER SYSTEMS INTELLIGENCE RESULTS")
    logger.info("=" * 60)
    logger.info(f"⚡ Processing Time: {result.processing_time_ms:.2f}ms")
    logger.info(f"📦 Products Analyzed: {result.total_products}")
    logger.info(f"🔋 PSIBS Products: {len(result.psibs_products)}")
    logger.info(f"🎯 Average Confidence: {result.avg_confidence:.1%}")
    logger.info(f"📈 High Confidence Rate: {result.high_confidence_rate:.1%}")
    
    if result.psibs_products:
        logger.info("\n🔋 PSIBS PRODUCTS IDENTIFIED:")
        for i, product in enumerate(result.psibs_products, 1):
            logger.info(f"{i}. {product.product_identifier}")
            logger.info(f"   Family: {product.product_family.value}")
            logger.info(f"   Voltage: {product.voltage_class.value}")
            logger.info(f"   Application: {product.application_type.value}")
            logger.info(f"   Technology: {product.technology_type.value}")
            logger.info(f"   Current: {product.current_rating}")
            logger.info(f"   Confidence: {product.confidence_score:.1%}")
            logger.info(f"   Modernization: {product.modernization_path}")
    
    if result.modernization_recommendations:
        logger.info("\n🚀 MODERNIZATION RECOMMENDATIONS:")
        for i, rec in enumerate(result.modernization_recommendations, 1):
            logger.info(f"{i}. {rec['product']} → {rec['recommended_replacement']}")
            logger.info(f"   Complexity: {rec['migration_complexity']}")
            logger.info(f"   Timeline: {rec['timeline']}")
    
    # Save results
    files_created = filter_engine.save_results(result)
    
    if files_created:
        logger.info("\n💾 FILES CREATED:")
        for file_type, file_path in files_created.items():
            logger.info(f"📄 {file_type.upper()}: {file_path}")


if __name__ == "__main__":
    main() 