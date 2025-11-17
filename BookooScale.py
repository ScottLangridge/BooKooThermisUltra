import asyncio

from bleak import BleakScanner, BleakClient

WEIGHT_UUID = "0000ff11-0000-1000-8000-00805f9b34fb"
COMMAND_UUID = "0000ff12-0000-1000-8000-00805f9b34fb"

TARE_PACKET = bytearray([0x03, 0x0A, 0x01, 0x00, 0x00, 0x08])
TIMER_START_PACKET = bytearray([0x03, 0x0A, 0x04, 0x00, 0x00, 0x0A])
TIMER_STOP_PACKET = bytearray([0x03, 0x0A, 0x05, 0x00, 0x00, 0x0D])
TIMER_RESET_PACKET = bytearray([0x03, 0x0A, 0x06, 0x00, 0x00, 0x0C])
TARE_AND_TIMER_START_PACKET = bytearray([0x03, 0x0A, 0x07, 0x00, 0x00, 0x00])


class BookooScale:
    def __init__(self, address=None):
        self.address = address
        self.client = None

        self.weight = None

    async def establish_connection(self):
        print("Establishing connection...")

        if self.address is None:
            await self.discover_device()
        if self.address is None:
            print("Failed to establish connection.")
            return False

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
        while self.weight is None:
            await asyncio.sleep(0.05)
        return self.connected()

    def connected(self):
        if not self.client:
            return False
        return self.client.is_connected

    async def disconnect(self):
        if self.connected():
            print("Disconnecting...")
            await self.client.disconnect()
            self.weight = None
            return not self.connected()
        else:
            print("No device connected to disconnect from.")

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

    async def _send_command(self, data1, data2, data3, datasum=0x00):
        """Send a 6-byte command to the scale (checksum not required)."""
        if self.client is None or not self.client.is_connected:
            raise Exception("Not connected")

        packet = bytearray([0x03, 0x0A, data1, data2, data3, datasum])
        await self.client.write_gatt_char(COMMAND_UUID, packet)

    async def send_tare(self):
        print("Tare.")
        print(await self.client.write_gatt_char(COMMAND_UUID, TARE_PACKET))

    async def send_timer_start(self):
        print("Start Timer.")
        await self.client.write_gatt_char(COMMAND_UUID, TIMER_START_PACKET)

    async def send_timer_stop(self):
        print("Stop Timer.")
        await self.client.write_gatt_char(COMMAND_UUID, TIMER_STOP_PACKET)

    async def send_timer_reset(self):
        print("Reset Timer.")
        await self.client.write_gatt_char(COMMAND_UUID, TIMER_RESET_PACKET)

    async def send_tare_and_timer_start(self):
        print("Tare and Start Timer.")
        await self.client.write_gatt_char(COMMAND_UUID, TARE_AND_TIMER_START_PACKET)

    def _is_bookoo_device(self, device):
        if device.name is None:
            return False
        else:
            return device.name.lower().startswith("bookoo")
