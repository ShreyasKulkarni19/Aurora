"""Simple test script for the QA service."""

import asyncio
import httpx
import json


async def test_qa_service():
    """Test the QA service endpoints."""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test health endpoint
        print("Testing health endpoint...")
        try:
            response = await client.get(f"{base_url}/api/v1/health")
            print(f"Health check: {response.status_code} - {response.json()}")
        except Exception as e:
            print(f"Health check failed: {e}")
            return
        
        # Test ask endpoint (GET)
        print("\nTesting ask endpoint (GET)...")
        question = "Who is planning a trip to Paris?"
        try:
            response = await client.get(
                f"{base_url}/api/v1/ask",
                params={"question": question}
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except Exception as e:
            print(f"Ask (GET) failed: {e}")
        
        # Test ask endpoint (POST)
        print("\nTesting ask endpoint (POST)...")
        try:
            response = await client.post(
                f"{base_url}/api/v1/ask",
                json={"question": question}
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except Exception as e:
            print(f"Ask (POST) failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_qa_service())

