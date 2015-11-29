__author__ = 'Florian'
from util import get_lan_ip
#################
# CONFIGURATION #
#################


# CHANGE FROM HERE
#

UDP_PORT = 18877
IP = get_lan_ip()
BUF_SIZE = 4096
TIMEOUT_IN_SECONDS = 0.1

#
SCREEN_WIDTH = 320
SCREEN_HEIGHT = 240
SCREEN_DEEP = 32

#
LABEL_RIGHT = 0
LABEL_LEFT = 1

ALIGN_CENTER = 0
ALIGN_RIGHT = 1
ALIGN_LEFT = 2
VALIGN_CENTER = 0
VALIGN_TOP = 1
VALIGN_BOTTOM = 2

#
# Stop changing. Of course - you can do, but it should not be necessary
#
FONT = 'assets/DroidSansMono.ttf'
# set up the colors
BLACK =  (  0,   0,   0)
WHITE =  (255, 255, 255)
RED   =  (255,   0,   0)
GREEN =  (  0, 255,   0)
BLUE  =  (  0,   0, 255)
CYAN  =  (  0, 255, 255)
MAGENTA= (255,   0, 255)
YELLOW = (255, 255,   0)
RPM_YELLOW = (230, 230,   40)
GREY   = (214, 214, 214)

BACKGROUND_COLOR = BLACK
FOREGROUND_COLOR = WHITE
#
#
#

import os, sys
if sys.platform == 'darwin':
    # Display on Laptop Screen on the left
    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (-400,100)
    from datastream import MockBaseDataStream
    datastream = MockBaseDataStream()
    #from datastream import PDU1800DataStream
    #datastream = PDU1800DataStream(ip=IP, port=UDP_PORT)
elif sys.platform.startswith('linux'):
    if os.path.isfile('/etc/pointercal'):
        os.environ["TSLIB_CALIBFILE"] = '/etc/pointercal'
    os.putenv('SDL_VIDEODRIVER', 'fbcon')
    os.putenv('SDL_FBDEV'      , '/dev/fb1')
    os.putenv('SDL_MOUSEDRV'   , 'TSLIB')
    os.putenv('SDL_MOUSEDEV'   , '/dev/input/touchscreen')
    from evdev import InputDevice, list_devices

    devices = map(InputDevice, list_devices())
    eventX=""
    for dev in devices:
        if dev.name == "ADS7846 Touchscreen":
            eventX = dev.fn

    os.environ["SDL_MOUSEDEV"] = eventX
    from datastream import PDU1800DataStream
    datastream = PDU1800DataStream(ip=IP, port=UDP_PORT)
#
