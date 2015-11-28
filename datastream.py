# -*- coding: utf-8 -*-
__author__ = 'saf'

from collections import namedtuple
import time
from constants import *


SimDataPacket = namedtuple('SimDataPacketBase', ['version', GEAR, RPM, SPEED, MAX_RPM])

class SimulatedCar(object):
    VERSION=1
    MAX_RPM=11000
    MIN_RPM=1700
    MAX_GEAR=6
    MIN_GEAR=0
    MAX_THROTTLE_RPMS_DELTA=100
    MAX_SPEED=350
    MAX_RPM_GEAR = float(MAX_RPM * MAX_GEAR)


    def __init__(self):
        self.gear = self.MIN_GEAR
        self.rpm = self.MIN_RPM
        self.speed = 0

    @property
    def packet(self):
        self.speed = int(self.MAX_SPEED * ((self.rpm + (self.gear * self.MAX_RPM)) / self. MAX_RPM_GEAR))
        return SimDataPacket(self.VERSION, self.gear, self.rpm, self.speed, self.MAX_RPM)

    def accelerate(self, percent=100):
        if self.gear == self.MIN_GEAR:
            self.gear = 1
        self.rpm += percent
        if self.rpm > self.MAX_RPM:     # Hochschalten
            self.gear += 1
            self.rpm = self.MIN_RPM + 1
        elif self.rpm < self.MIN_RPM:   # Runterschalten
            self.gear -= 1
            self.rpm = self.MAX_RPM - 1

        if self.rpm > self.MAX_RPM:     # Check rpm within correct range
            self.rpm = self.MAX_RPM
        elif self.rpm < self.MIN_RPM:
            self.rpm = self.MIN_RPM

        if self.gear > self.MAX_GEAR:   # check gear within correct range
            self.gear = self.MAX_GEAR
        elif self.gear < self.MIN_GEAR:
            self.gear = self.MIN_GEAR

        return self.packet

    def brake(self, percent=100):
        return self.accelerate(-percent)

    @property
    def stopped(self):
        return self.gear == self.MIN_GEAR

    @property
    def topspeed(self):
        return self.speed >= self.MAX_SPEED


class BaseDataStream(object):

    def has_data_available(self):
        pass

    @property
    def packet(self):
        pass

class MockBaseDataStream(BaseDataStream):
    def __init__(self):
        super(MockBaseDataStream, self).__init__()
        self.car = SimulatedCar()
        self.accelerating = False
        self.t = time.time() - 1
        self.hz = 1.0/100

    @property
    def has_data_available(self):
        now = time.time()
        if (now - self.t) > self.hz:
            self.t = now
            return True
        return False

    @property
    def packet(self):
        if self.car.stopped:
            self.accelerating = True
        elif self.car.topspeed:
            self.accelerating = False
        if self.accelerating:
            self.car.accelerate()
        else:
            self.car.brake()

        return self.car.packet

if __name__== '__main__':
    stream = MockBaseDataStream()
    while True:
        if stream.has_data_available:
            packet = stream.packet
            print packet





