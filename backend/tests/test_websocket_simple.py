# test_websocket_simple.py
import asyncio
import websockets
import json
import sys

async def test_websocket(token):
    # Test with the simpler endpoint first
    uri = f"ws://localhost:8000/ws/test/?token={token}"
    
    print(f"Token: {token[:50]}...")
    print(f"Connecting to: {uri}")
    
    try:
        # Remove extra_headers - not supported in your version
        async with websockets.connect(uri) as websocket:
            print("✅ Connected successfully!")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            print(f"Received: {welcome}")
            
            # Send a test message
            await websocket.send(json.dumps({"test": "hello"}))
            
            # Get response
            response = await websocket.recv()
            print(f"Response: {response}")
            
    except websockets.exceptions.InvalidHandshake as e:
        print(f"❌ Connection rejected with status: {e}")
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Get a fresh token first
        print("Getting a fresh token...")
        import requests
        
        response = requests.post(
            "http://localhost:8000/api/auth/login",
            json={
                "email": "candai1996@hotmail.com",  # Replace with your email
                "password": "Cdkdad123!"   # Replace with your password
            }
        )
        
        if response.status_code == 200:
            token = response.json()["access"]
            print(f"Got token: {token[:50]}...")
        else:
            print(f"Login failed: {response.text}")
            sys.exit(1)
    else:
        token = sys.argv[1]
    
    asyncio.run(test_websocket(token))