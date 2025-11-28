import asyncio
import time

from bleak import BleakScanner, BleakClient

WEIGHT_UUID = "0000ff11-0000-1000-8000-00805f9b34fb"
COMMAND_UUID = "0000ff12-0000-1000-8000-00805f9b34fb"

TARE_PACKET = bytearray([0x03, 0x0A, 0x01, 0x00, 0x00, 0x08])
TIMER_START_PACKET = bytearray([0x03, 0x0A, 0x04, 0x00, 0x00, 0x0A])
TIMER_STOP_PACKET = bytearray([0x03, 0x0A, 0x05, 0x00, 0x00, 0x0D])
TIMER_RESET_PACKET = bytearray([0x03, 0x0A, 0x06, 0x00, 0x00, 0x0C])
TARE_AND_TIMER_START_PACKET = bytearray([0x03, 0x0A, 0x07, 0x00, 0x00, 0x00])


class BookooScale:
    def __init__(self):
        self._address = None
        self._client = None

        self._weight = None

        # Timer tracking
        self._timer_start_time = None
        self._timer_running = False
        self._timer_elapsed = 0.0  # Accumulated time when timer is paused

    # ----- CONNECTIVITY -----
    async def establish_connection(self):
        print("Establishing connection...")

        # Find device if not already located
        if self._address is None:
            await self._discover_device()

        # If not found, fail
        if self._address is None:
            print("Failed to establish connection.")
            return False

        # Connect
        self._client = BleakClient(self._address)
        success = await self._connect()
        if success:
            print(f'Successfully connected to {self._client.name}!')
        return success

    def is_connected(self):
        if not self._client:
            return False
        return self._client.is_connected

    async def disconnect(self):
        if self.is_connected():
            print("Disconnecting...")
            await self._client.disconnect()
            self._weight = None
            return not self.is_connected()
        else:
            print("No device connected to disconnect from.")

    # ----- READ COMMANDS -----
    def read_weight(self):
        return self._weight

    def read_time(self):
        """Read current timer value in seconds"""
        if not self._timer_running:
            return self._timer_elapsed

        # Timer is running, calculate current elapsed time
        current_time = time.time()
        running_time = current_time - self._timer_start_time
        return self._timer_elapsed + running_time

    def is_timer_running(self):
        """Check if timer is currently running"""
        return self._timer_running

    # ----- WRITE COMMANDS -----
    async def send_tare(self):
        print("Tare.")
        await self._client.write_gatt_char(COMMAND_UUID, TARE_PACKET)

    async def send_timer_start(self):
        print("Start Timer.")

        if self._timer_running:
            print("Timer already running, ignoring start command.")
            return

        if self._timer_elapsed > 0:
            print("Timer is paused with accumulated time, ignoring start command. Reset timer first.")
            return

        await self._client.write_gatt_char(COMMAND_UUID, TIMER_START_PACKET)

        # Update timer tracking - always update to stay in sync with scale
        self._timer_start_time = time.time()
        self._timer_running = True

    async def send_timer_stop(self):
        print("Stop Timer.")

        if not self._timer_running:
            print("Timer not running, ignoring stop command.")
            return

        await self._client.write_gatt_char(COMMAND_UUID, TIMER_STOP_PACKET)

        # Accumulate elapsed time
        current_time = time.time()
        self._timer_elapsed += current_time - self._timer_start_time
        self._timer_running = False

    async def send_timer_reset(self):
        print("Reset Timer.")

        if self._timer_running:
            print("Timer is running, ignoring reset command. Stop timer first.")
            return

        await self._client.write_gatt_char(COMMAND_UUID, TIMER_RESET_PACKET)

        # Reset timer tracking
        self._timer_start_time = None
        self._timer_running = False
        self._timer_elapsed = 0.0

    async def send_tare_and_timer_start(self):
        print("Tare and Start Timer.")

        if self._timer_running:
            print("Timer already running, ignoring tare+start command.")
            return

        await self._client.write_gatt_char(COMMAND_UUID, TARE_AND_TIMER_START_PACKET)

        # Update timer tracking (same as timer_start) - always update to stay in sync
        self._timer_start_time = time.time()
        self._timer_running = True

    # ----- PRIVATE -----
    async def _discover_device(self):
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
            self._address = bookoo_devices[0].address
            return True

    async def _connect(self):
        print("Connecting...")
        await self._client.connect()

        # Wait for first weight value
        asyncio.create_task(self._poll_weight())
        while self._weight is None:
            await asyncio.sleep(0.05)
        return self.is_connected()

    def _is_bookoo_device(self, device):
        if device.name is None:
            return False
        else:
            return device.name.lower().startswith("bookoo")

    def _on_weight(self, sender, data: bytearray):
        if len(data) != 20:
            return

        checksum = 0
        for b in data[:19]:
            checksum ^= b
        if checksum != data[19]:
            return

        sign = 1 if data[6] == 43 else -1
        raw = (data[7] << 16) | (data[8] << 8) | data[9]
        self._weight = sign * (raw / 100)

    async def _poll_weight(self):
        await self._client.start_notify(WEIGHT_UUID, self._on_weight)

    async def _send_command(self, data1, data2, data3, datasum=0x00):
        """Send a 6-byte command to the scale (checksum not required)."""
        if self._client is None or not self._client.is_connected:
            raise Exception("Not connected")

        packet = bytearray([0x03, 0x0A, data1, data2, data3, datasum])
        await self._client.write_gatt_char(COMMAND_UUID, packet)
