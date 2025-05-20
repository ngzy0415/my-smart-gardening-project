import time
import board
from adafruit_onewire.bus import OneWireBus
from adafruit_ds18x20 import DS18X20

class WaterproofTempSensor:
    def __init__(self, pin):
        self.bus = OneWireBus(pin)
        self.sensor = DS18X20(self.bus, self.bus.scan()[0])

    def read_temperature(self):
        return self.sensor.temperature
