import pycom

radio = pycom.PyCom("0x94", port="COM10", debug=True)
#radio.power_on() # works
print(f"Current frequency: {radio.read_operating_frequency()}Hz")
radio.send_operating_frequency(14123456)
#radio.power_off() # works