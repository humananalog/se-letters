#!/usr/bin/env python3
"""
Database Endpoints Test Script
Tests all database endpoints to ensure PostgreSQL migration is working
correctly
"""

import requests
import json
import time
import psycopg2
from typing import Dict, Any, List
from loguru import logger


class DatabaseEndpointsTester:
    """Test all database endpoints"""
    
    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_get_all_letters(self) -> Dict[str, Any]:
        """Test GET /api/letters endpoint"""
        logger.info("🔍 Testing GET /api/letters")
        
        try:
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/api/letters")
            response_time = time.time() - start_time
            
            logger.info(f"Response time: {response_time:.3f}s")
            logger.info(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.success(
                    f"✅ GET /api/letters successful - {len(data)} letters returned"
                )
                
                # Validate response structure
                if data and len(data) > 0:
                    first_letter = data[0]
                    required_fields = [
                        'id', 'source_file_path', 'document_name', 'created_at'
                    ]
                    missing_fields = [
                        field for field in required_fields 
                        if field not in first_letter
                    ]
                    
                    if missing_fields:
                        logger.warning(f"⚠️ Missing fields in response: {missing_fields}")
                    else:
                        logger.success("✅ Response structure validation passed")
                
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "letter_count": len(data),
                    "data": data[:3] if data else []  # Return first 3 letters for inspection
                }
            else:
                logger.error(f"❌ GET /api/letters failed with status {response.status_code}")
                logger.error(f"Response: {response.text}")
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text
                }
                
        except Exception as e:
            logger.error(f"❌ GET /api/letters exception: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def test_get_letter_by_id(self, letter_id: int) -> Dict[str, Any]:
        """Test GET /api/letters?id=X endpoint"""
        logger.info(f"🔍 Testing GET /api/letters?id={letter_id}")
        
        try:
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/api/letters", params={"id": letter_id})
            response_time = time.time() - start_time
            
            logger.info(f"Response time: {response_time:.3f}s")
            logger.info(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.success(f"✅ GET /api/letters?id={letter_id} successful")
                
                # Validate response structure
                required_fields = ['id', 'source_file_path', 'document_name', 'created_at']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    logger.warning(f"⚠️ Missing fields in response: {missing_fields}")
                else:
                    logger.success("✅ Response structure validation passed")
                
                # Check if products and technical_specs are present
                if 'products' in data:
                    logger.info(f"📦 Letter has {len(data['products'])} products")
                if 'technical_specs' in data:
                    logger.info(f"🔧 Letter has {len(data['technical_specs'])} technical specs")
                
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "letter_id": letter_id,
                    "data": data
                }
            elif response.status_code == 404:
                logger.warning(f"⚠️ Letter {letter_id} not found (404)")
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "letter_id": letter_id,
                    "not_found": True
                }
            else:
                logger.error(f"❌ GET /api/letters?id={letter_id} failed with status {response.status_code}")
                logger.error(f"Response: {response.text}")
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text
                }
                
        except Exception as e:
            logger.error(f"❌ GET /api/letters?id={letter_id} exception: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_available_letter_ids(self) -> List[int]:
        """Get available letter IDs from database for testing"""
        logger.info("🔍 Getting available letter IDs from database")
        
        try:
            conn = psycopg2.connect(
                host='localhost',
                database='se_letters_dev',
                user='alexandre'
            )
            
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM letters ORDER BY id LIMIT 10")
                results = cur.fetchall()
                letter_ids = [row[0] for row in results]
                
            conn.close()
            
            logger.info(f"📊 Found {len(letter_ids)} letter IDs: {letter_ids}")
            return letter_ids
            
        except Exception as e:
            logger.error(f"❌ Failed to get letter IDs: {e}")
            return []
    
    def test_database_connection(self) -> Dict[str, Any]:
        """Test direct database connection"""
        logger.info("🔍 Testing direct PostgreSQL connection")
        
        try:
            start_time = time.time()
            conn = psycopg2.connect(
                host='localhost',
                database='se_letters_dev',
                user='alexandre'
            )
            
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM letters")
                count = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM letter_products")
                product_count = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM letter_product_matches")
                match_count = cur.fetchone()[0]
            
            conn.close()
            response_time = time.time() - start_time
            
            logger.success(f"✅ Database connection successful ({response_time:.3f}s)")
            logger.info(f"📊 Database stats: {count} letters, {product_count} products, {match_count} matches")
            
            return {
                "success": True,
                "response_time": response_time,
                "letter_count": count,
                "product_count": product_count,
                "match_count": match_count
            }
            
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive test of all endpoints"""
        logger.info("🚀 Starting comprehensive database endpoints test")
        
        results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "base_url": self.base_url,
            "tests": {}
        }
        
        # Test 1: Database connection
        logger.info("=" * 60)
        results["tests"]["database_connection"] = self.test_database_connection()
        
        # Test 2: Get all letters
        logger.info("=" * 60)
        results["tests"]["get_all_letters"] = self.test_get_all_letters()
        
        # Test 3: Get specific letters
        logger.info("=" * 60)
        letter_ids = self.get_available_letter_ids()
        results["tests"]["get_letter_by_id"] = {}
        
        for letter_id in letter_ids[:3]:  # Test first 3 letters
            logger.info(f"Testing letter ID: {letter_id}")
            results["tests"]["get_letter_by_id"][letter_id] = self.test_get_letter_by_id(letter_id)
            time.sleep(0.5)  # Small delay between requests
        
        # Test 4: Test non-existent letter
        logger.info("=" * 60)
        logger.info("Testing non-existent letter ID: 99999")
        results["tests"]["get_letter_by_id"][99999] = self.test_get_letter_by_id(99999)
        
        # Summary
        logger.info("=" * 60)
        logger.info("📊 Test Summary:")
        
        total_tests = 0
        passed_tests = 0
        
        for test_name, test_result in results["tests"].items():
            if isinstance(test_result, dict) and test_result.get("success"):
                passed_tests += 1
            elif isinstance(test_result, dict):
                # Handle nested results for get_letter_by_id
                for letter_id, letter_result in test_result.items():
                    total_tests += 1
                    if letter_result.get("success"):
                        passed_tests += 1
            else:
                total_tests += 1
        
        logger.success(f"✅ Tests passed: {passed_tests}/{total_tests}")
        
        results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": f"{(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%"
        }
        
        return results

def main():
    """Main test function"""
    logger.info("🧪 Database Endpoints Test Suite")
    logger.info("Testing PostgreSQL migration for SE Letters application")
    
    # Test with different ports in case 3000 is busy
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
        logger.error("❌ Could not find running webapp on any port")
        logger.info("Please start the webapp with: cd webapp && npm run dev")
        return
    
    # Run comprehensive test
    tester = DatabaseEndpointsTester(base_url)
    results = tester.run_comprehensive_test()
    
    # Save results
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    results_file = f"logs/database_endpoints_test_{timestamp}.json"
    
    try:
        import os
        os.makedirs("logs", exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.success(f"📄 Test results saved to: {results_file}")
        
    except Exception as e:
        logger.error(f"❌ Failed to save results: {e}")
    
    # Final status
    success_rate = results["summary"]["success_rate"]
    if success_rate == "100.0%":
        logger.success("🎉 All tests passed! PostgreSQL migration is working correctly.")
    else:
        logger.warning(f"⚠️ Some tests failed. Success rate: {success_rate}")

if __name__ == "__main__":
    main() 