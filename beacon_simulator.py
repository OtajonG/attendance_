import sys

sys.coinit_flags = 0
import asyncio
import platform
from bleak import BleakClient, BleakScanner
from bleak.backends.scanner import AdvertisementData
import struct

TEACHER_BEACON_UUID = "019637fa-978a-7a1c-8447-f914acdc999c"
TEACHER_BEACON_MAJOR = 1
TEACHER_BEACON_MINOR = 10
BEACON_POWER = -59  # Approximate Tx power


async def advertise_ibeacon():
    if platform.system() != "Windows":
        print(
            "BLE advertising using bleak is primarily supported on Windows for this example."
        )
        return

    from bleak.winrt import winrt_bluetooth
    from bleak.exc import BleakError

    manufacturer_id = 0x4C00  # Apple

    beacon_data = bytes(
        [
            0x02,  # Flags length
            0x01,  # Flags data type
            0x1A,  # LE General Discoverable Mode + BR/EDR Not Supported
            0xFF,  # Manufacturer Specific Data
            0x4C,
            0x00,  # Apple Manufacturer ID (little endian)
            0x02,  # iBeacon prefix
            0x15,  # Length of iBeacon advertising payload
            # Proximity UUID (little endian)
            0xFA,
            0x37,
            0x96,
            0x01,
            0x8A,
            0x97,
            0x1C,
            0x7A,
            0x47,
            0x84,
            0xF9,
            0x14,
            0xDC,
            0xAC,
            0x99,
            0x9C,
            # Major (big endian)
            (TEACHER_BEACON_MAJOR >> 8) & 0xFF,
            TEACHER_BEACON_MAJOR & 0xFF,
            # Minor (big endian)
            (TEACHER_BEACON_MINOR >> 8) & 0xFF,
            TEACHER_BEACON_MINOR & 0xFF,
            # Calibrated Tx Power (signed byte)
            struct.pack("b", BEACON_POWER)[0],
        ]
    )

    try:
        bluetooth_radio = await winrt_bluetooth.get_default_radio()
        if not bluetooth_radio:
            print("Could not get default Bluetooth radio.")
            return

        advertisement_data = AdvertisementData(
            local_name="iBeaconSimulator",
            manufacturer_data={manufacturer_id: beacon_data},
            service_uuids=[],
        )

        print(
            f"Advertising iBeacon: UUID={TEACHER_BEACON_UUID}, Major={TEACHER_BEACON_MAJOR}, Minor={TEACHER_BEACON_MINOR}, TxPower={BEACON_POWER}"
        )
        await bluetooth_radio.start_advertising(advertisement_data)

        while True:
            await asyncio.sleep(1)

    except BleakError as e:
        print(f"Bleak error during advertising: {e}")
    except NotImplementedError:
        print("BLE advertising is not implemented for this platform with Bleak.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(advertise_ibeacon())
