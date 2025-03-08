import asyncio
import httpx
import json
import sys

async def test_health():
    """Test the health endpoint."""
    print("Testing health endpoint...")
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/api/health")
        print(f"Status code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        print()

async def test_models():
    """Test the models endpoint."""
    print("Testing models endpoint...")
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/api/models")
        print(f"Status code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        print()

async def test_chat(prompt):
    """Test the chat endpoint."""
    print(f"Testing chat endpoint with prompt: '{prompt}'...")
    payload = {
        "prompt": prompt,
        "model": "deepseek-r1:1.5b",
        "system_prompt": "You are a helpful AI assistant. Provide concise responses.",
        "temperature": 0.7,
        "max_tokens": 500
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post("http://localhost:8000/api/chat", json=payload)
        print(f"Status code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        print()

async def main():
    """Run all tests."""
    # Test health endpoint
    await test_health()
    
    # Test models endpoint
    await test_models()
    
    # Test chat endpoint with different prompts
    prompts = [
        "What is FastAPI?",
        "Write a simple Python function to calculate the factorial of a number.",
        "Tell me a short joke."
    ]
    
    if len(sys.argv) > 1:
        # Use command line argument as prompt if provided
        prompts = [" ".join(sys.argv[1:])]
    
    for prompt in prompts:
        await test_chat(prompt)

if __name__ == "__main__":
    asyncio.run(main()) 