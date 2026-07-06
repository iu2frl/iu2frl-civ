
import sys
from pathlib import Path
import time

try:
    # Import the library installed using pip
    from iu2frl_civ.device_factory import DeviceFactory
    from iu2frl_civ.enums import DeviceType, OperatingMode
    print("Imported iu2frl_civ from pip-installed package.")
except ImportError:
    sys.path.append(str(Path(__file__).parent.parent))
    from src.iu2frl_civ.device_factory import DeviceFactory
    from src.iu2frl_civ.enums import DeviceType, OperatingMode
    print("Imported iu2frl_civ from local source code.")


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
            chunked_messages = chunkstring(text_to_send, 30)
            chunked_messages = list(chunked_messages)  # Convert generator to list to count chunks
            chunks_count = len(chunked_messages)
            print(f"Sending {chunks_count} chunks of CW messages...")
            for i in range(chunks_count):  # Split the text into chunks of 30 characters
                try:
                    print(f"Sending chunk {i+1}/{chunks_count}: {chunked_messages[i]}")
                    radio.send_cw_message(chunked_messages[i])  # Send each chunk as a CW message
                    time.sleep(0.5)
                    if not radio.read_mox_status():
                        print("Radio is not transmitting. Please check if the BK IN was activated.")
                        break
                    while radio.read_mox_status():
                        time.sleep(0.1)
                except Exception as e:
                    print(f"Error sending CW message: {e}")

if __name__ == "__main__":
    main()
