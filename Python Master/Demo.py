import serial
import serial.tools.list_ports
from tkinter import *
import tkinter as tk
from tkinter import ttk
from msilib.schema import ComboBox


def Send_Intensity(intensity):
    arduino.write(bytes(intensity, 'utf-8'))
    print("Intesntiy set to {}".format(intensity))


def Set_SerialPort():
    global arduino 
    print("{}".format(comport_combobox.get()[0:4]))
    arduino = serial.Serial(port=comport_combobox.get()[0:4], baudrate=baudrate_combobox.get(), timeout=1)

def Read_COMports():
    port_set = []
    ports = serial.tools.list_ports.comports()
    for port, desc ,hwid in sorted(ports):
        port_set.append("{} ({})".format(port,desc))
        if "Arduino" in desc:
            port_detected = "{} ({})".format(port,desc)
    return port_set, port_detected



def Do_Nothing():
    print("I am doing Nothing")


#Tkinter Window Setting
window = Tk()
window.geometry("330x100")
window.resizable(False,False)
window.title("Solar Tester")

#Menu Setting 
menubar = Menu(window)
fileMenu = Menu(menubar, tearoff=0)
fileMenu.add_command(label="Do nothing", command=Do_Nothing)
menubar.add_cascade(label="File", menu=fileMenu)



#Tkinter Widget setting

#Label
comport_label = Label(text = "COM port : ")
baudrate_label = Label(text = "Baudrate : ")

#Combobox
comport_combobox = ttk.Combobox(window,height=1,width=23,values=Read_COMports()[0])
comport_combobox.set(Read_COMports()[1])
baudrate_combobox = ttk.Combobox(window,height=1,width=23,values=[300,600, 1200, 2400, 4800, 9600, 14400, 19200, 28800, 31250, 38400, 57600,115200])
baudrate_combobox.set(115200)
comport_combobox['state'] = 'readonly'
baudrate_combobox['state'] = 'readonly'
#Button
comport_refresh = Button(window, height = 1,width = 7, text = "Refresh",command=Do_Nothing)
Serial_Start = Button(window, height = 1,width = 7, text = "Start",command=Set_SerialPort)

#SlideBard (Scale)
lamp_Scale = Scale(window, from_=0, to=100,length = 320,orient=HORIZONTAL, command=Send_Intensity)

#Grid Widgets
comport_label.grid(row=0,column=0)
comport_combobox.grid(row=0,column=1)
comport_refresh.grid(row=0,column=2)

baudrate_label.grid(row=1,column=0)
baudrate_combobox.grid(row=1,column=1)
Serial_Start.grid(row=1,column=2)

lamp_Scale.grid(row=2,column=0,columnspan=4)

window.config(menu=menubar)
mainloop()
