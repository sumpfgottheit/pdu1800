# PDU1800 - Raspberry PI Dashboard Display for Assetto Corsa

The PDU1800 ist the *PI Display Unit 1800* for [Assetto Corsa](http://www.assettocorsa.net/), a tremendous Race Simulation from [Kunos](http://www.kunos-simulazioni.com/). It acts as a dashboard using the  [Watterott RPi Touch-Display](https://github.com/watterott/RPi-Display).

## Pictues say more than words

![alt tag](https://raw.github.com/sumpfgottheit/pdu1800/master/doc/screen1.png)

![alt tag](https://raw.github.com/sumpfgottheit/pdu1800/master/doc/screen2.jpg)

I published two videos, that will show you how it works on the pi. I will publish another one once I have installed it on my wheel:
* Youtube: [Ingame (LaFerrari at Spielberg South)](https://youtu.be/xYxKDCZYCDI)
* Youtube: [Simulation 1](https://www.youtube.com/watch?v=lXocxouxeA8)
* Youtube: [Simulation 2](https://www.youtube.com/watch?v=2IsrtLMVFcg)

## Description what you see

![alt tag](https://raw.github.com/sumpfgottheit/pdu1800/master/doc/display_widget_description.png)

Note, that it is necessary to use shared memory, the API and the UDP Server, to get all the data, that I want to show on the display.

## Why do we need the N-th Assetto Corsa Dashboard?

If you look into the Assetto Corsa Forums, you will find awesome dashboards, as ingame app, for smartphones, browsers or to build your cockpit using Arduino hardware. Honestly, there is no need for another dashboard. I am more interested in the act of creating something new. I've never done a Game Plugin and, although I use Python at work daily, I've never done anything graphical with pygame or interfaced with C-programs directly. So the technical challenge was also interesting for me.

I actually spend far more hours in Assetto Corsa programming my PDU1800 than driving, which may be the reason I always see this funny blue flags while racing....

## Installation

The PDU1800 consists of two components:

* The Raspberry Pi Display
* The [PDU1800 Data Provider](https://github.com/sumpfgottheit/pdu1800_data_provider) which is a standard Assetto Corsa Plugin 

See the [Wiki](https://github.com/sumpfgottheit/pdu1800/wiki) for installation instructions for the PDU1800 on the Raspberry and the Readme of the [PDU1800 Data Provider](https://github.com/sumpfgottheit/pdu1800_data_provider).

## Usage Hints

If you exit a driving session and let the dashboard run, the UDP Telemetry Reader needs to be reinitialized. Just touch the display a click on "Restart". This will reinitialize the Telemetry Reader and the fuel calculation.

## Technical Overview

The [PDU1800 Data Provider](https://github.com/sumpfgottheit/pdu1800_data_provider) is a Assetto Corsa Python Plugin. It collects the necessary data using [Rombiks siminfo.py](http://www.assettocorsa.net/forum/index.php?threads/shared-memory-for-python-applications-sim_info-py-for-ac-v0-22.11382/) and the PythonAPI for the Delta Time. All data is collected, converted into a hash, pickled and sent to the Pi with UDP. The data provider can show a debug window with the current collected data. 

The PDU1800 is also written in Python (2.7) and pygame. I extracts the data, hands it over to a specific widget (eg the LapTimeWidget) which takes care of displaying the data. The touchscreen shows the current IP of the Pi - necessary to configure the data provider - and can be used to quit the application of the shutdown the whole pi.

## Simulation on PC or Mac

The PDU1800 has been developed on a Mac and been tested on a PC - no need for a Pi. To develop, just install a python 2.7 interpreter with pygame. If you just start the `main.py`, you should be presented with a working PDU1800 on the screen, which uses a collected datastream `pdu1800_datastream.json`. If you want to collect your own datastream, just set the `raspberry_ip` in the `pdu1800_data_provider/config.ini` to the ip of your PC/Mac and start the `datastream.py` which will create a new `pdu1800_datastream.json`. 

It's all python, so adapt it if necessary.


