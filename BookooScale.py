from bleak import BleakScanner, BleakClient


class BookooScale:
    def __init__(self, address=None):
        self.address = address
        self.client = None

    async def establish_connection(self):
        print("Establishing connection...")

        if self.address is None:
            await self.discover_device()

        if self.address is None:
            print("Failed to connect!")
            return False

        self.client = BleakClient(self.address)
        await self.client.connect()
        success = self.client.is_connected
        print(f'Successfully connected to {self.client.name}!')
        await self.client.disconnect()
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

    def _is_bookoo_device(self, device):
        if device.name is None:
            return False
        else:
            return device.name.lower().startswith("bookoo")
