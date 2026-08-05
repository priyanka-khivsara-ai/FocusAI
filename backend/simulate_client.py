import asyncio
import websockets
import json
import time

async def simulate():
    uri = "ws://localhost:8000/ws/user/karanjkarak078/AI-123"
    
    dummy_payload = {
        "right_eye": [{"x": 0.5, "y": 0.5, "z": 0.1} for _ in range(16)],
        "left_eye": [{"x": 0.4, "y": 0.5, "z": 0.1} for _ in range(16)],
        "irises": [{"x": 0.5, "y": 0.5, "z": 0.1}, {"x": 0.4, "y": 0.5, "z": 0.1}],
        "matrix": [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0],
        "mouth": [{"x": 0.45, "y": 0.7, "z": 0.1} for _ in range(40)],
        "left_eyebrow": [{"x": 0.4, "y": 0.3, "z": 0.1} for _ in range(10)],
        "right_eyebrow": [{"x": 0.5, "y": 0.3, "z": 0.1} for _ in range(10)]
    }

    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket.")
            for i in range(3):
                await websocket.send(json.dumps(dummy_payload))
                response = await websocket.recv()
                print(f"Received: {response}")
                await asyncio.sleep(1)
            print("Simulation complete.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(simulate())
