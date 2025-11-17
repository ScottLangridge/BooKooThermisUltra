import asyncio
import time

from BookooScale import BookooScale


async def main():
    scale = BookooScale()
    assert await scale.establish_connection()

    try:
        while True:
            print(scale.weight)
            await asyncio.sleep(0.1)
    except Exception as e:
        # Disconnect gracefully in case of any issues
        print("Exception: " + str(e))
        await scale.disconnect()

asyncio.run(main())