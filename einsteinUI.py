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
import cv2
import numpy as np
import time
import pyqtgraph as pg
from pypylon import pylon
from einsteinEncodedUI import Ui_MainWindow
import easygui
from cmdDevTools import (cvWindow,
                         circlePixelID,
                         openImgFile,
                         buffer2image,
                         cameraSetVals,
                         singleCapture,
                         templateMatch8b)

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
        self.shotButton.clicked.connect(self.singleCapture)
        self.saveButton.clicked.connect(self.saveImage)

        
        self.actionOpen_Image.triggered.connect(self.openImage)
        self.actionOpen_Circle_Dictionary.triggered.connect(self.circleDictUpload)
        
        self.actionon.triggered.connect(self.autoOn)
        self.actionoff.triggered.connect(self.autoOff)
    
        self.plotting_widget.setLayout(QVBoxLayout())
        self.im_widget = pg.ImageView(self)
        self.im_widget.ui.histogram.hide()
        self.im_widget.ui.roiBtn.hide()
        self.im_widget.ui.menuBtn.hide()
        self.plotting_widget.layout().addWidget(self.im_widget)
        self.im_widget.show()


    def editTextBox(self, text):
        self.label.setText(QtWidgets.QApplication.translate("", text, None, -1))

    def videoToggle(self):
        if self.videoOn:
            self.editTextBox("live stream off")
            self.videoOn = False
        else:
            self.editTextBox("live stream on")
            self.videoOn = True

    def singleCapture(self):
        self.camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        self.camera.Open()
        self.camera = cameraSetVals(self.camera)
        buffer = self.camera.grabOne(int(singleConfig['expo']*1.1))
        if not buffer:
            raise RuntimeError("Camera failed to capture single image")
        self.image = buffer2image(buffer)
        self.displayImageFullScreen(self.image)
        self.displayImageInWindow(self.image)
        self.editTextBox("Captured. Save it!")
    
    def saveImage(self):
        fileName = self.lineEdit.text()
        fileName = fileName + ".tiff"
        cv2.imwrite(fileName, self.image)
        self.editTextBox(fileName + " has been saved")

    def displayImageInWindow(self, imageToShow):
        cropImage = self.imageCenterCrop(imageToShow)
        resizedImg = cv2.resize(cropImage, (480, 320))
        self.im_widget.setImage(resizedImg.transpose())

    def displayImageFullscreen(self,imageToShow):
        windowName = "fullscreen image"
        cv2.namedWindow(windowName, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(windowName, cv2.WND_PROP_FULLSCREEN, 
                              cv2.WINDOW_FULLSCREEN)
        resizedImg = cv2.resize(imageToShow, (480, 320))
        cv2.imshow(windowName, imageToShow)
        cv2.waitKey(3000)
        cv2.destroyAllWindows()

    def imageCenterCrop(self, image):
        """ Takes a full 3088x2064 basler output image
            and crops to the region of interest. saves memory and ups speed
            top left - bottom right, xy
            650, 120 to 2200, 1500. will need to change later.
            final size 700 x 430
        """
        croppedImage = image[120:1500, 650:2200]
        return croppedImage

    def openImage(self):
        filePath = openImgFile()
        self.editTextBox("opening " + str(filePath))
        self.image = cv2.imread(filePath, 0)        
        self.displayImageFullscreen(self.image)
        self.displayImageInWindow(self.image)
        self.editTextBox("image opened")

    def circleDictUpload(self):
        """ 
            currently takes in the template image that needs to be matched.
            implementing json later...
        """
        filePath = openImgFile()
        self.editTextBox("opening " + str(filePath))
        self.template = cv2.imread(filePath, 0)        
        self.displayImageFullscreen(self.template)
        self.editTextBox("circle dictionary uploaded")

    def autoOn(self):
        if self.template.any() and self.image.any():
            print("yahtzee")
        else:
            self.editTextBox("You need to upload image and template")
        pass
    
    def autoOff(self):
        pass

    def analyzeImage(self):
        self.editTextBox("Function not yet implemented")
    
        
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

