#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 14 14:01:00 2021

@author: benjaminmodlin
"""
import dill # if dill is not recognized, run "pip install dill" in your console
import tkinter
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

#edit name here (can just manually change it if you want)
filenameToOpen = input("put in the name you want to open: ")


filenameToOpenExt = filenameToOpen + ".pkl"

dataObject = None

with open(filenameToOpenExt, 'rb') as input:
    dataObject = dill.load(input)


# comment out what you don't need below

#print(dataObject.voltageValues) # prints the voltage array of the data you stored
#print(dataObject.stepsValues) # prints the steps array of the data you stored


#dataObject.createGraph() # re-creates the graph of the fourier transform/raw data