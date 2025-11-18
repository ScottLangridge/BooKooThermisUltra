import asyncio
import time

from BookooScale import BookooScale


async def main():
    scale = BookooScale()
    assert await scale.establish_connection()

    try:
        # Tare and count to three.
        await scale.send_tare_and_timer_start()
        await asyncio.sleep(3.1)
        await scale.send_timer_stop()

        # Wait three seconds and reset
        await asyncio.sleep(3)
        await scale.send_timer_reset()

        # Loop weight
        while True:
            print(str(scale.weight) + "g")
            await asyncio.sleep(0.1)


    except Exception as e:
        # Disconnect gracefully in case of any issues
        print("Exception: " + str(e))
        await scale.disconnect()
    await scale.disconnect()

asyncio.run(main())