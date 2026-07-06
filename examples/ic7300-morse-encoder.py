# Import the library installed using pip
# from iu2frl_civ.device_base import DeviceBase
# from iu2frl_civ.device_factory import DeviceFactory
# from iu2frl_civ.enums import DeviceType, OperatingMode

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from src.iu2frl_civ.device_factory import DeviceFactory
from src.iu2frl_civ.exceptions import CivTimeoutException
from src.iu2frl_civ.enums import DeviceType, OperatingMode, SelectedFilter, VFOOperation, ScanMode

def chunkstring(string, length):
    """Split a string into chunks of a specified length."""

    return (string[0+i:length+i] for i in range(0, len(string), length))

def main():
    """
    Main function to initialize the radio and send CW messages.
    This function initializes the IC-7300 radio using the DeviceFactory and enters a loop to send CW messages.
    The user can input text to send as CW messages, which will be split into chunks of 30 characters for transmission.
    """

    try:
        radio = DeviceFactory.get_repository(radio_address="0x94", device_type=DeviceType.IC_7300, port="COM8", baudrate=115200, fake=False)
        radio.set_operating_mode(OperatingMode.CW)
    except Exception as e:
        print(f"Error initializing radio: {e}")
        exit(1)

    while True:
        text_to_send = input("Enter text to send (or 'exit' to quit): ")
        if text_to_send.lower() == 'exit':
            break
        else:
            for chunk in chunkstring(text_to_send, 30):  # Split the text into chunks of 30 characters
                try:
                    radio.send_cw_message(chunk)  # Send each chunk as a CW message
                    
                except Exception as e:
                    print(f"Error sending CW message: {e}")

if __name__ == "__main__":
    main()
