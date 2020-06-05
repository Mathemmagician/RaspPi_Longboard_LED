import time
from random import randint
from math import sin, cos, pi, radians
import colorsys

from Adafruit_BNO055 import BNO055

import board
import neopixel         # LEDs
from constants import * # numpixels, Colors, FML, FMR, BMR, BML, etc.

import pigpio
import ir_hasher            # Remote Controller
from hash2key import hash2key  # Remote Signal Map

''' LONGBOARD

  130 BMR BML 131
       ___
   []-|   |-[]
     _| x |_ <-0
    |  BACK | 6
    |       |     x  is where setup is locate
midR|       |
  95|       | 24 midL
    |       |
    |       |
    |_FRONT_| 42
      |   |
   []-|___|-[]
  60 FMR FML 59
'''


def forward_pulse(w=20, start=FML, delta=3, color1=BLUE, color2=GREEN):
    global pixels
    'sends pulses from the given point to opposite'
    try:
        pixels.fill(color1)
        for i in range(w):
            pixels[(start+1 + i + forward_pulse.state) % num_pixels] = color2
            pixels[(start   - i - forward_pulse.state) % num_pixels] = color2
        forward_pulse.state = (forward_pulse.state + delta) % (halfnum_pixels-w//2)
    except AttributeError:
        forward_pulse.state = 0


def forward_beat(w=5, start=FML, delta=1):
    global pixels
    'sends beats from the given point to opposite'
    try:
        pixels.fill((255, 255, 0))
        for k in range(forward_beat.state, halfnum_pixels, 3 * w):
            for i in range(w):
                pixels[(start+1 + i + k) % num_pixels] = (0, 50, 100)
                pixels[(start   - i - k) % num_pixels] = (0, 50, 100) 

        forward_beat.state = (forward_beat.state + delta) % (3 * w)
    except AttributeError:
        forward_beat.state = 0


def turning(w=4, delta=3, color=(128, 0, 128)):
    global pixels
    'right -> postivie delta, left -> negative delta'
    try:
        pixels.fill((200, 40, 0))
        for i in range(w):
            for j in range((i + turning.state) % (4 * w), num_pixels, 4 * w):
                pixels[j] = color
        turning.state += delta
    except AttributeError:
        turning.state = 0


def sideLight(side='right', delta=3):
    global pixels
    try:
        pixels.fill((0,0,0))
        center = midR if side=='right' else midL

        for i in range(center-sideLight.state, center+sideLight.state):
            pixels[i] = YELLOW
        #pixels[center-sideLight.state, center+sideLight.state] = [YELLOW] * (2 * sideLight.state)
        
        sideLight.state += delta
        sideLight.state %= 30
    except AttributeError:
        sideLight.state = 0


def random_bright_color():
    return (randint(35, 255), randint(35, 255), randint(35, 255))


def disco(w=5):
    global pixels
    try:
        pixels.fill(BLACK)
        for i in range(disco.start, num_pixels, w):
            pixels[i] = disco.color

        disco.color = random_bright_color()
        disco.counter += 1
        disco.start = (disco.start + disco.delta) % w
        if disco.counter == 15:
            disco.counter = 0
            disco.delta = -disco.delta
    except AttributeError:
        disco.color = random_bright_color()
        disco.start = 0
        disco.counter = 0
        disco.delta = 1


def hsv2rgb(h,s,v):
    'return non-normalized hsv to rgb conversion'
    return tuple(round(i * 255) for i in colorsys.hsv_to_rgb(h,s,v))


def rainbow():
    global pixels
    'Smart people use HSV for ranbow'
    try:
        color = hsv2rgb(rainbow.time/360, 1, 1)
        pixels.fill(color)

        rainbow.time = (rainbow.time + 2) % 360
    except AttributeError:
        rainbow.time = 0

def cruising():
    global CRUISING
    CRUISING = not CRUISING
    print(CRUISING)



def callback(hash):
    'This function is called when IR remote sends a signal'
    global boardfunc, funckwargs
    if hash not in hash2key:
        print(f'Unrecognized hash: {hash}')
    else:
        key = hash2key[hash]
        if key == 'KEY_5':
            cruising()
        print(f'{hash2key[hash]} was pressed')
        if key in key_functionality:
            boardfunc, funckwargs = key_functionality[key]


# Raspberry Pi configuration with serial UART and RST connected to GPIO 18:
print("Setting up BNO055")
bno = BNO055(serial_port='/dev/serial0', rst=18)
if not bno.begin():
    raise RuntimeError('Failed to initialize BNO055! Is the sensor connected?')

pixel_pin = board.D12  # NeoPixels connected to BCM 12 pin -- WAS CHANGED FROM 18 TO 12
ORDER = neopixel.GRB

import os
print("Running `sudo pigpiod` to enable IR communcation")
os.system("sudo pigpiod")

print("Initializing Controller")
# Instantiate Remote controller
pi = pigpio.pi()
ir = ir_hasher.hasher(pi, 17, callback, 5)


print("Initializing NeoPixels")
with neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.4, auto_write=False, pixel_order=ORDER) as pixels:


    key_functionality = {
            'UP':       (forward_pulse, {}),
            'DOWN':     (forward_pulse, {'start': BML}),
            'LEFT':     (forward_pulse, {'start': 24}),
            'RIGHT':    (forward_pulse, {'start': 95}),
            'KEY_7':    (turning, {'delta': -3}),
            'KEY_9':    (turning, {'delta': +3}),
            'KEY_1':    (rainbow, {}),
            'KEY_2':    (disco, {}),
            'KEY_3':    (forward_beat, {})
    }

    
    TESTING = False
    CRUISING = False

    boardfunc = forward_pulse
    funckwargs = {}

    heading, roll, pitch = bno.read_euler() # Euler angles in degrees
    EMA = heading # Exponential Moving Average
    EMA_alpha = 0.05

    filenum = 1
    while os.path.exists(f"trip_{filenum:03}.csv"):
        filenum += 1

    print(f"writing data to `trip_{filenum:03}.csv`")
    tripfile = open(f"trip_{filenum:03}.csv", "w")

    print("Beginning the loop")
    try:
        while True:
            heading, roll, pitch = bno.read_euler() # Euler angles in degrees
            sys, gyro, accel, mag = bno.get_calibration_status() # Read Calibration Status. 0-poor, 3-perfect
            #print('Heading={0:0.2F} Roll={1:0.2F} Pitch={2:0.2F}\tSys_cal={3} Gyro_cal={4} \
            #        Accel_cal={5} Mag_cal={6}'.format(heading, roll, pitch, sys, gyro, accel, mag))

            data = f"{heading:0.02f},{EMA:0.02f},{roll:0.02f},{pitch:0.02f},{sys},{gyro},{accel},{mag}"

            #print(data)
            tripfile.write(data+"\n")

            
            if abs(EMA - heading) < 180:
                shortArcHeading = heading
            else:
                if heading > 180:
                    shortArcHeading = (heading - 360)
                else:
                    shortArcHeading = (heading + 360)
            EMA = ((1 - EMA_alpha) * EMA + EMA_alpha * shortArcHeading) % 360
            
            if TESTING:
                pixels.fill(BLUE)
                pixels[(FML + int(heading/360 * num_pixels)) % num_pixels] = (0, 255, 0)
            elif CRUISING:
                if EMA - shortArcHeading > 7: # More than 1 degree inclination
                    #print("LEFT")
                    sideLight("left")
                elif EMA - shortArcHeading < -7:
                    #print("RIGHT")
                    sideLight()
                else:
                    #print("STRAIGHT")
                    #pixels.fill(YELLOW)
                    forward_pulse(color1=BLACK, color2=YELLOW)
                    
            else:
                if funckwargs: # makes sure kwargs list isn't empty
                    boardfunc(**funckwargs)
                else:
                    boardfunc()

            pixels.show()



    except KeyboardInterrupt:
        print('Keyboard Interrupted. Cleaning Up')
        # Clean Up here
    finally:
        tripfile.close()
        print("Final Commands")

