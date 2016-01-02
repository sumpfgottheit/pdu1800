# -*- coding: utf-8 -*-
__author__ = 'saf'

from collections import namedtuple
import time
import timeit
import socket
import select
from constants import *
from config import *
import pickle
import random
from datetime import datetime
import json
from telemetry_reader import ACTelemetryReader
from pprint import pformat

SimDataPacket = namedtuple('SimDataPacketBase', ['version', GEAR, RPM, SPEED, MAX_RPM, NUM_CARS, POS, NUM_LAPS, LAPS_COMPLETED,
                                                 CURRENT_TIME, LAST_TIME, BEST_TIME])

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
        self.packet_id = 0
        self.pos = 1
        self.num_cars = 2
        self.num_laps = 98
        self.laps_completed = 0
        self.last_time = self.current_time = self.best_time = 0
        self.t = datetime.now()

    def times2delta(self, a, b):
        return (a - b).total_seconds()

    @property
    def packet(self):
        self.packet_id += 1
        if self.packet_id % 200 == 0:
            self.pos = 2 if self.pos == 1 else 1
        if self.packet_id % 300 == 0:
            self.num_cars = random.randint(1,4)
        self.current_time = self.times2delta(self.t, datetime.now())
        if self.packet_id % 400 == 0:
            self.laps_completed += 1
            self.last_time = self.current_time
            self.t = datetime.now()
            if self.last_time < self.best_time:
                self.best_time = self.last_time
        self.speed = int(self.MAX_SPEED * ((self.rpm + (self.gear * self.MAX_RPM)) / self. MAX_RPM_GEAR))
        return SimDataPacket(self.VERSION, self.gear, self.rpm, self.speed, self.MAX_RPM, self.num_cars, self.pos, self.num_laps, self.laps_completed,
                             self.current_time, self.last_time, self.best_time)

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

class PDU1800DataStream(BaseDataStream):
    def __init__(self, ip, port):
        super(PDU1800DataStream, self).__init__()
        self.port = port
        self.local_ip = ip
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking(0)
        self.sock.bind((self.local_ip, self.port))
        self.ac_server_ip = None
        self.telemetry_reader = None

    @property
    def has_data_available(self):
        ready = select.select([self.sock], [], [], TIMEOUT_IN_SECONDS)
        return ready[0]

    @property
    def packet(self):
        if self.ac_server_ip is None:
            _d, _address = self.sock.recvfrom(BUFFER_SIZE)  # Recieve from udp
            self.ac_server_ip = _address[0]
            self.telemetry_reader = ACTelemetryReader(self.local_ip, self.ac_server_ip)
            self.telemetry_reader.start()
        else:
            _d = self.sock.recv(BUFFER_SIZE)  # Recieve from udp
        packet = pickle.loads(_d)   # unpickle the data
        if self.telemetry_reader is not None:
            packet['rt_car_info'] = self.telemetry_reader.rt_car_info
        return packet

    def quit(self):
        if self.telemetry_reader:
            self.telemetry_reader.running = False
            self.telemetry_reader.join(2.0) # Wait 2 seconds

class PDU1800DatasStreamRepeater(BaseDataStream):
    def __init__(self, skip_packets = 0):
        with open('pdu1800_datastream.json') as f:
            self.stream = json.load(f)
        self.t = 0
        self.stream_iterator = iter(self.stream)
        self.next_t, self.next_packet = self.stream_iterator.next()
        while self.next_packet['physics']['speed_kmh'] < 1.0:
            self.next_t, self.next_packet = self.stream_iterator.next()
        for i in range(skip_packets):
            self.next_t, self.next_packet = self.stream_iterator.next()
        self.ts = time.clock()


    @property
    def has_data_available(self):
        #elapsed_since_last_visit = time.clock() - self.ts
        #t = abs(self.next_t - elapsed_since_last_visit)
        #self.ts = time.clock()
        #time.sleep(min(t, 0.2))
        return True

    @property
    def packet(self):
        packet = self.next_packet
        self.next_t, self.next_packet = self.stream_iterator.next()
        return packet

if __name__== '__main__':
    #stream = MockBaseDataStream()
    #while True:
    #    if stream.has_data_available:
    #        packet = stream.packet
    #        print( packet)
    datastream = PDU1800DataStream(IP, UDP_PORT)
    l = []
    t = timeit.default_timer()
    record = False
    try:
        while True:
            if datastream.has_data_available:
                d = datastream.packet
                now = timeit.default_timer()
                delta_t = now - t

                if not record:
                    if d['physics']['speed_kmh'] > 1.0:
                        record = True
                    else:
                        continue
                l.append((delta_t, d))
                t = now
    except KeyboardInterrupt:
        if len(l) > 0:
            print "Writing File"
            with open('pdu1800_datastream.json', 'w') as f:
                f.write(json.dumps(l, indent=2))
    print "Quiting Datastream"
    datastream.quit()






