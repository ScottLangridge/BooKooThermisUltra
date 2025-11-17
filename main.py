import asyncio

from BookooScale import BookooScale


async def main():
    scale = BookooScale()

    try:
        assert await scale.establish_connection()
        await scale.disconnect()
    except Exception as e:
        # Disconnect gracefully in case of any issues
        print("Exception: " + str(e))
        await scale.disconnect()

asyncio.run(main())