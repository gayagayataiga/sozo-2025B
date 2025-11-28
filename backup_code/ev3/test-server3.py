#!/usr/bin/env python3

import socket
from ev3dev2.motor import LargeMotor, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C, SpeedPercent
import sys

# --- Motor A Setup (LargeMotor) ---
try:
    motor_A = LargeMotor(OUTPUT_A)
    print("Motor A (Large) initialized on port A.")
except Exception as e:
    print("Error: Motor not connected to port A.", file=sys.stderr)
    print(e, file=sys.stderr)
    sys.exit(1)

# --- Motor B Setup (MediumMotor) ---
try:
    motor_B = MediumMotor(OUTPUT_B)
    print("Motor B (Medium) initialized on port B.")
except Exception as e:
    print("Error: Motor not connected to port B.", file=sys.stderr)
    print(e, file=sys.stderr)
    sys.exit(1)

# --- Motor C Setup (MediumMotor) ---
try:
    motor_C = LargeMotor(OUTPUT_C)
    print("Motor C (Medium) initialized on port C.")
except Exception as e:
    print("Error: Motor not connected to port C.", file=sys.stderr)
    print(e, file=sys.stderr)
    sys.exit(1)

# --- Server Configuration ---
HOST = '0.0.0.0'
PORT = 65432
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print("Server is listening for Angle-Control commands on port", PORT)
    print("Waiting for connection...")

    try:
        while True:
            conn, addr = s.accept()
            with conn:
                print("Connected by", addr)
                print(
                    "Use commands like 'A:90:50', 'B:-45:30','C:-30:30', 'A:stop', 'stop_all', 'shutdown'")
                while True:
                    data = conn.recv(1024)
                    if not data:
                        print("Connection with ", addr, " closed.")
                        break

                    command = data.decode('utf-8').strip().lower()
                    if not command:
                        continue

                    print("Received command:", command)

                    # --- Command Handling ---

                    if command == "stop_all":
                        motor_A.off()
                        motor_B.off()
                        motor_C.off()
                        print("Stopping all motors.")

                    elif command == "shutdown":
                        print("Shutdown command received. Exiting.")
                        motor_A.off()
                        motor_B.off()
                        motor_C.off()
                        sys.exit(0)

                    else:
                        parts = command.split(':')

                        # --- New Format: MOTOR:DEGREES:SPEED ---
                        if len(parts) == 3:
                            try:
                                motor_id = parts[0].upper()
                                degrees = int(parts[1])
                                speed = int(parts[2])

                                target_motor = None
                                if motor_id == 'A':
                                    target_motor = motor_A
                                elif motor_id == 'B':
                                    target_motor = motor_B
                                elif motor_id == 'C':
                                    target_motor = motor_C
                                else:
                                    print("Unknown motor ID: ", motor_id)
                                    continue

                                if not 1 <= speed <= 100:
                                    print(
                                        "Invalid speed. Must be between 1 and 100.")
                                    continue

                                print("Motor ", motor_id, ": Moving ",
                                      degrees, " degrees at ", speed, "% speed.")

                                target_motor.on_to_degrees(
                                    speed=SpeedPercent(speed),
                                    position=degrees,
                                    brake=True,
                                    block=False
                                )

                            except ValueError:
                                print(
                                    "Invalid format. Degrees/Speed must be numbers.")
                            except Exception as e:
                                print("Error executing command:", e)
                        # --- Stop individual motor (e.g., A:stop) ---
                        elif len(parts) == 2 and parts[1] == "stop":
                            motor_id = parts[0].upper()
                            if motor_id == 'A':
                                motor_A.off()
                                print("Stopping motor A.")
                            elif motor_id == 'B':
                                motor_B.off()
                                print("Stopping motor B.")
                            elif motor_id == 'C':
                                motor_C.off()
                            else:
                                print("Unknown motor ID for stop:", motor_id)

                        # --- Unknown command ---
                        else:
                            print("Unknown command format.")
                            print("Use 'MOTOR:DEGREES:SPEED' (e.g., 'A:90:50')")
                            print("Or 'A:stop', 'B:stop', 'stop_all', 'shutdown'")

    except KeyboardInterrupt:
        print("Server stopped by user (Ctrl+C).")
    finally:
        print("Stopping all motors before exit.")
        motor_A.off()
        motor_B.off()
        motor_C.off()
