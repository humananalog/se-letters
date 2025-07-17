#!/usr/bin/env python3
"""
Comprehensive Database Endpoints Test
Validates all database endpoints with detailed checks
"""

import requests
import json
import time
import psycopg2
from typing import Dict, Any, List
from loguru import logger


class ComprehensiveEndpointTester:
    """Comprehensive test of all database endpoints"""
    
    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_endpoint_health(self) -> Dict[str, Any]:
        """Test basic endpoint health"""
        logger.info("🏥 Testing endpoint health")
        
        try:
            response = self.session.get(f"{self.base_url}/api/letters", timeout=10)
            return {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_get_all_letters_detailed(self) -> Dict[str, Any]:
        """Detailed test of GET /api/letters"""
        logger.info("📋 Testing GET /api/letters (detailed)")
        
        try:
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/api/letters")
            response_time = time.time() - start_time
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text
                }
            
            data = response.json()
            
            # Validate response structure
            validation_results = self._validate_letters_structure(data)
            
            return {
                "success": True,
                "status_code": response.status_code,
                "response_time": response_time,
                "letter_count": len(data),
                "validation": validation_results,
                "sample_data": data[0] if data else None
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_get_letter_by_id_detailed(self, letter_id: int) -> Dict[str, Any]:
        """Detailed test of GET /api/letters?id=X"""
        logger.info(f"📄 Testing GET /api/letters?id={letter_id} (detailed)")
        
        try:
            start_time = time.time()
            response = self.session.get(
                f"{self.base_url}/api/letters", 
                params={"id": letter_id}
            )
            response_time = time.time() - start_time
            
            if response.status_code == 404:
                return {
                    "success": True,
                    "status_code": 404,
                    "response_time": response_time,
                    "not_found": True,
                    "letter_id": letter_id
                }
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text
                }
            
            data = response.json()
            
            # Validate response structure
            validation_results = self._validate_letter_detail_structure(data)
            
            return {
                "success": True,
                "status_code": response.status_code,
                "response_time": response_time,
                "letter_id": letter_id,
                "validation": validation_results,
                "data": data
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_database_integrity(self) -> Dict[str, Any]:
        """Test database integrity and consistency"""
        logger.info("🔍 Testing database integrity")
        
        try:
            conn = psycopg2.connect(
                host='localhost',
                database='se_letters_dev',
                user='alexandre'
            )
            
            with conn.cursor() as cur:
                # Get counts
                cur.execute("SELECT COUNT(*) FROM letters")
                letter_count = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM letter_products")
                product_count = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM letter_product_matches")
                match_count = cur.fetchone()[0]
                
                # Check for orphaned records
                cur.execute("""
                    SELECT COUNT(*) FROM letter_products lp
                    LEFT JOIN letters l ON lp.letter_id = l.id
                    WHERE l.id IS NULL
                """)
                orphaned_products = cur.fetchone()[0]
                
                # Check for orphaned matches
                cur.execute("""
                    SELECT COUNT(*) FROM letter_product_matches lpm
                    LEFT JOIN letter_products lp ON lpm.letter_product_id = lp.id
                    WHERE lp.id IS NULL
                """)
                orphaned_matches = cur.fetchone()[0]
                
                # Get sample letter IDs
                cur.execute("SELECT id FROM letters ORDER BY id LIMIT 5")
                sample_ids = [row[0] for row in cur.fetchall()]
            
            conn.close()
            
            return {
                "success": True,
                "letter_count": letter_count,
                "product_count": product_count,
                "match_count": match_count,
                "orphaned_products": orphaned_products,
                "orphaned_matches": orphaned_matches,
                "sample_ids": sample_ids,
                "integrity_ok": orphaned_products == 0 and orphaned_matches == 0
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_performance_metrics(self) -> Dict[str, Any]:
        """Test performance metrics"""
        logger.info("⚡ Testing performance metrics")
        
        metrics = {}
        
        # Test multiple requests to get average response times
        for endpoint in ["/api/letters", "/api/letters?id=9"]:
            response_times = []
            
            for _ in range(5):
                try:
                    start_time = time.time()
                    if "id=" in endpoint:
                        response = self.session.get(f"{self.base_url}{endpoint}")
                    else:
                        response = self.session.get(f"{self.base_url}{endpoint}")
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        response_times.append(response_time)
                    
                    time.sleep(0.1)  # Small delay between requests
                    
                except Exception:
                    continue
            
            if response_times:
                metrics[endpoint] = {
                    "avg_response_time": sum(response_times) / len(response_times),
                    "min_response_time": min(response_times),
                    "max_response_time": max(response_times),
                    "request_count": len(response_times)
                }
        
        return {
            "success": True,
            "metrics": metrics
        }
    
    def _validate_letters_structure(self, data: List[Dict]) -> Dict[str, Any]:
        """Validate structure of letters list response"""
        if not data:
            return {"valid": True, "message": "Empty list is valid"}
        
        required_fields = [
            'id', 'source_file_path', 'document_name', 'created_at'
        ]
        
        validation_results = []
        for i, letter in enumerate(data):
            missing_fields = [f for f in required_fields if f not in letter]
            if missing_fields:
                validation_results.append({
                    "index": i,
                    "missing_fields": missing_fields
                })
        
        return {
            "valid": len(validation_results) == 0,
            "errors": validation_results,
            "checked_letters": len(data)
        }
    
    def _validate_letter_detail_structure(self, data: Dict) -> Dict[str, Any]:
        """Validate structure of individual letter response"""
        required_fields = [
            'id', 'source_file_path', 'document_name', 'created_at'
        ]
        
        missing_fields = [f for f in required_fields if f not in data]
        
        # Check optional fields
        optional_fields = ['products', 'technical_specs']
        present_optional = [f for f in optional_fields if f in data]
        
        return {
            "valid": len(missing_fields) == 0,
            "missing_required": missing_fields,
            "present_optional": present_optional,
            "products_count": len(data.get('products', [])),
            "tech_specs_count": len(data.get('technical_specs', []))
        }
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive test suite"""
        logger.info("🚀 Starting comprehensive endpoint test suite")
        
        results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "base_url": self.base_url,
            "tests": {}
        }
        
        # Test 1: Endpoint health
        logger.info("=" * 60)
        results["tests"]["endpoint_health"] = self.test_endpoint_health()
        
        # Test 2: Database integrity
        logger.info("=" * 60)
        results["tests"]["database_integrity"] = self.test_database_integrity()
        
        # Test 3: Get all letters
        logger.info("=" * 60)
        results["tests"]["get_all_letters"] = self.test_get_all_letters_detailed()
        
        # Test 4: Get specific letters
        logger.info("=" * 60)
        sample_ids = results["tests"]["database_integrity"].get("sample_ids", [])
        results["tests"]["get_letter_by_id"] = {}
        
        for letter_id in sample_ids[:3]:  # Test first 3 letters
            results["tests"]["get_letter_by_id"][letter_id] = (
                self.test_get_letter_by_id_detailed(letter_id)
            )
            time.sleep(0.2)
        
        # Test 5: Non-existent letter
        results["tests"]["get_letter_by_id"][99999] = (
            self.test_get_letter_by_id_detailed(99999)
        )
        
        # Test 6: Performance metrics
        logger.info("=" * 60)
        results["tests"]["performance"] = self.test_performance_metrics()
        
        # Generate summary
        results["summary"] = self._generate_summary(results["tests"])
        
        return results
    
    def _generate_summary(self, tests: Dict) -> Dict[str, Any]:
        """Generate test summary"""
        total_tests = 0
        passed_tests = 0
        issues = []
        
        for test_name, test_result in tests.items():
            if isinstance(test_result, dict) and test_result.get("success"):
                passed_tests += 1
            elif isinstance(test_result, dict):
                # Handle nested results
                for letter_id, letter_result in test_result.items():
                    total_tests += 1
                    if letter_result.get("success"):
                        passed_tests += 1
                    else:
                        issues.append(f"{test_name}[{letter_id}]: {letter_result.get('error', 'Unknown error')}")
            else:
                total_tests += 1
        
        # Check for specific issues
        if tests.get("database_integrity", {}).get("success"):
            integrity = tests["database_integrity"]
            if not integrity.get("integrity_ok"):
                issues.append("Database integrity issues detected")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": f"{(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%",
            "issues": issues,
            "overall_status": "PASS" if len(issues) == 0 else "FAIL"
        }


def main():
    """Main test function"""
    logger.info("🧪 Comprehensive Database Endpoints Test Suite")
    logger.info("Testing PostgreSQL migration for SE Letters application")
    
    # Find running webapp
    test_ports = [3000, 3001, 3002, 3003]
    base_url = None
    
    for port in test_ports:
        try:
            response = requests.get(f"http://localhost:{port}/api/letters", timeout=5)
            if response.status_code == 200:
                base_url = f"http://localhost:{port}"
                logger.info(f"✅ Found webapp running on port {port}")
                break
        except requests.exceptions.RequestException:
            continue
    
    if not base_url:
        logger.error("❌ Could not find running webapp")
        return
    
    # Run comprehensive test
    tester = ComprehensiveEndpointTester(base_url)
    results = tester.run_comprehensive_test()
    
    # Save results
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    results_file = f"logs/comprehensive_endpoint_test_{timestamp}.json"
    
    try:
        import os
        os.makedirs("logs", exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.success(f"📄 Test results saved to: {results_file}")
        
    except Exception as e:
        logger.error(f"❌ Failed to save results: {e}")
    
    # Print summary
    summary = results["summary"]
    logger.info("=" * 60)
    logger.info("📊 COMPREHENSIVE TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Overall Status: {summary['overall_status']}")
    logger.info(f"Success Rate: {summary['success_rate']}")
    logger.info(f"Tests Passed: {summary['passed_tests']}/{summary['total_tests']}")
    
    if summary['issues']:
        logger.warning("⚠️ Issues Found:")
        for issue in summary['issues']:
            logger.warning(f"  - {issue}")
    else:
        logger.success("🎉 All tests passed! PostgreSQL migration is working correctly.")
    
    # Performance summary
    if results["tests"].get("performance", {}).get("success"):
        perf = results["tests"]["performance"]["metrics"]
        logger.info("⚡ Performance Summary:")
        for endpoint, metrics in perf.items():
            logger.info(f"  {endpoint}: {metrics['avg_response_time']:.3f}s avg")


if __name__ == "__main__":
    main() 