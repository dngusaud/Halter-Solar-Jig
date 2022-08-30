# Importing Libraries

from argparse import ArgumentDefaultsHelpFormatter
from asyncore import write
from curses import baudrate
from math import comb
from sqlite3 import Row
import serial
import time

import tkinter as tk
from tkinter import ttk
from tkinter import *



def write_to_serial(value):
    arduino.write(bytes(value, 'utf-8'))
    print("value {} has sent!!".format(value))


def setup_serial(device,baudrate):
    global arduino
    print("{} is connected!!".format(device))
    arduino = serial.Serial(port=device, baudrate=baudrate, timeout=.1)


def set_intensity(value):
    write_to_serial(value)


def main():
    #------------------Widget Setting Start-----------------#
    #Window setting
    window = Tk()
    window.geometry("340x180")
    window.resizable(False,False)
    window.title("Collar Hardware Tester")

    #label
    label_port = Label(text = "Port : ")
    label_baudrate = Label(text = "Baud rate : ")
    label_voltage = Label(text = "Voltage : {}mV".format(100))
    label_current = Label(text = "Current : {}mA".format(100))
    label_power = Label(text =   "Power   : {}mW".format(100))


    #Combobox
    combobox_comport = ttk.Combobox(window)
    combobox_comport['values'] = ('/dev/ttyACM0')
    combobox_comport.set('/dev/ttyACM0')
    combobox_baudrate = ttk.Combobox(window)
    combobox_baudrate['values'] = ('9600','19200','115200')
    combobox_baudrate.set('115200')

    #Button
    button_refresh = Button(window, height=1, width=7, text="Refresh")
    button_connect = Button(window, height=1, width=7, text="Connect")

    #Slidebar 
    scale_intensity = Scale(window, from_=0, to=100,length=320, orient=HORIZONTAL, command=set_intensity)

    #WGriding
    label_port.grid(row=0,column=0)
    combobox_comport.grid(row=0,column=1)
    button_refresh.grid(row=0,column=2)

    label_baudrate.grid(row=1,column=0)
    combobox_baudrate.grid(row=1,column=1)
    button_connect.grid(row=1,column=2)

    scale_intensity.grid(row=2,column=0,columnspan=4)

    label_voltage.grid(row=3,column=0,columnspan=4)
    label_current.grid(row=4,column=0,columnspan=4)
    label_power.grid(row=5,column=0,columnspan=4)


    #------------------Widget Setting End------------------#

    #------------------Functional Code Start------------------#
    setup_serial(combobox_comport.get(),combobox_baudrate.get())


    window.mainloop()
    #------------------Functional Code End------------------#



if __name__ == "__main__":
    main()


#arduino = serial.Serial(port='/dev/ttyACM0', baudrate=115200, timeout=.1)
#
#def write_read(x):
#    arduino.write(bytes(x, 'utf-8'))
#    time.sleep(0.05)
#    data = arduino.readline()
#    return data
#
#while True:
#    num = input("Enter a number: ") # Taking input from user
#    value = write_read(num)
#    print(value) # printing the value

