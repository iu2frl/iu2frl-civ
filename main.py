import pycom

radio = pycom.PyCom("0x94", port="COM10", debug=True)
#radio.power_on() # works
print(f"Frequency: {radio.read_operating_frequency()}Hz")
#radio.send_operating_frequency(14000000)
print(radio._encode_frequency(14000000))  # b'\x00\x00\x00\x14\x00'
print(radio._encode_frequency(14050123))  # b'\x23\x01\x05\x14\x00'
print(radio._encode_frequency(28050123))  # b'\x23\x01\x05\x28\x00'
#radio.power_off() # works