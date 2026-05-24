import asyncio
import websockets

async def test_ws():
    uri = "ws://localhost:8000/api/v1/ws/interview/a68b926b-dbc1-4f83-8637-b88df761c19a"
    try:
        async with websockets.connect(uri) as ws:
            print("Connected!")
    except Exception as e:
        print(f"Connection failed: {e}")

asyncio.run(test_ws())
