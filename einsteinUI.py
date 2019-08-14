"""
    This will be the final User interface for the Einstein D4Scope. Specifically suited for touchscreen use (480x 320)
    Will have the following functions:
    1) Upload Circle dictionary
    2) Live Feed to Align Sample, then click feed to take picture (3088 x 2064)
    3) picture will auto-save, and display circle matches to verify fit
    4) will display avg brightnesses and background brightness
    5) unique ID assigned to image and saved (based on date/time) as tiff
    6) Outlier Detection
"""
import os, sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (QApplication, 
                            QMainWindow, 
                            QVBoxLayout, 
                            QFileDialog)
from scipy import ndimage
import cv2
import numpy as np
import time
import pyqtgraph as pg
from pypylon import pylon
from einsteinEncodedUI import Ui_MainWindow
import easygui
import json
import csv
from cmdDevTools import (cvWindow,
                         openImgFile,
                         buffer2image,
                         cameraSetVals,
                         templateMatch8b,
                         patternMatching,
                         generatePatternMasks)

# will store these configs in a json file later for modification
# Configs for video streaming, will be optimizable later
imgScaleDown = 2
videoConfig = {'gain': 24,
               'expo': 1e5,
               'digshift': 4,
               'pixelform':'Mono8',
               'binval': 2}

singleConfig = {'gain': 12,
                'expo': 1e6,
                'digshift': 4,
                'pixelform':'Mono12p',
                'binval': 2}

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        
        self.videoOn = False
        self.videoToggleButton.clicked.connect(self.videoToggle)
        self.shotButton.clicked.connect(self.singleCaptureUI)
        self.saveButton.clicked.connect(self.saveImage)

        self.actionOpen_Image.triggered.connect(self.openImage)
        self.actionOpen_Circle_Dictionary.triggered.connect(self.circleDictUpload)
        self.actionOpenData.triggered.connect(self.dataFileOpen)
        
        self.actionon.triggered.connect(self.autoOn)
        self.actionoff.triggered.connect(self.autoOff)
    
        self.plotting_widget.setLayout(QVBoxLayout())
        self.im_widget = pg.ImageView(self)
        self.im_widget.ui.histogram.hide()
        self.im_widget.ui.roiBtn.hide()
        self.im_widget.ui.menuBtn.hide()
        self.plotting_widget.layout().addWidget(self.im_widget)
        self.im_widget.show()
        self.circleDictUploaded = False


    def editTextBox(self, text):
        self.label.setText(QtWidgets.QApplication.translate("", text, None, -1))

    def videoToggle(self):
        if self.videoOn:
            self.editTextBox("live stream off")
            self.videoOn = False
            self.Camera.Close()
        else:
            self.editTextBox("live stream on, ESC to leave")
            self.VideoOn = True
            self.camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
            self.camera.Open()
            self.camera = cameraSetVals(self.camera, videoConfig)
            self.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
            while camera.IsGrabbing():
                buffer = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
                if buffer.GrabSucceeded():
                    frame = buffer2image(buffer)
                    self.displayImageFullscreen(frame, 1)
                    keypress = cv2.waitKey(1)
                    if keypress == 27:
                        cv2.destroyAllWindows()
                        camera.StopGrabbing()
                        break
                buffer.Release()
            camera.Close()

    def singleCaptureUI(self):
        self.camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        self.camera.Open()
        self.camera = cameraSetVals(self.camera, singleConfig)
        buffer = self.camera.grabOne(int(singleConfig['expo']*1.1))
        if not buffer:
            raise RuntimeError("Camera failed to capture single image")
        self.image = buffer2image(buffer)
        self.displayImageFullScreen(self.image, 2500)
        self.displayImageInWindow(self.image)
        self.buffer.Release()
        self.camera.Close()
        self.editTextBox("Captured. Save it!")
    
    def saveImage(self):
        fileName = self.lineEdit.text()
        fileName = fileName + ".tiff"
        cv2.imwrite(fileName, self.image)
        self.editTextBox(fileName + " has been saved")

    def displayImageInWindow(self, imageToShow):
        #cropImage = self.imageCenterCrop(imageToShow)
        #resizedImg = cv2.resize(cropImage, (480, 320))
        self.im_widget.setImage(imageToShow.transpose())

    def displayImageFullscreen(self,imageToShow, delayMs):
        windowName = "fullscreen image"
        cv2.namedWindow(windowName, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(windowName, cv2.WND_PROP_FULLSCREEN, 
                              cv2.WINDOW_FULLSCREEN)
        #resizedImg = cv2.resize(imageToShow, (480, 320))
        cv2.imshow(windowName, imageToShow)
        cv2.waitKey(delayMs)
        cv2.destroyAllWindows()

    def imageCenterCrop(self, image):
        """ Takes a full 3088x2064 basler output image
            and crops to the region of interest. saves memory and ups speed
            top left - bottom right, xy
            650, 120 to 2200, 1500. will need to change later.
            final size 700 x 430
        """
        croppedImage = image #[120:1500, 650:2200]
        return croppedImage

    def openImage(self):
        filePath = openImgFile()
        self.editTextBox("opening " + str(filePath))
        self.image = cv2.imread(filePath, -1)        
        self.displayImageFullscreen(self.image, 2500)
        self.displayImageInWindow(self.image)
        self.editTextBox("image opened")

    def circleDictUpload(self):
        """ 
            currently takes in the template image that needs to be matched.
            implementing json later...
        """
        filePath = openImgFile()
        self.editTextBox("opening " + str(filePath))
        #self.template = cv2.imread(filePath, 0)        
        #self.displayImageFullscreen(self.template)
        self.patternDict = {}
        with open(filePath) as json_file:
            self.patternDict = json.load(json_file)
        self.editTextBox("circle dictionary uploaded")
        self.circleDictUploaded = True

    def autoOn(self):
        self.payload = patternMatching(self.image, self.patternDict)
        #cvWindow("test", payload["ver_Img"], False)
        verImg = cv2.cvtColor(payload["ver_Img"].copy(), cv2.COLOR_BGR2GRAY)
        self.displayImageInWindow(verImg)
        textOut = ("avg intens: " + str(round(payload["avgIntens"], 2)) +
                   " . BG: " + str(round(payload["background"], 2)))
        self.editTextBox(textOut)
    def autoOff(self):
        pass

    def analyzeImage(self):
        self.editTextBox("Function not yet implemented")

    def dataFileOpen(self):
        self.editTextBox("Select Data File for output")
        filePath = openImgFile()



    
        
def main():
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()
    frame = MainWindow()
    frame.show()
    app.exec_()
    app.quit()

if __name__ == '__main__':
    main()

