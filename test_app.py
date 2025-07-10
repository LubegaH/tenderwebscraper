#!/usr/bin/env python3
"""
Simple test script to verify the app works correctly after memory fixes.
"""
import json
from app import app

def test_app():
    """Test the Flask app endpoints."""
    print("🧪 Testing Flask app after memory fixes...")
    
    with app.test_client() as client:
        # Test the main page
        print("📄 Testing main page...")
        response = client.get('/')
        if response.status_code == 200:
            print("✅ Main page loads successfully")
        else:
            print(f"❌ Main page failed: {response.status_code}")
            return False
        
        # Test the crawl endpoint with a simple request
        print("🕷️  Testing crawl endpoint...")
        test_data = {
            'urls': ['https://httpbin.org/html'],
            'buzzwords': ['html', 'test']
        }
        
        response = client.post('/crawl', 
                              data=json.dumps(test_data),
                              content_type='application/json')
        
        if response.status_code == 200:
            print("✅ Crawl endpoint responds successfully")
            data = response.get_json()
            if isinstance(data, list) and len(data) > 0:
                print(f"✅ Received {len(data)} results")
                result = data[0]
                if 'url' in result and 'found' in result:
                    print("✅ Response format is correct")
                    if result.get('found'):
                        print(f"✅ Found buzzwords: {result['found']}")
                    else:
                        print("ℹ️  No buzzwords found (this is ok)")
                else:
                    print("❌ Response format is incorrect")
                    return False
            else:
                print("❌ No results returned")
                return False
        else:
            print(f"❌ Crawl endpoint failed: {response.status_code}")
            try:
                error_data = response.get_json()
                print(f"Error details: {error_data}")
            except:
                print(f"Raw response: {response.data}")
            return False
    
    print("✅ All tests passed!")
    return True

if __name__ == "__main__":
    success = test_app()
    if success:
        print("\n🎉 App is working correctly! You can now run it with:")
        print("   python3 run.py")
        print("   Then visit: http://localhost:5000")
    else:
        print("\n❌ Tests failed. Please check the errors above.")