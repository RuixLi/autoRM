############################
# Version 5.4.2

# this script present Kalatsky & Stryker's stimuli for retinotopic mapping
# the default direction of moving bar is L2R -> R2L -> D2U -> U2D
# refer to Jun Zhuang, elife, 2017 for details
# the stimulus parameter is optimized for 32inch [1600,900] monitor

# written by Ruix.Li in Nov, 2018
# modified in Jun, 2019
# modified in Aug, 2020
# modified in Feb, 2021
# modified in Apr, 2021, fix and test NIDAQ functionality

############################
from psychopy.visual.windowwarp import Warper
import numpy as np
from psychopy import visual, monitors, core, event
import ctypes
import os
import math
import time
import json

################################
# -- expeirment information
subjectID = 'THYG6S0113Ma'  # mouse ID, used to name log files
experimenter = ''
usingDAQ = False  # set True to use DAQ
NIcounterPort = b"Dev3/ctr0"  # the counter port name
saveDir = ''  # save to here if defined
trialNum = 20  # number of trial for each direction
verbose = False  # print the current progress during stim
printIntervel = 10  # frame intervel to print

############################
# -- stim config
interTrialFrame = 30  # frame between each trial
squareSizeDeg = 20
squareFlipRate = 3
barWidthDeg = 15
barSpdDegPerSec = 10  # moving speed of the bar

# -- monitor information
monitorNum = 0  # set to 1 or 0 to change monitor
monitorName = ''  # set a monitor name from monitor center
monitorResolution = (1600, 900)  # in pixel
monitorSize = (70.9, 39.9)  # (x, y) in cm, not including boarders
gazeCenter = (0, 0)  # the projection of optical axis on the screen, in cm
monitorDisance = 20  # distance between eye and monitor, in cm
frameRate = 10  # used when not usingDAQ, 10 FPS imaging frame rate is recommended

# -- Setup NIQADs


def CHK(err):
    # error checking routine
    # if err is minus, returns error message
    ignoreError = False
    if err < 0 and not ignoreError:
        buf_size = 100
        buf = ctypes.create_string_buffer(buf_size)
        nidaq.DAQmxGetErrorString(err, ctypes.byref(buf), ctypes.c_uint32(buf_size))
        # DAQmxGetErrorString (int32 errorCode, char errorString[], uInt32 bufferSize);
        raise RuntimeError('NIDAQ call failed with error %d: %s' % (err, repr(buf.value)))


class DAQCounter:
    def __init__(self, lines, taskName="") -> None:
        self.taskName = taskName
        self.taskHandel = ctypes.c_ulong(0)
        self.lines = lines
        self.value = ctypes.c_ulong(0)
        self.verbose = False

        # built-in values
        self.rising = 10280
        self.falling = 10171
        self.countUp = 10128
        self.initialCount = ctypes.c_ulong(0)
        self.timeout = ctypes.c_double(10.0)

        print('DAQ-CNT: start ...')
        CHK(nidaq.DAQmxCreateTask(self.taskName, ctypes.byref(self.taskHandel)))
        # DAQmxCreateTask(const char taskName, taskHandel*) (* is output)
        CHK(nidaq.DAQmxCreateCICountEdgesChan(self.taskHandel, self.lines, "", self.falling, self.initialCount, self.countUp))
        # DAQmxCreateCICountEdgesChan(taskHandel, const char lines, const char name, int32 edge, uInt32 initialCount, int32 countDirection)
        CHK(nidaq.DAQmxStartTask(self.taskHandel))

    def read(self):
        if self.verbose:
            print('DAQ-CNT: read ...')
        CHK(nidaq.DAQmxReadCounterScalarU32(self.taskHandel, self.timeout, ctypes.byref(self.value), None))
        # DAQmxReadCounterScalarU32(taskHandel, float64 timeout, uInt32 value*, bool32 reserved)
        return self.value.value

    def clear(self):
        nidaq.DAQmxStopTask(self.taskHandel)
        nidaq.DAQmxClearTask(self.taskHandel)
        print('DAQ-CNT: clear ...')


if usingDAQ:
    try:
        nidaq = ctypes.windll.nicaiu  # load the DLL
        print('DAQ: load the DLL')
    except OSError:
        print('DAQ: can not load DLL')

    frameCounter = DAQCounter(NIcounterPort)


def deg2pix(degree, ori=0):
    degree = float(degree)
    pix = monitorResolution[ori] * monitorDisance * math.tan(math.radians(degree)) / monitorSize[ori]
    return pix


def pix2deg(pix, ori=0):
    pixCM = monitorSize[ori] * float(pix) / monitorResolution[ori]
    degree = math.degrees(math.atan(pixCM / float(monitorDisance)))
    return degree


currentFrame = 0
squareSizePix = np.floor(deg2pix(squareSizeDeg, 0))
verticalBarWidthPix = np.floor(deg2pix(barWidthDeg, 0))
horizontalBarwidthPix = np.floor(deg2pix(barWidthDeg, 1))
barSpdPixPerSec = np.floor(deg2pix(barSpdDegPerSec, 0) / frameRate)

# -- generate checkerboard
Dsquare = (squareSizePix, squareSizePix)
loc_center = (0, 0)  # the location center of checkerboard
coords = []  # coordinates of each square consisting the checkerboard
colors = []  # color index for each square

negCordx = monitorResolution[0] + gazeCenter[0]
posCordx = monitorResolution[0] - gazeCenter[0]
negCordy = monitorResolution[1] + gazeCenter[1]
posCordy = monitorResolution[1] - gazeCenter[1]

negCordxN = np.ceil(abs(negCordx / squareSizePix)) + 1
posCordxN = np.ceil(abs(posCordx / squareSizePix)) + 1
negCordyN = np.ceil(abs(negCordy / squareSizePix)) + 1
posCordyN = np.ceil(abs(posCordy / squareSizePix)) + 1
NsquareX = int(negCordxN + posCordxN + 1)  # the number of squares in a raw
NsquareY = int(negCordyN + posCordyN + 1)  # the number of squares in a column
Nsquare = NsquareX * NsquareY  # total number of squares

startCordX = -1 * (negCordxN + 0.5) * squareSizePix - squareSizePix / 2  # coordinate for start
stopCordX = (posCordxN + 0.5) * squareSizePix  # coordinate for stop
startCordy = -1 * (negCordyN + 0.5) * squareSizePix - squareSizePix / 2
stopCordy = (posCordyN + 0.5) * squareSizePix
coordsX = np.arange(startCordX, stopCordX, squareSizePix)
coordsY = np.arange(startCordy, stopCordy, squareSizePix)

colorsIdx = np.ones((NsquareX, NsquareY), dtype=int)
colorsIdx[1::2, ::2] = -1
colorsIdx[::2, 1::2] = -1

for i in range(NsquareX):
    for j in range(NsquareY):
        coords.append((coordsX[i], coordsY[j]))
        colors.append(np.array([1, 1, 1]) * colorsIdx[i][j])

# calculate positions of BKpre and BKpos
BKWidthX = monitorResolution[0] + verticalBarWidthPix
BKWidthY = monitorResolution[1] + horizontalBarwidthPix
vBKprePositions = [i for i in np.arange(BKWidthX, step=barSpdPixPerSec)]
vBKposPositions = [x - BKWidthX for x in vBKprePositions]
hBKprePositions = [i for i in np.arange(BKWidthY, step=barSpdPixPerSec)]
hBKposPositions = [x - BKWidthY for x in hBKprePositions]
vBKprePositionsInv = [-1 * i for i in np.arange(BKWidthX, step=barSpdPixPerSec)]
vBKposPositionsInv = [x + BKWidthX for x in vBKprePositionsInv]
hBKprePositionsInv = [-1 * i for i in np.arange(BKWidthY, step=barSpdPixPerSec)]
hBKposPositionsInv = [x + BKWidthY for x in hBKprePositionsInv]

for _ in range(interTrialFrame):
    vBKprePositions.insert(0, vBKprePositions[0])
    vBKposPositions.insert(0, vBKposPositions[0])
    hBKprePositions.insert(0, hBKprePositions[0])
    hBKposPositions.insert(0, hBKposPositions[0])
    vBKprePositionsInv.insert(0, vBKprePositionsInv[0])
    vBKposPositionsInv.insert(0, vBKposPositionsInv[0])
    hBKprePositionsInv.insert(0, hBKprePositionsInv[0])
    hBKposPositionsInv.insert(0, hBKposPositionsInv[0])

# -- set the warp center
monitorWidth = monitorSize[0]
monitorSizeM = map(float, monitorSize)
gazeCenterM = map(float, gazeCenter)
project_center = map(lambda x, y: (x + y / 2) / y, gazeCenter, monitorSizeM)
visualAzi = (0, pix2deg(negCordx) + pix2deg(negCordx))
visualElv = (-1*pix2deg(negCordy), pix2deg(negCordx))

# -- create monitor and window objects
monitor = monitors.Monitor(name=monitorName,
                           width=monitorWidth,
                           distance=monitorDisance)

monitor.setSizePix(monitorResolution)

myWin = visual.Window(size=monitorResolution,
                      fullscr=False,  # True for full screen
                      allowGUI=False,
                      color=[0, 0, 0],  # [0,0,0] is grey and [-1,-1,-1] is black
                      units='pix',
                      screen=monitorNum,
                      monitor=monitor,
                      useFBO=True)

# create the checkerboard
checkerboard = visual.ElementArrayStim(myWin,
                                       xys=coords,
                                       fieldPos=loc_center,
                                       colors=colors,
                                       nElements=Nsquare,
                                       elementMask=None,
                                       elementTex=None,
                                       contrs=1,
                                       sizes=Dsquare)

# generate BKpres and BKpos
hBKpre = visual.Rect(win=myWin,
                     units='pix',
                     width=monitorResolution[1],
                     height=monitorResolution[0],
                     ori=90,
                     contrast=1,
                     opacity=1,
                     fillColor=[0, 0, 0],
                     lineColor=[0, 0, 0],
                     pos=(0, hBKprePositions[0]))

hBKpos = visual.Rect(win=myWin,
                     units='pix',
                     width=monitorResolution[1],
                     height=monitorResolution[0],
                     ori=90,
                     contrast=1,
                     opacity=1,
                     fillColor=[0, 0, 0],
                     lineColor=[0, 0, 0],
                     pos=(0, hBKposPositions[0]))

vBKpre = visual.Rect(win=myWin,
                     units='pix',
                     width=monitorResolution[0],
                     height=monitorResolution[1],
                     ori=0,
                     contrast=1,
                     opacity=1,
                     fillColor=[0, 0, 0],
                     lineColor=[0, 0, 0],
                     pos=(vBKprePositions[0], 0))

vBKpos = visual.Rect(win=myWin,
                     units='pix',
                     width=monitorResolution[0],
                     height=monitorResolution[1],
                     ori=0,
                     contrast=1,
                     opacity=1,
                     fillColor=[0, 0, 0],
                     lineColor=[0, 0, 0],
                     pos=(vBKposPositions[0], 0))

warper = Warper(win=myWin,
                warp='cylindrical',
                warpfile="",
                warpGridsize=300,
                eyepoint=project_center,
                flipHorizontal=False,
                flipVertical=False)

# -- calculate frames for trial and recording
verticalFrame = len(vBKprePositions)
horizontalFrame = len(hBKprePositions)
vtTrailsFrame = trialNum * len(vBKprePositions)
hzTrialsFrame = trialNum * len(hBKprePositions)
totalFrame = 2 * vtTrailsFrame + 2 * hzTrialsFrame
contrast = [-1, 1]

# -- prepare and wait for start

print('subject ID: %s' % subjectID)
print('stimulation is ready to go...')
print('a vertical trial has %s frames' % str(len(vBKprePositions)))
print('a horizontal trial has %s frames' % str(len(hBKprePositions)))
print('set total frame number as %d' % totalFrame)

quitind = 0
trial_counter = 0
hzFlg = 2 * vtTrailsFrame
clock = core.Clock()

while currentFrame < totalFrame and quitind == 0:  # start the trial
    checkerboard.contrs = contrast[int(np.floor(np.mod(clock.getTime() * 2 * squareFlipRate, 2)))]  # make contrast flip
    checkerboard.draw()

    x_j = np.mod(currentFrame - 1, len(vBKprePositions))
    y_j = np.mod(currentFrame - hzFlg - 1, len(hBKprePositions))

    # L2R
    if currentFrame <= vtTrailsFrame:
        vBKpre.pos = (vBKprePositions[x_j], 0)
        vBKpos.pos = (vBKposPositions[x_j], 0)
        barPosition = 0.5 * (vBKpre.pos[0] + vBKpos.pos[0])
        if verbose and currentFrame % printIntervel == 0:
            print('frame: %d, bar position: %2.1f deg   \r' % (currentFrame, pix2deg(barPosition, 0) + pix2deg(negCordx)), end='', flush=True)
        vBKpre.draw()
        vBKpos.draw()

    # R2L
    if currentFrame > vtTrailsFrame and currentFrame <= hzFlg:
        vBKpre.pos = (vBKprePositionsInv[x_j], 0)
        vBKpos.pos = (vBKposPositionsInv[x_j], 0)
        barPosition = 0.5 * (vBKpre.pos[0] + vBKpos.pos[0])
        if verbose and currentFrame % printIntervel == 0:
            print('frame: %d, bar position: %2.1f deg   \r' % (currentFrame, pix2deg(barPosition, 0) + pix2deg(negCordx)), end='', flush=True)
        vBKpre.draw()
        vBKpos.draw()

    # D2U
    if currentFrame > hzFlg and currentFrame <= hzFlg + hzTrialsFrame:
        hBKpre.pos = (0, hBKprePositions[y_j])
        hBKpos.pos = (0, hBKposPositions[y_j])
        barPosition = 0.5 * (hBKpre.pos[1] + hBKpos.pos[1])
        if verbose and currentFrame % printIntervel == 0:
            print('frame: %d, bar position: %2.1f deg   \r' % (currentFrame, pix2deg(barPosition, 1)), end='', flush=True)
        hBKpre.draw()
        hBKpos.draw()

    # U2D
    if currentFrame > hzFlg + hzTrialsFrame:
        hBKpre.pos = (0, hBKprePositionsInv[y_j])
        hBKpos.pos = (0, hBKposPositionsInv[y_j])
        barPosition = 0.5 * (hBKpre.pos[1] + hBKpos.pos[1])
        if verbose and currentFrame % printIntervel == 0:
            print('frame: %d, bar position: %2.1f deg   \r' % (currentFrame, pix2deg(barPosition, 1)), end='', flush=True)
        hBKpre.draw()
        hBKpos.draw()

    myWin.flip()

    if usingDAQ == True:
        currentFrame = frameCounter.read()  # pass the camera frame to the code
    else:
        currentFrame = int(frameRate * clock.getTime())

    for key in event.getKeys():  # quit if press q or esc
        if key in ['escape', 'q']:
            quitind = 1

myWin.close()
if usingDAQ:
    frameCounter.clear()

print('stim over...')
print('real frame number is', currentFrame)

if totalFrame > currentFrame + 3:
    print('experiment is interupted, not save logs')
    savelog = False
else:
    savelog = True

if savelog == True:
    dateTimeStamp = time.strftime("%y%m%d%H%M")
    dateTime = time.strftime("%Y/%m/%d-%H:%M:%S")
    logName = 'RMlog' + '-' + subjectID + '-' + dateTimeStamp + '.txt'
    print('logging...')

    if not saveDir:
        expLog = open(logName, 'w+')
    else:
        expLog = open(os.path.join(saveDir, logName), 'w+')

    expLog.write('########## RM-LOG ##########\n')
    expLog.write('######### BASIC INFO #########\n')
    expLog.write('subjectID = %s\n' % subjectID)
    expLog.write('experimenter = %s\n' % experimenter)
    expLog.write('dateTime = %s\n' % dateTime)
    expLog.write('dateTimeStamp = %s\n' % dateTimeStamp)
    expLog.write('\n')

    expLog.write('######## TRIAL CONFIG ########\n')
    expLog.write('totalFrame = %d\n' % totalFrame)
    expLog.write('realFrame = %d\n' % currentFrame)
    expLog.write('verticalFrame = %d\n' % verticalFrame)
    expLog.write('horizontalFrame = %d\n' % horizontalFrame)
    expLog.write('trialNum = %d\n' % trialNum)
    expLog.write('interTrialFrame = %d\n' % interTrialFrame)
    expLog.write('\n')

    expLog.write('######## STIM CONFIG ########\n')
    expLog.write('squareSizeDeg = %d deg\n' % squareSizeDeg)
    expLog.write('squareSizePix = %d pix\n' % squareSizePix)
    expLog.write('squareFlipRate = %d Hz\n' % squareFlipRate)
    expLog.write('barSpdDegPerSec = %d deg/sec\n' % barSpdDegPerSec)
    expLog.write('barSpdPixPerSec = %d deg/sec\n' % barSpdPixPerSec)
    expLog.write('barWidthDeg = %d deg\n' % barWidthDeg)
    expLog.write('\n')

    expLog.write('######## MONITOR INFO ########\n')
    expLog.write('monitorName = %s Hz\n' % monitorName)
    expLog.write('monitorResolution = %d x %d pixel\n' % (monitorResolution[0], monitorResolution[1]))
    expLog.write('monitorSize = %d x %d cm\n' % (monitorSize[0], monitorSize[1]))
    expLog.write('monitorDisance = %d cm\n' % monitorDisance)
    expLog.write('gazeCenter = (%d, %d)\n' % gazeCenter)
    expLog.write('visualAzi = (%.2f, %.2f) deg \n' % visualAzi)
    expLog.write('visualElv = (%.2f, %.2f) deg \n' % visualElv)
    expLog.write('\n')
    expLog.close()

    # create config file
    cnfgName = 'RMcnfg' + '-' + subjectID + '-' + dateTimeStamp + '.json'

    cnfgDict = {
        "subjectID": subjectID,
        "experimenter": experimenter,
        "dateTime": dateTime,
        "dateTimeStamp": dateTimeStamp,
        "verticalFrame": verticalFrame,
        "horizontalFrame": horizontalFrame,
        "trialNum": trialNum,
        "interTrialFrame": interTrialFrame,
        "totalFrame": totalFrame,
        "realFrame": currentFrame,
        "monitorName": monitorName,
        "monitorResolution": monitorResolution,
        "monitorSize": monitorSize,
        "monitorDisance": monitorDisance,
        "gazeCenter": gazeCenter,
        "squareSizeDeg": squareSizeDeg,
        "squareSizePix": squareSizePix,
        "squareFlipRate": squareFlipRate,
        "barSpdPixPerSec": barSpdPixPerSec,
        "barSpdDegPerSec": barSpdDegPerSec,
        "barWidthDeg": barWidthDeg,
        "visualAzi": visualAzi,
        "visualElv": visualElv
    }

    if not saveDir:
        f = open(cnfgName, 'w')
        json.dump(cnfgDict, f, sort_keys=True, indent=4)
        f.close()
    else:
        f = open(os.path.join(saveDir, cnfgName), 'w')
        json.dump(cnfgDict, f, sort_keys=True, indent=4)
        f.close()

    print('log end...')
