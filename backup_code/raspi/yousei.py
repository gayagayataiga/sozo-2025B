import gpiozero
from ik_2 import invers_kinematics
from gpiozero import AngularServo
from gpiozero.pins.pigpio import PiGPIOFactory

from time import sleep
import curses


def main(stdscr):


factory = PiGPIOFactory()

servo1 = AngularServo(
    22,
    min_angle=0,
    max_angle=180,
    min_pulse_width=0.0004,
    max_pulse_width=0.0024,
    pin_factory=factory
)

servo2 = AngularServo(
    24,
    min_angle=0,
    max_angle=180,
    min_pulse_width=0.0004,
    max_pulse_width=0.0024,
    pin_factory=factory
)

curses.cbreak()
stdscr.nodelay(True)
stdscr.keypad(True)


L1 = 190
L2 = 30
L3 = 160
L4 = 40
L5 = 170
x = 200
y = 0
theta1, theta2 = invers_kinematics(x, y, L1, L2, L3, L4, L5)

# servo1.angle = theta1
# servo2.angle = 180-theta2

step = 5
dt = 0.02

while True:
ch = stdscr.getch()
if ch != -1:
if ch == ord('q'):
break
elif ch == curses.KEY_LEFT:
x = max(0, x - step)
elif ch == curses.KEY_RIGHT:
x = min(300, x + step)
elif ch == curses.KEY_UP:
y = min(300, y + step)
elif ch == curses.KEY_DOWN:
y = max(0, y - step)

theta1, theta2 = invers_kinematics(x, y, L1, L2, L3, L4, L5)

servo1.angle = theta1 + 15
servo2.angle = 180 - theta2

stdscr.addstr(0, 0, f"theta1, theta2, x, y : {theta1}, {theta2}, {x}, {y} ")

stdscr.refresh()
sleep(dt)

curses.wrapper(main)
