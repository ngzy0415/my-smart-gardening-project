import time
import board
import pwmio
from adafruit_motor import servo

class ServoMotor:
    def __init__(self, pin):
        pwm = pwmio.PWMOut(pin, duty_cycle=2 ** 15, frequency=50)
        self.servo = servo.Servo(pwm, min_pulse=500, max_pulse=2500)
        self.angle = 180

    def move_to(self, angle):
        self.servo.angle = angle
        self.angle = angle