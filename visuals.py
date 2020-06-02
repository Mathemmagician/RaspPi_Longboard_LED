
''' LONGBOARD

  130 BMR BML 131
       ___
   []-|   |-[]
     _| x |_ <-0
    |  BACK | 6
    |       |     x  is where setup is located
    |       |
  95|       | 24
    |       |
    |       |
    |_FRONT_| 42
      |   |
   []-|___|-[]
  60 FMR FML 59
'''


def forward_pulse(w=20, start=FML, delta=4):
    'sends pulses from the given point to opposite'
    try:
        pixels.fill(BLUE)
        for i in range(w):
            pixels[(start+1 + i + forward_pulse.state) % num_pixels] = GREEN
            pixels[(start   - i - forward_pulse.state) % num_pixels] = GREEN
        forward_pulse.state = (forward_pulse.state + delta) % (halfnum_pixels-w//2)
    except AttributeError:
        forward_pulse.state = 0


def forward_beat(w=5, start=FML, delta=1):
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
    'right -> postivie delta, left -> negative delta'
    try:
        pixels.fill((200, 40, 0))
        for i in range(w):
            for j in range((i + turning.state) % (4 * w), num_pixels, 4 * w):
                pixels[j] = color
        turning.state += delta
    except AttributeError:
        turning.state = 0


def sideLight(side='right', delta=1):
    try:
        pixels.fill((0,0,0))

        
        sideLight.state += delta
    except AttributeError:
        sideLight.state = 0


def random_bright_color():
    return (randint(35, 255), randint(35, 255), randint(35, 255))


def disco(w=5):
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
    'Smart people use HSV for ranbow'
    try:
        color = hsv2rgb(rainbow.time/360, 1, 1)
        pixels.fill(color)

        rainbow.time = (rainbow.time + 2) % 360
    except AttributeError:
        rainbow.time = 0
