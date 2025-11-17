from bleak import BleakScanner, BleakClient


class BookooScale:
    def __init__(self, address=None):
        self.address = address
        self.client = None

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
        return self.connected()

    def connected(self):
        return self.client.is_connected

    async def disconnect(self):
        print("Disconnecting...")
        await self.client.disconnect()
        return not self.connected()

    def _is_bookoo_device(self, device):
        if device.name is None:
            return False
        else:
            return device.name.lower().startswith("bookoo")
