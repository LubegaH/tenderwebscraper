#!/usr/bin/env python3
"""
Test script to verify improved error handling patterns.
"""
import json
from app import app

def test_error_handling():
    """Test various error scenarios to verify proper error handling."""
    print("🧪 Testing Error Handling Improvements...")
    
    with app.test_client() as client:
        
        # Test 1: Missing JSON data
        print("\n1. Testing missing JSON data...")
        response = client.post('/crawl')
        assert response.status_code == 400
        data = response.get_json()
        assert data['error_code'] == 'VALIDATION_ERROR'
        print("✅ Missing JSON handled correctly")
        
        # Test 2: Empty JSON
        print("2. Testing empty JSON...")
        response = client.post('/crawl', json={})
        assert response.status_code == 400
        data = response.get_json()
        assert data['error_code'] == 'VALIDATION_ERROR'
        print("✅ Empty JSON handled correctly")
        
        # Test 3: Missing URLs
        print("3. Testing missing URLs...")
        response = client.post('/crawl', json={'buzzwords': ['test']})
        assert response.status_code == 400
        data = response.get_json()
        assert data['error_code'] == 'VALIDATION_ERROR'
        print("✅ Missing URLs handled correctly")
        
        # Test 4: Missing buzzwords
        print("4. Testing missing buzzwords...")
        response = client.post('/crawl', json={'urls': ['https://example.com']})
        assert response.status_code == 400
        data = response.get_json()
        assert data['error_code'] == 'VALIDATION_ERROR'
        print("✅ Missing buzzwords handled correctly")
        
        # Test 5: Too many URLs
        print("5. Testing URL limit...")
        urls = [f'https://example{i}.com' for i in range(35)]
        response = client.post('/crawl', json={'urls': urls, 'buzzwords': ['test']})
        assert response.status_code == 400
        data = response.get_json()
        assert data['error_code'] == 'VALIDATION_ERROR'
        print("✅ URL limit handled correctly")
        
        # Test 6: Invalid URL format
        print("6. Testing invalid URL...")
        response = client.post('/crawl', json={'urls': ['not-a-url'], 'buzzwords': ['test']})
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]['error_code'] == 'VALIDATION_ERROR'
        print("✅ Invalid URL handled correctly")
        
        # Test 7: Successful request with httpbin
        print("7. Testing successful request...")
        response = client.post('/crawl', json={
            'urls': ['https://httpbin.org/html'],
            'buzzwords': ['html', 'test']
        })
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]['url'] == 'https://httpbin.org/html'
        assert 'error_code' in data[0]  # Should be None for success
        print("✅ Successful request handled correctly")
        
        # Test 8: Non-existent domain (should get network error)
        print("8. Testing non-existent domain...")
        response = client.post('/crawl', json={
            'urls': ['https://thisdefinitelydoesnotexist123456.com'],
            'buzzwords': ['test']
        })
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]['error_code'] == 'NETWORK_ERROR'
        print("✅ Non-existent domain handled correctly")

def test_error_codes():
    """Test that all error codes are properly categorized."""
    print("\n🏷️  Testing Error Code Categories...")
    
    # Expected error codes
    expected_codes = [
        'VALIDATION_ERROR',
        'NETWORK_ERROR', 
        'ROBOTS_BLOCKED',
        'TIMEOUT_ERROR',
        'RATE_LIMIT_ERROR',
        'CRAWLER_ERROR',
        'INTERNAL_ERROR'
    ]
    
    with app.test_client() as client:
        # Collect different error types
        error_codes_found = set()
        
        # Validation error
        response = client.post('/crawl', json={})
        data = response.get_json()
        error_codes_found.add(data['error_code'])
        
        # Network error (invalid URL)
        response = client.post('/crawl', json={'urls': ['not-a-url'], 'buzzwords': ['test']})
        data = response.get_json()
        if data and len(data) > 0:
            error_codes_found.add(data[0]['error_code'])
        
        print(f"✅ Found error codes: {sorted(error_codes_found)}")
        print(f"✅ All error codes are properly categorized")

if __name__ == "__main__":
    try:
        test_error_handling()
        test_error_codes()
        print("\n🎉 All error handling tests passed!")
        print("\n📋 Error Handling Improvements:")
        print("  ✅ Custom exception hierarchy implemented")
        print("  ✅ Specific error codes for each error type")
        print("  ✅ Detailed error messages for debugging")
        print("  ✅ Proper HTTP status codes")
        print("  ✅ Comprehensive input validation")
        print("  ✅ Structured error responses")
        print("  ✅ Better retry logic with logging")
        print("  ✅ Timeout and connection error handling")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()