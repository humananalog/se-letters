#!/usr/bin/env python3
"""
PIX2B Production Test Script
Tests the production pipeline specifically on PIX2B document to diagnose extraction issues
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from se_letters.core.config import get_config
from se_letters.services.document_processor import DocumentProcessor
from se_letters.services.sota_grok_service import SOTAGrokService
from se_letters.services.enhanced_duckdb_service import EnhancedDuckDBService
from se_letters.utils.logger import get_logger

logger = get_logger(__name__)


class PIX2BProductionTester:
    """Test production pipeline components on PIX2B document"""
    
    def __init__(self):
        """Initialize test environment"""
        self.config = get_config()
        self.test_file = Path("data/test/documents/PIX2B_Phase_out_Letter.pdf")
        
        # Expected content for validation
        self.expected_content = """Internal Communication:
Withdrawal notice of PIX Double Bus Bar (PIX 2B) offer from all markets
Except Belgium frame contract where we have signed contract.
The Power System Business Unit launched projects to streamline the MV product offers.
In the frame of this project, please be informed that it has been decided to withdraw the
PIX 2B offer, launched in 2014
12 – 17.5kV, up to 3150A, 50/60Hz, 31.5kA 3s
There will be NO substitution for this range.
Note: For Belgium utility Frame contract – Schneider will continue to support until end of
Frame contract – Nov'2023. Hence Belgium utility is out of scope of this PWP.
We plan:
• The customer announcement by mid of April 2020.
• No Orders will be accepted starting post internal communication (Mar'2020).
We kindly ask you to analyze your ongoing opportunities and inform us in case you have
• Quotations still valid / alive after the last order date
• or coming orders not possible to be booked for analysis purpose.
• Frame contracts still valid – e.g. Belgium utility where there is commitment from =S=
To manage this withdrawal process properly and to coordinate all necessary actions an
operational PWP (Product Withdrawal Process) team involving MVO (Medium Voltage
Offer) Activity and Energy Field Services organisation has been set up.
This team is in charge to define and/or to confirm:
• the evaluation of Services business
• the spare part offer that will be maintained for a minimum of 10 years to support
the Installed Base of PIX 2B.
• the Services Ecofit Centre that will support Front Offices and Field Services
engineers.
• the customer communication (we will come back to you with the appropriate communication
content for external customers).
This project/process is splitted into 2 steps
• Stop of commercialisation to all countries apart from Belgium
• Full PWP after the end of the Belgium frame contract in 2023
One of the key success factors of this withdrawal is the support and the involvement of the
Front Offices in the process.
Thus, we kindly ask for your help to nominate a local contact person in your
country/region who the PWP team can work with and who will lead related activities,
including preparation of customer communication.
We would appreciate your reply within 31st of Mar 2020, please revert back to offer
simplification manager (amar.wategaonkar@se.com) or Global Product Manager
(josef.eberl@se.com).
Be assure of the full support of MVO Activity in this PWP, do not hesitate to revert to your
day to day contact (Business Development) or to request support / information.
We will keep you aware of this Product Withdrawal Project progress in the coming weeks.
Yours Faithfully,
Amar WATEGAONKAR Josef EBERL
MVO - Offer Simplification Manager Global Product Manager
(Medium Voltage Equipment's)"""
        
        print("🧪 PIX2B Production Test Initialized")
        print(f"📄 Test file: {self.test_file}")
        print(f"📊 Expected content length: {len(self.expected_content)} characters")
        
    def test_document_extraction(self) -> Dict[str, Any]:
        """Test document text extraction"""
        print("\n🔍 Testing Document Text Extraction...")
        
        try:
            processor = DocumentProcessor(self.config)
            document = processor.process_document(self.test_file)
            
            if not document:
                return {
                    "success": False,
                    "error": "Document processor returned None",
                    "extracted_text": "",
                    "text_length": 0
                }
            
            extracted_text = document.text
            text_length = len(extracted_text)
            
            # Check if extraction worked
            success = text_length > 100  # Minimum viable extraction
            
            # Check for key content
            key_phrases = [
                "PIX Double Bus Bar",
                "PIX 2B",
                "12 – 17.5kV",
                "3150A",
                "amar.wategaonkar@se.com",
                "Power System Business Unit"
            ]
            
            found_phrases = [phrase for phrase in key_phrases if phrase in extracted_text]
            
            result = {
                "success": success,
                "extracted_text": extracted_text,
                "text_length": text_length,
                "key_phrases_found": found_phrases,
                "key_phrases_total": len(key_phrases),
                "extraction_quality": len(found_phrases) / len(key_phrases)
            }
            
            print(f"✅ Text extraction: {'SUCCESS' if success else 'FAILED'}")
            print(f"📝 Extracted length: {text_length} characters")
            print(f"🎯 Key phrases found: {len(found_phrases)}/{len(key_phrases)}")
            print(f"📊 Extraction quality: {result['extraction_quality']:.2%}")
            
            if not success:
                print(f"❌ Extracted text preview: {extracted_text[:200]}...")
            
            return result
            
        except Exception as e:
            print(f"❌ Document extraction failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "extracted_text": "",
                "text_length": 0
            }
    
    def test_grok_extraction(self, document_text: str) -> Dict[str, Any]:
        """Test Grok metadata extraction"""
        print("\n🤖 Testing Grok Metadata Extraction...")
        
        if not document_text:
            print("❌ No document text provided for Grok extraction")
            return {
                "success": False,
                "error": "No document text provided",
                "metadata": None
            }
        
        try:
            # Use the expected content if extraction failed
            test_text = document_text if len(document_text) > 100 else self.expected_content
            
            grok_service = SOTAGrokService(self.config)
            
            print(f"🔍 Processing {len(test_text)} characters with Grok...")
            start_time = time.time()
            
            # Use process_raw_document method instead of extract_metadata
            result = grok_service.process_raw_document(self.test_file, test_text)
            metadata = result if result else None
            
            processing_time = time.time() - start_time
            
            # Evaluate metadata quality
            quality_score = self._evaluate_metadata_quality(metadata)
            
            result = {
                "success": metadata is not None,
                "metadata": metadata,
                "processing_time": processing_time,
                "quality_score": quality_score
            }
            
            print(f"✅ Grok extraction: {'SUCCESS' if result['success'] else 'FAILED'}")
            print(f"⏱️ Processing time: {processing_time:.2f}s")
            print(f"📊 Quality score: {quality_score:.2%}")
            
            if metadata:
                self._print_metadata_summary(metadata)
            
            return result
            
        except Exception as e:
            print(f"❌ Grok extraction failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "metadata": None
            }
    
    def _evaluate_metadata_quality(self, metadata: Dict[str, Any]) -> float:
        """Evaluate the quality of extracted metadata"""
        if not metadata:
            return 0.0
        
        score = 0.0
        total_checks = 0
        
        # Check product information
        if "product_information" in metadata and metadata["product_information"]:
            product = metadata["product_information"][0] if isinstance(metadata["product_information"], list) else metadata["product_information"]
            
            # Product identifier
            if product.get("product_identifier") == "PIX2B":
                score += 1
            total_checks += 1
            
            # Range label
            if "PIX" in str(product.get("range_label", "")):
                score += 1
            total_checks += 1
            
            # Technical specs
            tech_specs = product.get("technical_specifications", {})
            if tech_specs.get("voltage_level") and "17.5kV" in str(tech_specs.get("voltage_level")):
                score += 1
            total_checks += 1
            
            if tech_specs.get("current_rating") and "3150A" in str(tech_specs.get("current_rating")):
                score += 1
            total_checks += 1
        
        # Check lifecycle information
        if "lifecycle_information" in metadata:
            lifecycle = metadata["lifecycle_information"]
            
            # Check for key dates
            if lifecycle.get("announcement_date") and "2020" in str(lifecycle.get("announcement_date")):
                score += 1
            total_checks += 1
            
            key_dates = lifecycle.get("key_dates", {})
            if key_dates.get("last_order_date") and "2020" in str(key_dates.get("last_order_date")):
                score += 1
            total_checks += 1
        
        # Check business information
        if "business_information" in metadata:
            business = metadata["business_information"]
            
            if business.get("affected_countries") and "Belgium" in str(business.get("affected_countries")):
                score += 1
            total_checks += 1
        
        # Check contact information
        if "contact_information" in metadata:
            contact = metadata["contact_information"]
            
            if contact.get("contact_details") and "amar.wategaonkar@se.com" in str(contact.get("contact_details")):
                score += 1
            total_checks += 1
        
        return score / total_checks if total_checks > 0 else 0.0
    
    def _print_metadata_summary(self, metadata: Dict[str, Any]):
        """Print a summary of extracted metadata"""
        print("\n📋 Metadata Summary:")
        
        # Product information
        if "product_information" in metadata and metadata["product_information"]:
            product = metadata["product_information"][0] if isinstance(metadata["product_information"], list) else metadata["product_information"]
            print(f"   🔧 Product: {product.get('product_identifier', 'N/A')}")
            print(f"   📦 Range: {product.get('range_label', 'N/A')}")
            
            tech_specs = product.get("technical_specifications", {})
            if tech_specs:
                print(f"   ⚡ Voltage: {tech_specs.get('voltage_level', 'N/A')}")
                print(f"   🔌 Current: {tech_specs.get('current_rating', 'N/A')}")
        
        # Lifecycle information
        if "lifecycle_information" in metadata:
            lifecycle = metadata["lifecycle_information"]
            print(f"   📅 Announcement: {lifecycle.get('announcement_date', 'N/A')}")
            
            key_dates = lifecycle.get("key_dates", {})
            if key_dates:
                print(f"   🚫 Last Order: {key_dates.get('last_order_date', 'N/A')}")
        
        # Business information
        if "business_information" in metadata:
            business = metadata["business_information"]
            print(f"   🌍 Countries: {business.get('affected_countries', 'N/A')}")
            print(f"   💼 Impact: {business.get('business_impact', 'N/A')}")
        
        # Contact information
        if "contact_information" in metadata:
            contact = metadata["contact_information"]
            print(f"   📧 Contacts: {contact.get('contact_details', 'N/A')}")
    
    def test_database_validation(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Test database validation of extracted ranges"""
        print("\n🗄️ Testing Database Validation...")
        
        if not metadata:
            print("❌ No metadata provided for database validation")
            return {"success": False, "error": "No metadata provided"}
        
        try:
            db_service = EnhancedDuckDBService("data/IBcatalogue.duckdb")
            
            # Extract ranges from metadata
            ranges = []
            if "product_information" in metadata and metadata["product_information"]:
                product = metadata["product_information"][0] if isinstance(metadata["product_information"], list) else metadata["product_information"]
                if product.get("range_label"):
                    ranges.append(product["range_label"])
                if product.get("product_identifier"):
                    ranges.append(product["product_identifier"])
            
            print(f"🔍 Validating ranges: {ranges}")
            
            # Search for products using the extracted ranges
            from se_letters.services.enhanced_duckdb_service import SearchCriteria
            
            search_criteria = SearchCriteria(ranges=ranges, obsolete_only=True)
            search_result = db_service.search_products(search_criteria)
            
            valid_ranges = ranges if search_result.products else []
            invalid_ranges = [] if search_result.products else ranges
            
            # Also search for PIX products specifically
            pix_criteria = SearchCriteria(ranges=["PIX"], obsolete_only=True)
            pix_result = db_service.search_products(pix_criteria)
            
            result = {
                "success": True,
                "valid_ranges": valid_ranges,
                "invalid_ranges": invalid_ranges,
                "products_found": len(search_result.products),
                "pix_products_found": len(pix_result.products),
                "sample_products": pix_result.products[:5] if pix_result.products else []
            }
            
            print(f"✅ Database validation: SUCCESS")
            print(f"✅ Valid ranges: {valid_ranges}")
            print(f"❌ Invalid ranges: {invalid_ranges}")
            print(f"🔍 PIX products found: {len(pix_result.products)}")
            
            return result
            
        except Exception as e:
            print(f"❌ Database validation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def run_complete_test(self) -> Dict[str, Any]:
        """Run complete production test"""
        print("🚀 Starting Complete PIX2B Production Test")
        print("=" * 60)
        
        # Test 1: Document extraction
        extraction_result = self.test_document_extraction()
        
        # Test 2: Grok metadata extraction
        grok_result = self.test_grok_extraction(extraction_result.get("extracted_text", ""))
        
        # Test 3: Database validation
        db_result = self.test_database_validation(grok_result.get("metadata"))
        
        # Overall assessment
        overall_success = (
            extraction_result.get("success", False) and
            grok_result.get("success", False) and
            db_result.get("success", False)
        )
        
        overall_result = {
            "overall_success": overall_success,
            "extraction_test": extraction_result,
            "grok_test": grok_result,
            "database_test": db_result,
            "recommendations": self._generate_recommendations(extraction_result, grok_result, db_result)
        }
        
        print("\n" + "=" * 60)
        print(f"🎯 Overall Test Result: {'SUCCESS' if overall_success else 'FAILED'}")
        print("\n📋 Recommendations:")
        for rec in overall_result["recommendations"]:
            print(f"   • {rec}")
        
        return overall_result
    
    def _generate_recommendations(self, extraction_result: Dict, grok_result: Dict, db_result: Dict) -> list:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Document extraction issues
        if not extraction_result.get("success"):
            recommendations.append("Fix document text extraction - PDF processing is failing")
        elif extraction_result.get("extraction_quality", 0) < 0.8:
            recommendations.append("Improve document text extraction quality")
        
        # Grok extraction issues
        if not grok_result.get("success"):
            recommendations.append("Fix Grok API connectivity and authentication")
        elif grok_result.get("quality_score", 0) < 0.7:
            recommendations.append("Enhance Grok prompts to extract richer metadata")
        
        # Database validation issues
        if not db_result.get("success"):
            recommendations.append("Fix database connectivity and validation logic")
        elif not db_result.get("valid_ranges"):
            recommendations.append("Improve range extraction and validation mapping")
        
        # Performance issues
        if grok_result.get("processing_time", 0) > 30:
            recommendations.append("Optimize Grok processing time")
        
        if not recommendations:
            recommendations.append("All tests passed! System is working correctly.")
        
        return recommendations


def main():
    """Run the PIX2B production test"""
    tester = PIX2BProductionTester()
    
    try:
        result = tester.run_complete_test()
        
        # Save results
        output_file = Path("data/output/pix2b_production_test_results.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {output_file}")
        
        # Exit with appropriate code
        exit_code = 0 if result["overall_success"] else 1
        sys.exit(exit_code)
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 