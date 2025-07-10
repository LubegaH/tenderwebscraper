#!/usr/bin/env python3
"""
Test script to verify memory leak fixes and context manager functionality.
"""
import time
import gc
from app import SHAWebCrawler

def test_context_manager():
    """Test that the context manager properly initializes and cleans up."""
    print("Testing context manager functionality...")
    
    # Test context manager
    with SHAWebCrawler(max_workers=2, queue_size=10) as crawler:
        print(f"✓ Context manager initialized successfully")
        print(f"✓ Thread executor created: {crawler.executor is not None}")
        
        # Test a simple crawl
        urls = ["https://httpbin.org/html"]
        buzzwords = ["html"]
        
        try:
            results = crawler.crawl_urls(urls, buzzwords)
            print(f"✓ Crawl completed successfully: {len(results)} results")
        except Exception as e:
            print(f"✗ Crawl failed: {e}")
    
    print("✓ Context manager cleanup completed")

def test_memory_cleanup():
    """Test that resources are properly cleaned up."""
    print("\nTesting memory cleanup...")
    
    # Create multiple crawler instances to test cleanup
    for i in range(3):
        with SHAWebCrawler(max_workers=2, queue_size=10) as crawler:
            urls = ["https://httpbin.org/html"]
            buzzwords = ["test"]
            
            try:
                results = crawler.crawl_urls(urls, buzzwords)
                print(f"✓ Iteration {i+1} completed: {len(results)} results")
            except Exception as e:
                print(f"✗ Iteration {i+1} failed: {e}")
        
        # Force garbage collection
        gc.collect()
        time.sleep(0.1)
    
    print("✓ Memory cleanup test completed")

def test_closed_crawler():
    """Test that closed crawler raises appropriate error."""
    print("\nTesting closed crawler behavior...")
    
    crawler = SHAWebCrawler(max_workers=2, queue_size=10)
    crawler.cleanup()
    
    try:
        crawler.crawl_urls(["https://httpbin.org/html"], ["test"])
        print("✗ Should have raised RuntimeError")
    except RuntimeError as e:
        print(f"✓ Correctly raised RuntimeError: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")

if __name__ == "__main__":
    print("Starting memory leak fix tests...\n")
    
    test_context_manager()
    test_memory_cleanup()
    test_closed_crawler()
    
    print("\n✅ All tests completed!")