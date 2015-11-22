#!/usr/bin/env python

import pickle 
from util import get_lan_ip
from pprint import pprint
import socket

LOCAL_IP = get_lan_ip()
PORT = 18877
BUF_SIZE = 4096

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((LOCAL_IP, PORT))

while True:
    data = sock.recv(BUF_SIZE)  # Recieve from udp
    data = pickle.loads(data)   # unpickle the data
    max_key_length = max([len(k) for k in data.keys()])
    for key, value in data.items():
        print "%s : %s" % ( key.ljust(max_key_length), value)
    print
