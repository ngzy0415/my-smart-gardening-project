import time
import board
import digitalio
import busio
import pyRTOS
import dcmotor
import stepper_motor

# UART setup for communication
uart = busio.UART(board.GP0, board.GP1, baudrate=9600)

# Initialize devices
dc_motor = dcmotor.DCMotor(board.GP8, board.GP9)
stepper1 = stepper_motor.StepperMotor([board.GP2, board.GP3, board.GP4, board.GP5], 0.001)
relay = digitalio.DigitalInOut(board.GP15)
relay.direction = digitalio.Direction.OUTPUT

access_granted = False

def execute_command(command):
    global access_granted
    print(f"Executing command: {command}")
    if command == 'GRANT':
        access_granted = True
        print("Access granted: DC Motor and other devices can run")
        for _ in range(10):  # Quick on and off to simulate slow speed
            dc_motor.move_forward()
            time.sleep(1)
            dc_motor.stop()
            time.sleep(1)
    elif command == 'REVOKE':
        access_granted = False
        dc_motor.stop
        print("Access revoked: DC Motor and relay stopped")
    elif command == 'R_O':
        print("Roof Open")
        stepper1.step_motor(2000, 'backward')
    elif command == 'R_C':
        print("Roof Close")
        stepper1.step_motor(2000, 'forward')
    elif command == 'M_A':
        relay.value = True
        print("Relay activated for moisture")
        time.sleep(4)  # Adjusted execution time
        relay.value = False
        print("Relay deactivated after 4 seconds")
    elif command == 'W_T_A':
        relay.value = True
        print("Relay activated for water temperature")
        time.sleep(2)  # Adjusted execution time
        relay.value = False
        print("Relay deactivated after 2 seconds")
    elif command == 'R_A':
        print("Roof closing (Rain detected)")
        stepper1.step_motor(2000, 'forward')
    elif command == 'L_1_A':
        print("Roof opening (LDR1_ACTIVATE)")
        stepper1.step_motor(2000, 'backward')
    elif command == 'L_2_A':
        print("Roof closing (LDR2_ACTIVATE)")
        stepper1.step_motor(2000, 'forward')
    elif command == 'D_C_F':
        dc_motor.move_forward()
        print("DC Motor running fast due to high temperature")
    elif command == 'D_M_S':
        for _ in range(10):  # Quick on and off to simulate slow speed
            dc_motor.move_forward()
            time.sleep(1)
            dc_motor.stop()
            time.sleep(2)
        print("DC Motor running slow due to low temperature")
    elif command == 'W_P_A':
        relay.value = True
        print("Relay activated for water pump")
        time.sleep(4)  # Adjusted execution time
        relay.value = False
        print("Relay deactivated after 5 seconds")
        

# pyRTOS Tasks
def command_receiver_task(self):
    while True:
        command = uart.read(32)
        if command:
            command = command.decode('utf-8').strip()
            print(f"Received command: {command}")
            execute_command(command)
        yield [pyRTOS.timeout(1)]  # Reduce timeout to ensure constant command checking

# Adding tasks to pyRTOS
pyRTOS.add_task(pyRTOS.Task(command_receiver_task, name="Command Receiver Task"))

pyRTOS.start()

print("Starting Sensor Hub System...")