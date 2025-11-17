import asyncio
import time

from BookooScale import BookooScale


async def main():
    scale = BookooScale()
    assert await scale.establish_connection()

    try:
        await scale.send_tare_and_timer_start()
        print(scale.weight)
        await asyncio.sleep(3.5)
        print(scale.weight)
        await scale.send_timer_stop()
        print(scale.weight)
        await asyncio.sleep(3)
        print(scale.weight)
        await scale.send_timer_reset()
        print(scale.weight)
    except Exception as e:
        # Disconnect gracefully in case of any issues
        print("Exception: " + str(e))
        await scale.disconnect()
    await scale.disconnect()

asyncio.run(main())