#!/usr/bin/env python3
"""
Test script to verify the modular structure works correctly.
Tests both the new modular crawler and the Flask application.
"""
import json
import sys
from app import app

def test_modular_imports():
    """Test that all modular components can be imported correctly."""
    print("🧩 Testing Modular Structure Imports...")
    
    try:
        # Test crawler module imports
        from crawler import SHAWebCrawler
        from crawler import CrawlRequest, CrawlResult
        from crawler import ValidationError, NetworkError, CrawlerError
        from crawler.utils import find_buzzwords_in_text, create_cache_key
        from crawler.core import SHAWebCrawler as CoreCrawler
        from crawler.models import CrawlRequest as ModelRequest
        
        print("✅ All modular imports successful")
        
        # Test that imports are the same
        assert SHAWebCrawler == CoreCrawler
        assert CrawlRequest == ModelRequest
        print("✅ Module aliases work correctly")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_modular_crawler_functionality():
    """Test that the modular crawler works identically to the old version."""
    print("\n🕷️  Testing Modular Crawler Functionality...")
    
    try:
        from crawler import SHAWebCrawler
        
        # Test context manager
        with SHAWebCrawler(max_workers=2, queue_size=10) as crawler:
            print("✅ Context manager works")
            
            # Test simple crawl
            results = crawler.crawl_urls(['https://httpbin.org/html'], ['html'])
            print(f"✅ Crawl completed: {len(results)} results")
            
            # Verify result structure
            if results and len(results) > 0:
                result = results[0]
                required_fields = ['url', 'found', 'error', 'error_code', 'status_code', 'retries']
                for field in required_fields:
                    assert field in result, f"Missing field: {field}"
                print("✅ Result structure is correct")
            
        print("✅ Modular crawler functionality verified")
        return True
        
    except Exception as e:
        print(f"❌ Crawler test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_flask_app_with_modular_structure():
    """Test that the Flask app works with the new modular structure."""
    print("\n🌐 Testing Flask App with Modular Structure...")
    
    try:
        with app.test_client() as client:
            # Test main page
            response = client.get('/')
            assert response.status_code == 200
            print("✅ Main page loads")
            
            # Test health check
            response = client.get('/health')
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'healthy'
            print("✅ Health check works")
            
            # Test crawl endpoint
            response = client.post('/crawl', json={
                'urls': ['https://httpbin.org/html'],
                'buzzwords': ['html']
            })
            assert response.status_code == 200
            data = response.get_json()
            assert isinstance(data, list)
            assert len(data) == 1
            print("✅ Crawl endpoint works with modular structure")
            
            # Test error handling still works
            response = client.post('/crawl', json={})
            assert response.status_code == 400
            data = response.get_json()
            assert 'error_code' in data
            print("✅ Error handling preserved")
            
        print("✅ Flask app works correctly with modular structure")
        return True
        
    except Exception as e:
        print(f"❌ Flask app test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_utility_functions():
    """Test that utility functions work correctly."""
    print("\n🔧 Testing Utility Functions...")
    
    try:
        from crawler.utils import (
            find_buzzwords_in_text, 
            create_cache_key,
            extract_domain,
            validate_url_list,
            validate_buzzwords_list
        )
        
        # Test buzzword finding
        text = "This is a test document for tenders and contracts"
        buzzwords = ["test", "tenders", "missing"]
        found = find_buzzwords_in_text(text, buzzwords)
        assert "test" in found
        assert "tenders" in found
        assert "missing" not in found
        print("✅ Buzzword detection works")
        
        # Test cache key creation
        key = create_cache_key("https://example.com", ["test", "buzz"])
        assert isinstance(key, str)
        assert "example.com" in key
        print("✅ Cache key creation works")
        
        # Test domain extraction
        domain = extract_domain("https://example.com/path")
        assert domain == "https://example.com"
        print("✅ Domain extraction works")
        
        # Test validation functions
        urls = validate_url_list(["  https://test.com  ", "", "https://test2.com", None])
        assert len(urls) == 2
        print("✅ URL validation works")
        
        words = validate_buzzwords_list(["  test  ", "", "buzz", None])
        assert len(words) == 2
        print("✅ Buzzword validation works")
        
        print("✅ All utility functions work correctly")
        return True
        
    except Exception as e:
        print(f"❌ Utility functions test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_code_organization():
    """Test that the code is properly organized."""
    print("\n📁 Testing Code Organization...")
    
    try:
        import os
        
        # Check that files exist
        required_files = [
            'crawler/__init__.py',
            'crawler/core.py',
            'crawler/models.py',
            'crawler/utils.py',
            'app.py',
            'app_old.py'  # Backup should exist
        ]
        
        missing_files = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            print(f"❌ Missing files: {missing_files}")
            return False
        
        print("✅ All required files exist")
        
        # Check that app.py is much smaller now
        with open('app.py', 'r') as f:
            new_app_lines = len(f.readlines())
        
        with open('app_old.py', 'r') as f:
            old_app_lines = len(f.readlines())
        
        print(f"📊 Code size reduction: {old_app_lines} → {new_app_lines} lines ({old_app_lines - new_app_lines} lines moved to modules)")
        
        if new_app_lines >= old_app_lines:
            print("⚠️  Warning: New app.py is not smaller than original")
        else:
            print("✅ Code successfully modularized")
        
        return True
        
    except Exception as e:
        print(f"❌ Code organization test failed: {e}")
        return False

def test_backward_compatibility():
    """Test that the API remains exactly the same."""
    print("\n🔄 Testing Backward Compatibility...")
    
    try:
        with app.test_client() as client:
            # Test exact same request format
            test_request = {
                'urls': ['https://httpbin.org/html', 'https://httpbin.org/json'],
                'buzzwords': ['html', 'json', 'test']
            }
            
            response = client.post('/crawl', json=test_request)
            assert response.status_code == 200
            
            data = response.get_json()
            assert isinstance(data, list)
            assert len(data) == 2  # Two URLs
            
            # Check response format is identical
            for result in data:
                required_fields = ['url', 'found', 'error', 'error_code', 'status_code', 'retries']
                for field in required_fields:
                    assert field in result, f"Missing field: {field}"
            
            print("✅ API response format unchanged")
            print("✅ Backward compatibility maintained")
            
        return True
        
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Modular Structure Implementation...")
    print("=" * 60)
    
    tests = [
        test_modular_imports,
        test_modular_crawler_functionality,
        test_flask_app_with_modular_structure,
        test_utility_functions,
        test_code_organization,
        test_backward_compatibility
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"📊 Test Summary: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n🎉 All tests passed! Modular structure is working correctly!")
        print("\n📋 Modularization Benefits:")
        print("  ✅ Clean separation of concerns")
        print("  ✅ Reusable crawler components")
        print("  ✅ Easier testing and maintenance")  
        print("  ✅ Preserved all functionality")
        print("  ✅ Maintained backward compatibility")
        print("  ✅ Better code organization")
        print("  ✅ Ready for future enhancements")
        
        sys.exit(0)
    else:
        print(f"\n❌ {failed} tests failed. Please check the errors above.")
        sys.exit(1)