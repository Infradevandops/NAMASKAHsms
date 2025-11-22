"""Simple load testing script - WITH ERROR HANDLING."""
import asyncio
import httpx
import time
from app.core.logging import get_logger

logger = get_logger(__name__)

async def test_endpoint(client, url, method="GET", data=None):
    """Test single endpoint."""
    try:
        if method == "GET":
            await client.get(url, timeout=10.0)
        else:
            await client.post(url, json=data, timeout=10.0)
        return True
    except httpx.TimeoutException as e:
        logger.warning(f"Timeout for {url}: {e}")
        return False
    except httpx.RequestError as e:
        logger.error(f"Request failed for {url}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error testing {url}: {e}")
        return False

async def run_load_test(url: str, num_requests: int = 100, concurrent: int = 10):
    """Run load test."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            start = time.time()
            
            tasks = []
            successful = 0
            failed = 0
            
            for i in range(num_requests):
                tasks.append(test_endpoint(client, url))
                if len(tasks) >= concurrent:
                    results = await asyncio.gather(*tasks)
                    successful += sum(results)
                    failed += len(results) - sum(results)
                    tasks = []
            
            if tasks:
                results = await asyncio.gather(*tasks)
                successful += sum(results)
                failed += len(results) - sum(results)
            
            duration = time.time() - start
            rps = num_requests / duration if duration > 0 else 0
            
            print(f"Load Test Results:")
            print(f"   Requests: {num_requests}")
            print(f"   Successful: {successful}")
            print(f"   Failed: {failed}")
            print(f"   Duration: {duration:.2f}s")
            print(f"   RPS: {rps:.2f}")
            print(f"   Avg Response: {(duration/num_requests)*1000:.2f}ms")
    except Exception as e:
        logger.error(f"Load test failed: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(run_load_test("http://localhost:8000/api/system/health", 100, 10))
    except KeyboardInterrupt:
        print("Load test interrupted")
    except Exception as e:
        print(f"Error running load test: {e}")
