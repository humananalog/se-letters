#!/usr/bin/env python3
"""
SEPAM Protection Relay Filter - Secret Sauce Implementation
Advanced filtering and intelligence for SEPAM protection relays using Schneider Electric coding rules

SECRET SAUCE: Sepam_Relay_Coding_Rules_Guide.markdown
- Comprehensive SEPAM series intelligence (10, 20, 40, 60, 80)
- Application type mapping (S, T, M, G, B, C)
- Hardware configuration validation
- Communication protocol intelligence
- Model variant detection and correlation

Version: 1.0.0 - SEPAM Intelligence
Author: SE Letters Team
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import time
from loguru import logger

# Add src to path for SOTA service
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from se_letters.services.sota_product_database_service import (
    SOTAProductDatabaseService, ProductMatch, SearchResult
)


class SEPAMSeries(Enum):
    """SEPAM series classification based on coding rules"""
    SERIES_10 = "10"  # Basic protection for medium voltage networks
    SERIES_20 = "20"  # Standard protection for distribution systems
    SERIES_40 = "40"  # Demanding applications with enhanced features
    SERIES_60 = "60"  # Complex distribution systems
    SERIES_80 = "80"  # Advanced applications with custom protection


class SEPAMApplication(Enum):
    """SEPAM application types based on coding rules"""
    SUBSTATION = "S"     # Substation protection
    TRANSFORMER = "T"    # Transformer protection
    MOTOR = "M"         # Motor protection
    GENERATOR = "G"     # Generator protection
    BUSBAR = "B"        # Busbar protection
    CAPACITOR = "C"     # Capacitor protection


@dataclass
class SEPAMProduct:
    """SEPAM product with enhanced intelligence"""
    product_identifier: str
    range_label: str
    subrange_label: str
    series: Optional[SEPAMSeries] = None
    application: Optional[SEPAMApplication] = None
    model_variant: Optional[str] = None
    protection_functions: List[str] = None
    communication_protocols: List[str] = None
    hardware_options: List[str] = None
    obsolescence_status: Optional[str] = None
    replacement_suggestions: Optional[str] = None
    confidence_score: float = 0.0


@dataclass
class SEPAMFilterResult:
    """Result of SEPAM filtering with intelligence analysis"""
    original_products: List[Dict[str, Any]]
    sepam_products: List[SEPAMProduct]
    micom_products: List[SEPAMProduct]  # Related protection relays
    powerlogic_products: List[SEPAMProduct]  # Replacement products
    series_analysis: Dict[str, Any]
    application_analysis: Dict[str, Any]
    modernization_recommendations: List[Dict[str, Any]]
    obsolescence_timeline: Dict[str, Any]
    processing_time_ms: float
    confidence_summary: Dict[str, float]


class SEPAMProtectionRelayFilter:
    """
    Advanced SEPAM protection relay filter with secret sauce intelligence
    
    Secret Sauce Components:
    1. SEPAM Series Intelligence (10, 20, 40, 60, 80)
    2. Application Type Detection (S, T, M, G, B, C)
    3. Model Variant Recognition (S20, S24, T20, S62, etc.)
    4. Protection Function Mapping
    5. Communication Protocol Intelligence
    6. Hardware Configuration Analysis
    7. Obsolescence Timeline Analysis
    8. Modernization Path Intelligence
    """
    
    def __init__(self):
        """Initialize SEPAM filter with coding rules intelligence"""
        self.sota_service = SOTAProductDatabaseService()
        
        # SEPAM Coding Rules - SECRET SAUCE
        self.sepam_series_mapping = {
            "10": {
                "name": "Series 10",
                "description": "Basic protection for medium voltage networks",
                "applications": ["S10", "T10", "M10"],
                "communication": ["Modbus"],
                "complexity": "Basic"
            },
            "20": {
                "name": "Series 20", 
                "description": "Standard protection for distribution systems",
                "applications": ["S20", "S24", "T20", "T24", "M20", "B21", "B22"],
                "communication": ["Modbus", "IEC61850"],
                "complexity": "Standard"
            },
            "40": {
                "name": "Series 40",
                "description": "Demanding applications with enhanced features", 
                "applications": ["S40", "S42", "T40", "T42", "M40"],
                "communication": ["Modbus", "IEC61850", "DNP3"],
                "complexity": "Enhanced"
            },
            "60": {
                "name": "Series 60",
                "description": "Complex distribution systems",
                "applications": ["S60", "S62", "T60", "T62", "M61", "G60", "G62", "C60"],
                "communication": ["Modbus", "IEC61850", "DNP3"],
                "complexity": "Complex"
            },
            "80": {
                "name": "Series 80",
                "description": "Advanced applications with custom protection",
                "applications": ["S80", "S81", "S84", "T81", "M80", "G80", "C86"],
                "communication": ["Modbus", "IEC61850", "DNP3", "TCP/IP"],
                "complexity": "Advanced"
            }
        }
        
        self.application_mapping = {
            "S": {
                "name": "Substation Protection",
                "description": "Substation protection with overcurrent and earth fault",
                "protection_functions": ["overcurrent", "earth_fault", "directional"]
            },
            "T": {
                "name": "Transformer Protection", 
                "description": "Transformer protection with differential and gas relay",
                "protection_functions": ["differential", "gas_relay", "temperature"]
            },
            "M": {
                "name": "Motor Protection",
                "description": "Motor protection with overload and thermal",
                "protection_functions": ["overload", "thermal", "undervoltage"]
            },
            "G": {
                "name": "Generator Protection",
                "description": "Generator protection with reverse power and frequency",
                "protection_functions": ["reverse_power", "frequency", "voltage"]
            },
            "B": {
                "name": "Busbar Protection",
                "description": "Busbar protection with differential and interlocking",
                "protection_functions": ["differential", "interlocking", "zone_selective"]
            },
            "C": {
                "name": "Capacitor Protection",
                "description": "Capacitor protection with unbalance and overvoltage",
                "protection_functions": ["unbalance", "overvoltage", "overcurrent"]
            }
        }
        
        # Hardware options mapping
        self.hardware_mapping = {
            "MES114F": "10 inputs, 4 outputs I/O module",
            "MET148-2": "8 temperature monitoring inputs",
            "ACE990": "Core balance CT interface",
            "ACE919CA": "RS485 communication interface"
        }
        
        # Communication protocol capabilities
        self.communication_capabilities = {
            "Modbus": {"series": ["10", "20", "40", "60", "80"], "description": "Legacy SCADA integration"},
            "IEC61850": {"series": ["20", "40", "60", "80"], "description": "Smart grid integration"},
            "DNP3": {"series": ["40", "60", "80"], "description": "Advanced SCADA protocol"},
            "TCP/IP": {"series": ["60", "80"], "description": "Ethernet communication"}
        }
        
        logger.info("🛡️ SEPAM Protection Relay Filter initialized with secret sauce")
        logger.info("📋 Series supported: 10, 20, 40, 60, 80")
        logger.info("⚡ Applications: Substation, Transformer, Motor, Generator, Busbar, Capacitor")
    
    def apply_sepam_intelligence_filter(self, products: List[Dict[str, Any]]) -> SEPAMFilterResult:
        """
        Apply comprehensive SEPAM intelligence filtering using secret sauce
        
        Args:
            products: List of products from document extraction
            
        Returns:
            SEPAMFilterResult with detailed analysis and intelligence
        """
        start_time = time.time()
        
        logger.info("🛡️ Applying SEPAM Protection Relay Intelligence Filter")
        logger.info(f"📋 Input products: {len(products)}")
        
        # Classify products by type
        sepam_products = []
        micom_products = []
        powerlogic_products = []
        
        for product in products:
            range_label = product.get('range_label', '').upper()
            
            if 'SEPAM' in range_label:
                sepam_product = self._analyze_sepam_product(product)
                sepam_products.append(sepam_product)
                
            elif 'MICOM' in range_label:
                micom_product = self._analyze_micom_product(product)
                micom_products.append(micom_product)
                
            elif 'POWERLOGIC' in range_label:
                powerlogic_product = self._analyze_powerlogic_product(product)
                powerlogic_products.append(powerlogic_product)
        
        # Perform series analysis
        series_analysis = self._analyze_series_distribution(sepam_products)
        
        # Perform application analysis
        application_analysis = self._analyze_application_distribution(sepam_products)
        
        # Generate modernization recommendations
        modernization_recommendations = self._generate_modernization_recommendations(
            sepam_products, micom_products, powerlogic_products
        )
        
        # Analyze obsolescence timeline
        obsolescence_timeline = self._analyze_obsolescence_timeline(
            sepam_products + micom_products + powerlogic_products
        )
        
        # Calculate confidence summary
        confidence_summary = self._calculate_confidence_summary(
            sepam_products + micom_products + powerlogic_products
        )
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        logger.info(f"✅ SEPAM Intelligence Filter completed in {processing_time_ms:.2f}ms")
        logger.info(f"🛡️ SEPAM products: {len(sepam_products)}")
        logger.info(f"⚡ MiCOM products: {len(micom_products)}")
        logger.info(f"🔧 PowerLogic products: {len(powerlogic_products)}")
        
        return SEPAMFilterResult(
            original_products=products,
            sepam_products=sepam_products,
            micom_products=micom_products,
            powerlogic_products=powerlogic_products,
            series_analysis=series_analysis,
            application_analysis=application_analysis,
            modernization_recommendations=modernization_recommendations,
            obsolescence_timeline=obsolescence_timeline,
            processing_time_ms=processing_time_ms,
            confidence_summary=confidence_summary
        )
    
    def _analyze_sepam_product(self, product: Dict[str, Any]) -> SEPAMProduct:
        """Analyze SEPAM product using coding rules intelligence"""
        
        product_identifier = product.get('product_identifier', '')
        range_label = product.get('range_label', '')
        subrange_label = product.get('subrange_label', '')
        
        # Extract series from subrange (e.g., "20" from "SEPAM 20")
        series = self._extract_sepam_series(subrange_label)
        
        # Determine application type
        application = self._determine_application_type(product_identifier, subrange_label)
        
        # Extract model variant
        model_variant = self._extract_model_variant(subrange_label, series, application)
        
        # Determine protection functions
        protection_functions = self._determine_protection_functions(series, application, model_variant)
        
        # Determine communication protocols
        communication_protocols = self._determine_communication_protocols(series)
        
        # Analyze hardware options
        hardware_options = self._analyze_hardware_options(series, application)
        
        # Calculate confidence score
        confidence_score = self._calculate_sepam_confidence(
            series, application, model_variant, protection_functions
        )
        
        logger.info(f"🛡️ SEPAM Analysis: {product_identifier}")
        logger.info(f"   📊 Series: {series.value if series else 'Unknown'}")
        logger.info(f"   ⚡ Application: {application.value if application else 'Unknown'}")
        logger.info(f"   🔧 Model: {model_variant}")
        logger.info(f"   📈 Confidence: {confidence_score:.3f}")
        
        return SEPAMProduct(
            product_identifier=product_identifier,
            range_label=range_label,
            subrange_label=subrange_label,
            series=series,
            application=application,
            model_variant=model_variant,
            protection_functions=protection_functions,
            communication_protocols=communication_protocols,
            hardware_options=hardware_options,
            obsolescence_status=product.get('obsolescence_status'),
            replacement_suggestions=product.get('replacement_suggestions'),
            confidence_score=confidence_score
        )
    
    def _analyze_micom_product(self, product: Dict[str, Any]) -> SEPAMProduct:
        """Analyze MiCOM product (related protection relay)"""
        
        product_identifier = product.get('product_identifier', '')
        range_label = product.get('range_label', '')
        subrange_label = product.get('subrange_label', '')
        
        # MiCOM products are typically equivalent to SEPAM 20-40 series
        # P20 -> Series 20 equivalent, P521 -> Series 40 equivalent
        series = self._map_micom_to_sepam_series(subrange_label)
        
        # MiCOM applications are typically substation or transformer protection
        application = SEPAMApplication.SUBSTATION  # Default for MiCOM
        
        model_variant = f"MiCOM_{subrange_label}"
        
        protection_functions = ["overcurrent", "earth_fault", "directional", "monitoring"]
        communication_protocols = ["Modbus", "IEC61850"]
        hardware_options = ["MES114F", "ACE919CA"]
        
        confidence_score = 0.85  # High confidence for MiCOM mapping
        
        logger.info(f"⚡ MiCOM Analysis: {product_identifier}")
        logger.info(f"   📊 Equivalent Series: {series.value if series else 'Unknown'}")
        logger.info(f"   📈 Confidence: {confidence_score:.3f}")
        
        return SEPAMProduct(
            product_identifier=product_identifier,
            range_label=range_label,
            subrange_label=subrange_label,
            series=series,
            application=application,
            model_variant=model_variant,
            protection_functions=protection_functions,
            communication_protocols=communication_protocols,
            hardware_options=hardware_options,
            obsolescence_status=product.get('obsolescence_status'),
            replacement_suggestions=product.get('replacement_suggestions'),
            confidence_score=confidence_score
        )
    
    def _analyze_powerlogic_product(self, product: Dict[str, Any]) -> SEPAMProduct:
        """Analyze PowerLogic product (replacement/modernization option)"""
        
        product_identifier = product.get('product_identifier', '')
        range_label = product.get('range_label', '')
        subrange_label = product.get('subrange_label', '')
        
        # PowerLogic is typically Series 60-80 equivalent
        series = SEPAMSeries.SERIES_60  # Modern series
        application = SEPAMApplication.SUBSTATION  # Versatile application
        
        model_variant = f"PowerLogic_{subrange_label}"
        
        protection_functions = ["advanced_overcurrent", "power_quality", "monitoring", "communication"]
        communication_protocols = ["Modbus", "IEC61850", "DNP3", "TCP/IP"]
        hardware_options = ["MES114F", "MET148-2", "ACE919CA"]
        
        confidence_score = 0.90  # High confidence for PowerLogic (modern)
        
        logger.info(f"🔧 PowerLogic Analysis: {product_identifier}")
        logger.info(f"   📊 Modern Series: {series.value}")
        logger.info(f"   📈 Confidence: {confidence_score:.3f}")
        
        return SEPAMProduct(
            product_identifier=product_identifier,
            range_label=range_label,
            subrange_label=subrange_label,
            series=series,
            application=application,
            model_variant=model_variant,
            protection_functions=protection_functions,
            communication_protocols=communication_protocols,
            hardware_options=hardware_options,
            obsolescence_status=product.get('obsolescence_status'),
            replacement_suggestions=product.get('replacement_suggestions'),
            confidence_score=confidence_score
        )
    
    def _extract_sepam_series(self, subrange_label: str) -> Optional[SEPAMSeries]:
        """Extract SEPAM series from subrange using coding rules"""
        if not subrange_label:
            return None
        
        # Look for series numbers in subrange
        series_patterns = {
            r'10': SEPAMSeries.SERIES_10,
            r'20': SEPAMSeries.SERIES_20, 
            r'40': SEPAMSeries.SERIES_40,
            r'60': SEPAMSeries.SERIES_60,
            r'80': SEPAMSeries.SERIES_80
        }
        
        for pattern, series in series_patterns.items():
            if re.search(pattern, subrange_label):
                return series
        
        return None
    
    def _determine_application_type(self, product_identifier: str, subrange_label: str) -> Optional[SEPAMApplication]:
        """Determine application type using coding rules patterns"""
        
        # Check for application indicators in product identifier or subrange
        text = f"{product_identifier} {subrange_label}".upper()
        
        if re.search(r'S\d+', text):
            return SEPAMApplication.SUBSTATION
        elif re.search(r'T\d+', text):
            return SEPAMApplication.TRANSFORMER
        elif re.search(r'M\d+', text):
            return SEPAMApplication.MOTOR
        elif re.search(r'G\d+', text):
            return SEPAMApplication.GENERATOR
        elif re.search(r'B\d+', text):
            return SEPAMApplication.BUSBAR
        elif re.search(r'C\d+', text):
            return SEPAMApplication.CAPACITOR
        
        # Default to substation for general SEPAM products
        return SEPAMApplication.SUBSTATION
    
    def _extract_model_variant(self, subrange_label: str, series: Optional[SEPAMSeries], 
                             application: Optional[SEPAMApplication]) -> str:
        """Extract specific model variant using coding rules"""
        
        if not series or not application:
            return subrange_label
        
        # Build model variant based on series and application
        series_num = series.value
        app_letter = application.value
        
        # Look for specific variants in the series mapping
        if series_num in self.sepam_series_mapping:
            series_info = self.sepam_series_mapping[series_num]
            applications = series_info["applications"]
            
            # Find matching application in the series
            for app in applications:
                if app.startswith(app_letter) and app[1:] in subrange_label:
                    return app
        
        # Fallback to constructed variant
        return f"{app_letter}{series_num}"
    
    def _determine_protection_functions(self, series: Optional[SEPAMSeries], 
                                     application: Optional[SEPAMApplication],
                                     model_variant: str) -> List[str]:
        """Determine protection functions based on series and application"""
        
        base_functions = []
        
        if application:
            app_info = self.application_mapping.get(application.value, {})
            base_functions.extend(app_info.get("protection_functions", []))
        
        # Add series-specific enhancements
        if series:
            if series in [SEPAMSeries.SERIES_60, SEPAMSeries.SERIES_80]:
                base_functions.extend(["advanced_monitoring", "power_quality", "harmonics"])
            
            if series == SEPAMSeries.SERIES_80:
                base_functions.extend(["custom_logic", "advanced_communication"])
        
        return list(set(base_functions))  # Remove duplicates
    
    def _determine_communication_protocols(self, series: Optional[SEPAMSeries]) -> List[str]:
        """Determine available communication protocols based on series"""
        
        if not series:
            return ["Modbus"]  # Default
        
        series_num = series.value
        
        protocols = []
        for protocol, info in self.communication_capabilities.items():
            if series_num in info["series"]:
                protocols.append(protocol)
        
        return protocols
    
    def _analyze_hardware_options(self, series: Optional[SEPAMSeries], 
                                application: Optional[SEPAMApplication]) -> List[str]:
        """Analyze available hardware options based on series and application"""
        
        hardware_options = []
        
        # Base I/O module for most series
        if series and series != SEPAMSeries.SERIES_10:
            hardware_options.append("MES114F")
        
        # Temperature monitoring for transformer applications
        if application == SEPAMApplication.TRANSFORMER:
            hardware_options.append("MET148-2")
        
        # Core balance CT for earth fault protection
        if application in [SEPAMApplication.SUBSTATION, SEPAMApplication.TRANSFORMER]:
            hardware_options.append("ACE990")
        
        # RS485 communication for most applications
        hardware_options.append("ACE919CA")
        
        return hardware_options
    
    def _map_micom_to_sepam_series(self, subrange_label: str) -> Optional[SEPAMSeries]:
        """Map MiCOM products to equivalent SEPAM series"""
        
        # MiCOM mapping to SEPAM equivalents
        micom_mapping = {
            'P20': SEPAMSeries.SERIES_20,
            'P40': SEPAMSeries.SERIES_40,
            'P521': SEPAMSeries.SERIES_40,  # Advanced differential relay
            'P122': SEPAMSeries.SERIES_20,
            'P139': SEPAMSeries.SERIES_40
        }
        
        return micom_mapping.get(subrange_label, SEPAMSeries.SERIES_20)
    
    def _calculate_sepam_confidence(self, series: Optional[SEPAMSeries], 
                                  application: Optional[SEPAMApplication],
                                  model_variant: str, 
                                  protection_functions: List[str]) -> float:
        """Calculate confidence score for SEPAM analysis"""
        
        confidence = 0.0
        
        # Series detection confidence
        if series:
            confidence += 0.30
        
        # Application detection confidence  
        if application:
            confidence += 0.25
        
        # Model variant confidence
        if model_variant and len(model_variant) > 2:
            confidence += 0.20
        
        # Protection functions confidence
        if protection_functions:
            confidence += min(len(protection_functions) * 0.05, 0.25)
        
        return min(confidence, 1.0)
    
    def _analyze_series_distribution(self, sepam_products: List[SEPAMProduct]) -> Dict[str, Any]:
        """Analyze distribution of SEPAM series"""
        
        series_count = {}
        total_products = len(sepam_products)
        
        for product in sepam_products:
            if product.series:
                series_name = f"Series {product.series.value}"
                series_count[series_name] = series_count.get(series_name, 0) + 1
        
        # Calculate percentages
        series_distribution = {}
        for series, count in series_count.items():
            percentage = (count / total_products * 100) if total_products > 0 else 0
            series_distribution[series] = {
                "count": count,
                "percentage": percentage,
                "complexity": self.sepam_series_mapping.get(series.split()[-1], {}).get("complexity", "Unknown")
            }
        
        return {
            "total_sepam_products": total_products,
            "series_distribution": series_distribution,
            "most_common_series": max(series_count.keys(), key=series_count.get) if series_count else None
        }
    
    def _analyze_application_distribution(self, sepam_products: List[SEPAMProduct]) -> Dict[str, Any]:
        """Analyze distribution of SEPAM applications"""
        
        app_count = {}
        total_products = len(sepam_products)
        
        for product in sepam_products:
            if product.application:
                app_name = self.application_mapping[product.application.value]["name"]
                app_count[app_name] = app_count.get(app_name, 0) + 1
        
        # Calculate percentages
        app_distribution = {}
        for app, count in app_count.items():
            percentage = (count / total_products * 100) if total_products > 0 else 0
            app_distribution[app] = {
                "count": count,
                "percentage": percentage
            }
        
        return {
            "total_applications": len(app_count),
            "application_distribution": app_distribution,
            "primary_application": max(app_count.keys(), key=app_count.get) if app_count else None
        }
    
    def _generate_modernization_recommendations(self, sepam_products: List[SEPAMProduct],
                                              micom_products: List[SEPAMProduct], 
                                              powerlogic_products: List[SEPAMProduct]) -> List[Dict[str, Any]]:
        """Generate modernization recommendations based on obsolescence analysis"""
        
        recommendations = []
        
        # Analyze obsolete SEPAM products
        for product in sepam_products:
            if product.obsolescence_status and "End of" in product.obsolescence_status:
                recommendation = {
                    "obsolete_product": product.product_identifier,
                    "series": product.series.value if product.series else "Unknown",
                    "application": product.application.value if product.application else "Unknown",
                    "recommendation_type": "modernization",
                    "recommended_series": "60" if product.series in [SEPAMSeries.SERIES_10, SEPAMSeries.SERIES_20] else "80",
                    "modernization_benefits": [
                        "Enhanced communication protocols",
                        "Advanced protection functions", 
                        "Improved monitoring capabilities",
                        "Smart grid compatibility"
                    ],
                    "migration_complexity": "Medium" if product.series == SEPAMSeries.SERIES_20 else "High"
                }
                recommendations.append(recommendation)
        
        # Analyze obsolete MiCOM products
        for product in micom_products:
            if product.obsolescence_status and "End of" in product.obsolescence_status:
                # Check if PowerLogic replacement is available
                powerlogic_replacement = None
                for pl_product in powerlogic_products:
                    if pl_product.obsolescence_status == "Active":
                        powerlogic_replacement = pl_product.product_identifier
                        break
                
                recommendation = {
                    "obsolete_product": product.product_identifier,
                    "product_type": "MiCOM Protection Relay",
                    "recommendation_type": "direct_replacement",
                    "recommended_product": powerlogic_replacement or "PowerLogic P5 Series",
                    "modernization_benefits": [
                        "Maintained protection philosophy",
                        "Enhanced monitoring capabilities",
                        "Improved communication options",
                        "Extended support lifecycle"
                    ],
                    "migration_complexity": "Low"
                }
                recommendations.append(recommendation)
        
        return recommendations
    
    def _analyze_obsolescence_timeline(self, all_products: List[SEPAMProduct]) -> Dict[str, Any]:
        """Analyze obsolescence timeline across all protection relay products"""
        
        obsolete_products = []
        active_products = []
        
        for product in all_products:
            if product.obsolescence_status:
                if "End of" in product.obsolescence_status:
                    obsolete_products.append({
                        "product": product.product_identifier,
                        "series": product.series.value if product.series else "Unknown",
                        "status": product.obsolescence_status
                    })
                elif product.obsolescence_status == "Active":
                    active_products.append({
                        "product": product.product_identifier,
                        "series": product.series.value if product.series else "Unknown"
                    })
        
        return {
            "obsolete_count": len(obsolete_products),
            "active_count": len(active_products),
            "obsolete_products": obsolete_products,
            "active_products": active_products,
            "obsolescence_rate": (len(obsolete_products) / len(all_products) * 100) if all_products else 0
        }
    
    def _calculate_confidence_summary(self, all_products: List[SEPAMProduct]) -> Dict[str, float]:
        """Calculate confidence summary across all products"""
        
        if not all_products:
            return {"average_confidence": 0.0, "high_confidence_rate": 0.0}
        
        confidences = [product.confidence_score for product in all_products]
        average_confidence = sum(confidences) / len(confidences)
        
        high_confidence_count = sum(1 for conf in confidences if conf >= 0.8)
        high_confidence_rate = (high_confidence_count / len(confidences)) * 100
        
        return {
            "average_confidence": average_confidence,
            "high_confidence_rate": high_confidence_rate,
            "total_products_analyzed": len(all_products)
        }


def test_sepam_filter_on_grok_metadata():
    """Test SEPAM filter on the provided grok_metadata.json"""
    
    logger.info("🧪 Testing SEPAM Filter on grok_metadata.json")
    
    # Load grok metadata
    grok_file = Path("data/output/json_outputs/SEPAM2040_PWP_Notice_20/latest/grok_metadata.json")
    
    if not grok_file.exists():
        logger.error(f"❌ Grok metadata file not found: {grok_file}")
        return
    
    with open(grok_file, 'r') as f:
        grok_data = json.load(f)
    
    products = grok_data.get('products', [])
    
    logger.info(f"📋 Loaded {len(products)} products from grok metadata")
    for i, product in enumerate(products, 1):
        logger.info(f"   {i}. {product.get('product_identifier')} - {product.get('obsolescence_status')}")
    
    # Apply SEPAM filter
    sepam_filter = SEPAMProtectionRelayFilter()
    result = sepam_filter.apply_sepam_intelligence_filter(products)
    
    # Display results
    print("\n" + "="*80)
    print("🛡️ SEPAM PROTECTION RELAY INTELLIGENCE FILTER RESULTS")
    print("="*80)
    
    print(f"\n📊 PROCESSING SUMMARY:")
    print(f"   ⏱️ Processing Time: {result.processing_time_ms:.2f}ms")
    print(f"   📋 Total Products: {len(result.original_products)}")
    print(f"   🛡️ SEPAM Products: {len(result.sepam_products)}")
    print(f"   ⚡ MiCOM Products: {len(result.micom_products)}")
    print(f"   🔧 PowerLogic Products: {len(result.powerlogic_products)}")
    
    print(f"\n🛡️ SEPAM PRODUCTS ANALYSIS:")
    for product in result.sepam_products:
        print(f"   📦 {product.product_identifier}")
        print(f"      📊 Series: {product.series.value if product.series else 'Unknown'}")
        print(f"      ⚡ Application: {product.application.value if product.application else 'Unknown'}")
        print(f"      🔧 Model: {product.model_variant}")
        print(f"      📈 Confidence: {product.confidence_score:.3f}")
        print(f"      🔴 Status: {product.obsolescence_status}")
    
    print(f"\n⚡ MiCOM PRODUCTS ANALYSIS:")
    for product in result.micom_products:
        print(f"   📦 {product.product_identifier}")
        print(f"      📊 Equivalent Series: {product.series.value if product.series else 'Unknown'}")
        print(f"      📈 Confidence: {product.confidence_score:.3f}")
        print(f"      🔴 Status: {product.obsolescence_status}")
    
    print(f"\n🔧 POWERLOGIC PRODUCTS ANALYSIS:")
    for product in result.powerlogic_products:
        print(f"   📦 {product.product_identifier}")
        print(f"      📊 Modern Series: {product.series.value if product.series else 'Unknown'}")
        print(f"      📈 Confidence: {product.confidence_score:.3f}")
        print(f"      🟢 Status: {product.obsolescence_status}")
    
    print(f"\n📊 SERIES ANALYSIS:")
    series_analysis = result.series_analysis
    print(f"   📋 Total SEPAM Products: {series_analysis['total_sepam_products']}")
    if series_analysis.get('most_common_series'):
        print(f"   🏆 Most Common Series: {series_analysis['most_common_series']}")
    
    for series, info in series_analysis.get('series_distribution', {}).items():
        print(f"   📊 {series}: {info['count']} products ({info['percentage']:.1f}%) - {info['complexity']} complexity")
    
    print(f"\n⚡ APPLICATION ANALYSIS:")
    app_analysis = result.application_analysis
    if app_analysis.get('primary_application'):
        print(f"   🎯 Primary Application: {app_analysis['primary_application']}")
    
    for app, info in app_analysis.get('application_distribution', {}).items():
        print(f"   ⚡ {app}: {info['count']} products ({info['percentage']:.1f}%)")
    
    print(f"\n🚀 MODERNIZATION RECOMMENDATIONS:")
    for i, rec in enumerate(result.modernization_recommendations, 1):
        print(f"   {i}. {rec['obsolete_product']}")
        print(f"      🎯 Type: {rec['recommendation_type']}")
        if 'recommended_product' in rec:
            print(f"      💡 Recommended: {rec['recommended_product']}")
        elif 'recommended_series' in rec:
            print(f"      💡 Recommended Series: {rec['recommended_series']}")
        print(f"      📊 Migration Complexity: {rec['migration_complexity']}")
    
    print(f"\n📈 CONFIDENCE SUMMARY:")
    conf_summary = result.confidence_summary
    print(f"   📊 Average Confidence: {conf_summary['average_confidence']:.3f}")
    print(f"   🎯 High Confidence Rate: {conf_summary['high_confidence_rate']:.1f}%")
    print(f"   📋 Products Analyzed: {conf_summary['total_products_analyzed']}")
    
    print(f"\n🕐 OBSOLESCENCE TIMELINE:")
    timeline = result.obsolescence_timeline
    print(f"   🔴 Obsolete Products: {timeline['obsolete_count']}")
    print(f"   🟢 Active Products: {timeline['active_count']}")
    print(f"   📊 Obsolescence Rate: {timeline['obsolescence_rate']:.1f}%")
    
    print("\n" + "="*80)
    print("✅ SEPAM INTELLIGENCE FILTER TEST COMPLETED")
    print("="*80)
    
    # Save results to file
    output_file = Path("scripts/sandbox") / f"sepam_intelligence_results_{int(time.time())}.json"
    output_data = {
        "test_metadata": {
            "source_file": str(grok_file),
            "test_timestamp": time.time(),
            "processing_time_ms": result.processing_time_ms
        },
        "sepam_products": [asdict(p) for p in result.sepam_products],
        "micom_products": [asdict(p) for p in result.micom_products],
        "powerlogic_products": [asdict(p) for p in result.powerlogic_products],
        "series_analysis": result.series_analysis,
        "application_analysis": result.application_analysis,
        "modernization_recommendations": result.modernization_recommendations,
        "obsolescence_timeline": result.obsolescence_timeline,
        "confidence_summary": result.confidence_summary
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2, default=str)
    
    logger.info(f"💾 Results saved to: {output_file}")


if __name__ == "__main__":
    test_sepam_filter_on_grok_metadata() 