import time
from bluetooth import *

# Define the UUID, Major, and Minor values for the teacher's beacon
TEACHER_BEACON_UUID = "019637fa-978a-7a1c-8447-f914acdc999c"
TEACHER_BEACON_MAJOR = 1
TEACHER_BEACON_MINOR = 10

# You might need to adjust these values depending on your system's requirements
BEACON_INTERVAL = (
    0.1  # Advertisement interval in seconds (shorter for faster detection)
)
BEACON_POWER = -59  # Measured Tx power at 1 meter in dBm


def advertise_beacon():
    """Advertises a Bluetooth LE beacon with the teacher's specific UUID, Major, and Minor."""
    adv_data = AdvertiseData(
        adv_type=ADVERTISING_TYPE_CONNECTABLE_IDLE,
        appearance=0x00,
        flags=0x06,
        manufacturer_data={
            0x4C00: bytes(
                [
                    0x02,  # Beacon prefix for iBeacon
                    0x15,  # Length of the iBeacon advertisement payload
                    # UUID
                    0x01,
                    0x96,
                    0x37,
                    0xFA,
                    0x97,
                    0x8A,
                    0x7A,
                    0x1C,
                    0x84,
                    0x47,
                    0xF9,
                    0x14,
                    0xAC,
                    0xDC,
                    0x99,
                    0x9C,
                    # Major
                    (TEACHER_BEACON_MAJOR >> 8) & 0xFF,
                    TEACHER_BEACON_MAJOR & 0xFF,
                    # Minor
                    (TEACHER_BEACON_MINOR >> 8) & 0xFF,
                    TEACHER_BEACON_MINOR & 0xFF,
                    # Measured Power (Tx power at 1 meter)
                    (BEACON_POWER & 0xFF) - 256 if BEACON_POWER < 0 else BEACON_POWER,
                ]
            )
        },
    )

    try:
        adapter = getDefaultAdapter()
        advertiser = BluetoothAdvertisement(adapter, BEACON_INTERVAL, adv_data)
        advertiser.start()
        print(
            f"Broadcasting teacher beacon: UUID={TEACHER_BEACON_UUID}, Major={TEACHER_BEACON_MAJOR}, Minor={TEACHER_BEACON_MINOR}"
        )
        while True:
            time.sleep(1)
        advertiser.stop()  # This line will likely not be reached in this loop
    except Exception as e:
        print(f"Error advertising beacon: {e}")


if __name__ == "__main__":
    advertise_beacon()
