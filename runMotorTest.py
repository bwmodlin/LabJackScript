import u3
import time
import numpy as np
import dill

import matplotlib.pyplot as plt
import matplotlib.widgets as widgets

import tkinter
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

# This code will always run first. Use it to start trials/tests, etc
def main():
    # running a real test
    runTest() 
    
    # running a fake test
    #analyzeData(None, True, True)
    # this call is used to test the analyze class. Just using the fake data arrays
        
        
# this class runs the test
class runTest:
    # CONSTANTS
    AIN0_ADDRESS = 0 # address for voltage register
    DAC0_ADDRESS = 5000 # address for (human input) motor trigger register
    AIN1_ADDRESS = 4 # address for (computer output) motor trigger register
    MOTOR_VOLTAGE = 5 # voltage for 'on' with triggers. Do not change unless you know what you're doing.
    
    # initializing some variables
    ourU3 = None # our u3 object (labjack itself)
    voltageValues = None # stores voltage test values
    
    
    def __init__(self):
        
        
        # creates empty voltage array
        self.voltageValues = []
        
        
        # Tries to autopen the labjack. If it is already opened, just initialize the variable without opening
        try:
            self.ourU3 = u3.U3()
            

            
        except:
            print("Labjack already open or not connected")
            
            self.ourU3 = u3.U3(autoOpen = False)
                
        
        # confirms that the motor trigger input is set to off to start
        self.ourU3.writeRegister(self.DAC0_ADDRESS, 0)
        
        
        # Runs the test when u3 is connected
        self.runModbusTest()
        
        
        
        
    
    # returns true if the motor is moving (reads output trigger)
    def isMotorMoving(self):
        return (self.ourU3.readRegister(self.AIN1_ADDRESS) > 2)

    # uses the human input trigger to start moving the motor
    def incrementMotorUp(self):
        self.ourU3.writeRegister(self.DAC0_ADDRESS, self.MOTOR_VOLTAGE)
        time.sleep(1)
        self.ourU3.writeRegister(self.DAC0_ADDRESS, 0)
    
    # runs a test using the modbus data collection method
    def runModbusTest(self):
        # starts motor
        self.incrementMotorUp()
    
        i = 0
    
        while(True): # if this loop runs forever, you aren't detecting the motor stopping correctly
            # takes data if the motor is moving
            if (self.isMotorMoving()):
                currentValue = self.ourU3.readRegister(self.AIN0_ADDRESS)
                self.voltageValues.append(currentValue)
            elif (len(self.voltageValues) > 0):
                # stops taking data if the motor is not moving
                # confirms that we have taken any data so it does not stop right away
                break
            
            i+=1
            
            time.sleep(0.001) # can change this. Not the best way to know how many samples/sec
    
        self.runAnalysis() # runs analysis after done taking data
        
    # old code for how we used to run the tests. May come back to this later
    def runStreamTest(self):
        print("not currently configured")
        # ourU3.configIO(FIOAnalog =1, EnableCounter0 = True)
    

        # # ourU3.streamConfig(NumChannels = 2, PChannels= [0,210], NChannels=[31,31], Resolution = 3, SampleFrequency = 10000)
        # ourU3.streamConfig(NumChannels = 1, PChannels= [0], NChannels=[31], Resolution = 3, SampleFrequency = 10000, SamplesPerPacket = 25)
        # try:
            #     print("starting stream")
        #     #ourU3.streamStart()
        
        
        #     startSeconds = time.time()
        
        #     currentSeconds = time.time()
        
                
        #     # for r in ourU3.streamData():
            #     #     currentSeconds = time.time()
            #     #     totalTime = currentSeconds-startSeconds
            #     #     if (totalTime >= 12.5):
                #     #         break
            
            #     #     if r is not None:
                
                #     #         for values in r['AIN0']:
                    #     #             voltageValues.append(values)
    
    # Runs analysis on the voltage values we have already collected
    def runAnalysis(self):
        self.ourU3.close()
        
        voltValuesNP = np.array(self.voltageValues)
        
        analyzeData(voltValuesNP, False, True)

# this class analyzes the data
class analyzeData:
    # CONSTANTS
    STEPS_PER_RUN = 1250 # currently how many steps per run we do
    LAM = 632.8 # wavelength of the laser we were using
    
    # values for our axes on our graphs
    
    voltageValues = None
    stepsValues = None
    
    ft = None
    frq = None
    
    
    # voltage arrays for testing purposes only
    mvoltarray = np.array([-832, -600, -384, -344,-520,-776,-920,-976,-864,-760,-560,-416,-336,-392,-504,-672,-864,-984,-928,-840,-592,-424,-352])
    voltarray = mvoltarray / 1000
    
    
    def __init__(self, voltageValues, isTest, wantGraph):
        # if isTest is true then use the testing arrays
        # if false then use the input array (what we will be doing when running the real data)
        if (isTest):
            self.voltageValues = self.voltarray
        else:
            self.voltageValues = voltageValues
        
        
        # average = np.average(self.voltageValues)
        # print(average)
        # self.voltageValues = self.voltageValues - average
        
        
        
        # set the steps axis 
        self.stepsValues = np.linspace(0,self.STEPS_PER_RUN,len(self.voltageValues))
        
        # calculate the fourier transform and find the magnitude using the conjugate
        self.ft = np.fft.rfft(self.voltageValues)
        self.ft = self.ft * np.conj(self.ft)

        # find the frequency values in 1 / sample
        self.frq = np.fft.rfftfreq(len(self.stepsValues), 1)
        
        # function finds the max frequency value
        maxFreq = self.getFreqAtMax()
        
        # function finds a guess for g (don't need to run everytime)
        #self.guessG(maxFreq)
        
        # creates the graph window
        if (wantGraph):
            self.createGraph()
        
        # stores the data in a text file (comment out if we don't need to save)
        #self.storeDataInText()
        
        # better way to save data we are using now. Can still use text if needed (uncomment line above)
        self.storeDataInObject()
        
        
    # function prints the frequency value at the max (in 1/sample)
    def getFreqAtMax(self):
        maxvalue = self.ft[1:100].max()

        maxindex = np.where(self.ft == maxvalue)

        freqatmax = self.frq[maxindex]

        print("Freq at max: " + str(freqatmax))
        
        return freqatmax
    
    # function finds a guess for g (nm/step)
    def guessG(self, freqatmax):
        periodguess = 1 / freqatmax
    
        nmpersample = (self.LAM / 2 ) / periodguess
    
        sampleperstep = len(self.voltageValues) / self.STEPS_PER_RUN
    
        guessg = nmpersample * sampleperstep
    
        print("Guess for g: " + str(guessg))
    
    # function stores the data in a text file (.csv really)
    def storeDataInText(self):
        # combines both step and voltage arrays into 1 2d array for storage
        combinedArrayNP = np.vstack((self.stepsValues, self.voltageValues)).T
        
        # takes input from user on filename
        fileName = input("Enter the name of the file to save the data: ")
        
        fileNameExt = fileName + ".csv"
        
        # creates file
        np.savetxt(fname = fileNameExt, X = combinedArrayNP, delimiter=",", header = "Steps ||| Voltage (Header)", footer = "Steps ||| Voltage (Footer)")
    
    # stores the data in a dill (python library, might need to download) file, which stores all the methods/attributes of the object
    # much easier to unpack than a text file
    # put in terminal "pip install dill" if your computer does not recognize dill
    def storeDataInObject(self):
        decision = input("Do you want to save this data? (y or n): ")
        
        if (decision ==  "y"):
            # takes input to get filename for the pickle/dill file
            fileName = input("Enter the name of the file to save the object: ")
        
            fileNameExt = fileName + ".pkl"
        
            # saves the data into the file
            with open(fileNameExt, 'wb') as f:
                dill.dump(self, f)
            
        
    # creates the graph window
    def createGraph(self):
        # creating the window and setting the size
        window = tkinter.Tk()
        window.title("Fourier Transform Data")
        window.configure(width=750, height=500)
        window.configure(bg='lightgray')
    
        # sets the format layout for the window
        winWidth = window.winfo_reqwidth()
        winwHeight = window.winfo_reqheight()
        posRight = int(window.winfo_screenwidth() / 2 - winWidth / 2)
        posDown = int(window.winfo_screenheight() / 2 - winwHeight / 2)
        window.geometry("+{}+{}".format(posRight, posDown))
    
    
    
    
        # creating a figure from the matplotlib library
        fig = Figure(figsize=(5, 4), dpi=100)
        
        
        # adding fourier transform graph 
        myPlot = fig.add_subplot(111)
        myPlot.plot(self.frq[5:int(len(self.ft)/5)], self.ft[5:int(len(self.ft)/5)])
        
        myPlot.set_xlabel("1/Sample")
        myPlot.set_ylabel("Magnitude")
    
        canvas = FigureCanvasTkAgg(fig, master=window)  # A tk.DrawingArea.
        canvas.draw()
        canvas.get_tk_widget().pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=1)
    
        # adding raw data graph
        fig2 = Figure(figsize=(5, 4), dpi=100)
    
        myPlot2 = fig2.add_subplot(111)
        
        nmvalues = self.stepsValues * 16.5
        
        cmvalues = nmvalues * 10**(-7)
        
        wavenumbervalues = 1 / cmvalues
        
        myPlot2.plot(self.stepsValues, self.voltageValues)
        
        myPlot2.set_xlabel("Steps")
        myPlot2.set_ylabel("Voltage (v)")
    
        canvas2 = FigureCanvasTkAgg(fig2, master=window)  # A tk.DrawingArea.
        canvas2.draw()
        canvas2.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
    
        # creating toolbars to see cursors 
        toolbar = NavigationToolbar2Tk(canvas, window)
        toolbar.update()
        canvas.get_tk_widget().pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=1)
    
        toolbar = NavigationToolbar2Tk(canvas2, window)
        toolbar.update()
        canvas.get_tk_widget().pack(side=tkinter.RIGHT, fill=tkinter.BOTH, expand=1)
        
        # making sure the window closes correctly
        def on_closing():
            window.destroy()
    
        window.protocol("WM_DELETE_WINDOW", on_closing)
    
    
        window.mainloop()
    

# Needed for python to recognize main method at the top
if (__name__ == "__main__"):
    main()