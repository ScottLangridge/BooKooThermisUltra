import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.drivers.Scale.BookooScale import BookooScale


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

        # Loop weight for ten seconds
        for i in range(100):
            print(str(scale.read_weight()) + "g")
            await asyncio.sleep(0.1)

        # Disconnect
        await scale.disconnect()

    except Exception as e:
        # Disconnect gracefully in case of any issues
        print("Exception: " + str(e))
        await scale.disconnect()
    await scale.disconnect()

asyncio.run(main())