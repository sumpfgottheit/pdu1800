# -*- coding: utf-8 -*-
__author__ = 'saf'

import socket
import ctypes
import functools
from ctypes import c_int32, c_float, c_bool, c_char, c_uint32, c_ubyte
import re
import codecs
from config import TIMEOUT_IN_SECONDS, BUFFER_SIZE, IP
import select
import time
import threading

LUT_FIELDNAMES_TO_UNDERSCORE={}

AC_SERVER_PORT=9996
AC_SERVER_IP="192.168.31.225"

OPERATION_HANDSHAKE=0
OPERATION_SUBSCRIBE_UPDATE=1
OPERATION_SUBSCRIBE_SPOT=2
OPERATION_DISMISS=3

#
# Utility Functions
#
def convert_to_lowercase_and_underscore(name):
    """
    The Shared Memory is in CamelCase - convert the names to Python Standard lowercase with underscores
    http://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-camel-case

    I have already changed the names in sim_info.py, so this function is no longer used
    """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def struct_to_hash(s):
    """
    Convert the given struct to a python hash
    Args:
        struct: The sim_info-scruct

    Returns: The struct as hash. The fieldnames are converted to lowercase/underscore
    """
    h = {}
    d = [(field, getattr(s, field)) for field in [f[0] for f in s._fields_]]
    for field, value in d:
        if field not in LUT_FIELDNAMES_TO_UNDERSCORE:
            LUT_FIELDNAMES_TO_UNDERSCORE[field] = convert_to_lowercase_and_underscore(field)
        field_name = LUT_FIELDNAMES_TO_UNDERSCORE[field]
        if not isinstance(value, (str, float, int)):
            value = list(value)
        h[field_name] = value
    return h

# Character Encoding...
def add_string_properties_from_utf_16_le(c):
    """
    c_ubyte arrays that start with '_' are automatically converted to a string attribute
    with the name of the field without the leading '_'. The content of the original
    Bytarray is decoded using UTF-16-LE.
    :param c: Class to add the properties to
    :return: Nothing
    """
    for field_name, field_type in c._fields_:
        if field_type._type_ == ctypes.c_ubyte and field_type._length_ > 1 and field_name.startswith('_'):
            field = field_name[1:]
            def getter(self, name=None):
                value = getattr(self, "_%s" % name)
                return codecs.decode(value, 'UTF-16-LE', 'replace').split('%')[0]
            setattr(c, field, property(functools.partial(getter, name=field)))

#
# C-Structs from the AC UDP Server
#
class Handshaker(ctypes.LittleEndianStructure):
    _fields_ = [
        ('identifier', c_int32),
        ('version', c_int32),
        ('operationId', c_int32),
    ]

class HandshakerResponse(ctypes.LittleEndianStructure):
    _fields_ = [
        ('_car_name', c_ubyte * 100),        # Windows' wchar_t is UTF16LE. We save the bytes as is and convert them explicitely
        ('_driver_name', c_ubyte * 100),     # The content is wchar_t * 50, which is 16bit * 50 which comes to 8bit (Byte) * 100
        ('identifier', c_uint32),
        ('version', c_uint32),
        ('_track_name', c_ubyte * 100),
        ('_track_config', c_ubyte * 100),
    ]

class RTCarInfo(ctypes.LittleEndianStructure):
    _fields_ = [
        ('identifier', c_char),
        ('size', c_int32),
        ('speed_Kmh', c_float),
        ('speed_Mph', c_float),
        ('speed_Ms', c_float),
        ('isAbsEnabled', c_bool),
        ('isAbsInAction', c_bool),
        ('isTcInAction', c_bool),
        ('isTcEnabled', c_bool),
        ('isInPit', c_bool),
        ('isEngineLimiterOn', c_bool),
        ('accG_vertical', c_float),
        ('accG_horizontal', c_float),
        ('accG_frontal', c_float),
        ('lapTime', c_int32),
        ('lastLap', c_int32),
        ('bestLap', c_int32),
        ('lapCount', c_int32),
        ('gas', c_float),
        ('brake', c_float),
        ('clutch', c_float),
        ('engineRPM', c_float),
        ('steer', c_float),
        ('gear', c_int32),
        ('cgHeight', c_float),
        ('wheelAngularSpeed', c_float * 4),
        ('slipAngle', c_float * 4),
        ('slipAngle_ContactPatch', c_float * 4),
        ('slipRatio', c_float * 4),
        ('tyreSlip', c_float * 4),
        ('ndSlip', c_float * 4),
        ('load', c_float * 4),
        ('Dy', c_float * 4),
        ('Mz', c_float * 4),
        ('tyreDirtyLevel', c_float * 4),
        ('camberRAD', c_float * 4),
        ('tyreRadius', c_float * 4),
        ('tyreLoadedRadius', c_float * 4),
        ('suspensionHeight', c_float * 4),
        ('carPositionNormalized', c_float),
        ('carSlope', c_float),
        ('carCoordinates', c_float * 3),
    ]


class RTLap(ctypes.LittleEndianStructure):
    _fields_ = [
        ('carIdentifierNumber', c_int32),
        ('lap', c_int32),
        ('_driverName', c_ubyte * 100),
        ('_carName', c_ubyte * 100),
        ('time', c_int32),
    ]
#
# Fix Character Encoding where needed
#
add_string_properties_from_utf_16_le(HandshakerResponse)
add_string_properties_from_utf_16_le(RTLap)
HANDSHAKER_RESPONSE_SIZE = ctypes.sizeof(HandshakerResponse)
RTLAP_SIZE = ctypes.sizeof(RTLap)
RTCARINFO_SIZE = ctypes.sizeof(RTCarInfo)

class ACTelemetryReader(threading.Thread):
    def __init__(self, local_ip, ac_server_ip, ac_server_port=9996):
        super(ACTelemetryReader, self).__init__()
        self.ac_server_ip = ac_server_ip
        self.ac_server_port = ac_server_port
        self.ac_server = (self.ac_server_ip, self.ac_server_port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((local_ip, 0))
        self.buffer = bytearray(BUFFER_SIZE)
        self.rt_car_info = {}
        self.running = False
        self.is_initialized = False
        self.is_subcribed = False

    def send_to_ac_server(self, msg):
        self.socket.sendto(msg, self.ac_server)

    def initialize_connection(self):
        msg = Handshaker(identifier=0, version=0, operationId=OPERATION_HANDSHAKE)
        self.send_to_ac_server(msg)
        nbytes = self.socket.recv_into(self.buffer, BUFFER_SIZE)
        r = HandshakerResponse.from_buffer_copy(self.buffer)
        assert r.identifier == 4242
        self.is_initialized = True

    def subscribe(self, update=True, spot=False):
        if update:
            msg = Handshaker(identifier=0, version=0, operationId=OPERATION_SUBSCRIBE_UPDATE)
            self.send_to_ac_server(msg)
        if spot:
            msg = Handshaker(identifier=0, version=0, operationId=OPERATION_SUBSCRIBE_SPOT)
            self.send_to_ac_server(msg)
        self.is_subcribed = True

    def disconnect(self):
        if self.socket is not None:
            msg = Handshaker(identifier=0, version=0, operationId=OPERATION_DISMISS)
            self.send_to_ac_server(msg)
            self.socket.close()
            self.socket = None

    def run(self):
        if not self.is_initialized:
            self.initialize_connection()
        if not self.is_subcribed:
            self.subscribe(update=True)
        self.running = True
        while self.running:
            ready = select.select([self.socket], [], [], TIMEOUT_IN_SECONDS)
            if ready[0]:
                nbytes = self.socket.recv_into(self.buffer, BUFFER_SIZE)
                if nbytes == RTCARINFO_SIZE:
                    rt_car_info = RTCarInfo.from_buffer_copy(self.buffer)
                    self.rt_car_info = struct_to_hash(rt_car_info)
                elif nbytes == RTLAP_SIZE:
                    pass
                else:
                    pass
        self.disconnect()

    def __del__(self):
        self.disconnect()

if __name__=='__main__':
    r = ACTelemetryReader(IP, AC_SERVER_IP)
    r.start()
    time.sleep(3)
    print r.rt_car_info
    r.running = False
    r.join()

