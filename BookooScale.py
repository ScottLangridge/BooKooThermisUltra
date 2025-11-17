import asyncio

from bleak import BleakScanner, BleakClient

WEIGHT_UUID = "0000ff11-0000-1000-8000-00805f9b34fb"


class BookooScale:
    def __init__(self, address=None):
        self.address = address
        self.client = None

        self.weight = None

    async def establish_connection(self):
        print("Establishing connection...")

        if self.address is None:
            await self.discover_device()

        self.client = BleakClient(self.address)
        success = await self.connect()
        if success:
            print(f'Successfully connected to {self.client.name}!')
        return success

    async def discover_device(self):
        print("Discovering Devices...")
        devices = await BleakScanner.discover()
        bookoo_devices = [i for i in devices if self._is_bookoo_device(i)]

        if len(bookoo_devices) == 0:
            print("No BooKoo devices found.")
            return False
        elif len(bookoo_devices) > 1:
            print("Multiple BooKoo devices found. Unhandled use case!")
            return False
        else:
            print("Device Found!")
            self.address = bookoo_devices[0].address
            return True

    async def connect(self):
        print("Connecting...")
        await self.client.connect()
        asyncio.create_task(self.poll_weight())
        return self.connected()

    def connected(self):
        return self.client.is_connected

    async def disconnect(self):
        print("Disconnecting...")
        await self.client.disconnect()
        self.weight = None
        return not self.connected()

    def on_weight(self, sender, data: bytearray):
        if len(data) != 20:
            return

        checksum = 0
        for b in data[:19]:
            checksum ^= b
        if checksum != data[19]:
            return

        sign = 1 if data[6] == 43 else -1
        raw = (data[7] << 16) | (data[8] << 8) | data[9]
        self.weight = sign * (raw / 100)

    async def poll_weight(self):
        await self.client.start_notify(WEIGHT_UUID, self.on_weight)

    def _is_bookoo_device(self, device):
        if device.name is None:
            return False
        else:
            return device.name.lower().startswith("bookoo")
