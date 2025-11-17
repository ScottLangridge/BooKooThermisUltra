import asyncio

from BookooScale import BookooScale

async def main():
    scale = BookooScale()
    assert await scale.establish_connection()

asyncio.run(main())