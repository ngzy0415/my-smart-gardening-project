import time
import board
import analogio

class MoistureSensor:
    def __init__(self, pin):
        self.sensor = analogio.AnalogIn(pin)

    def read_moisture(self):
        return (self.sensor.value / 65535) * 100