#!/usr/bin/env python3
from ev3dev2.motor import LargeMotor, OUTPUT_A, SpeedPercent
import time
try:
    motor_A = LargeMotor(OUTPUT_A)
except Exception as e:
    print("Error: Motor not connected to port A.")
    print(e)
    exit()
print("Starting program.")

print("Rotating motor +360 degrees...")
motor_A.on_for_degrees(
    speed=SpeedPercent(50),
    degrees=360
)

time.sleep(1)

print("Rotating motor -360 degrees...")
motor_A.on_for_degrees(
    speed=SpeedPercent(50),
    degrees=-360
)
