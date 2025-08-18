# test_websocket_python.py
import asyncio
import websockets
import json
import time

async def monitor_websocket():
    token = "YOUR_TOKEN_HERE"  # Replace with your token
    uri = f"ws://localhost:8000/ws/conversations/?token={token}"
    
    print(f"Connecting to {uri[:50]}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected successfully")
            start_time = time.time()
            
            # Receive initial data
            initial = await websocket.recv()
            print(f"📨 Initial data received")
            
            print("\n⏳ Monitoring connection... Send a WhatsApp message now")
            print("Press Ctrl+C to stop\n")
            
            # Keep listening
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    uptime = int(time.time() - start_time)
                    print(f"[{uptime}s] Received: {data['type']}")
                    
                    if data['type'] == 'conversation_update':
                        print(f"  ✅ Got update for conversation: {data.get('conversation_id')}")
                        
                except asyncio.TimeoutError:
                    # No message received, just continue
                    uptime = int(time.time() - start_time)
                    if uptime % 10 == 0:  # Log every 10 seconds
                        print(f"[{uptime}s] Still connected...")
                    continue
                    
    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ Connection closed: code={e.code}, reason={e.reason}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(monitor_websocket())