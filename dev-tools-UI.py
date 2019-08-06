"""
This is the Development Tools User Interface. It will have buttons and display for:
1) Generating a cropped region for pattern matching an array area
2) Clicking the window displays clicked region and brightnesses
3) Clicking two points will display the distance between the two
"""

import os, sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (QApplication, 
                            QMainWindow, 
                            QVBoxLayout, 
                            QFileDialog)
from matplotlib.backends.backend_qt5agg import (
        FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure
import cv2
import numpy as np
import time
import pyqtgraph as pg
from pypylon import pylon
from encodedDevUI import Ui_MainWindow

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.readImgButton.clicked.connect(self.readImage)
        self.analyzeImgButton.clicked.connect(self.analyzeImage)
        self.saveImgButton.clicked.connect(self.saveImage)
        self.liveStreamButton.clicked.connect(self.liveStream)
        self.stopStreamButton.clicked.connect(self.stopStream)
        
        #plotting
        self.plotting_widget.setLayout(QVBoxLayout())
        self.im_widget = pg.ImageView(self)
        self.im_widget.ui.histogram.hide()
        self.im_widget.ui.roiBtn.hide()
        self.im_widget.ui.menuBtn.hide()
            
        self.plotting_widget.layout().addWidget(self.im_widget)
        self.im_widget.show()


    def bottomTextBox(self, text):
        self.bottomDialogBox.setText(QtWidgets.QApplication.translate("", text, None, -1))


    def liveStream(self):
        self.stopStream = False
        self.camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        self.camera.Open()
        
       # Sets camera parameters for live viewing
        self.camera.Gain = 24
        self.camera.ExposureTime = 1e4
        self.camera.DigitalShift = 4
        self.camera.PixelFormat = "Mono8"
        
        # Set up impage processing for OpenCV
        converter = pylon.ImageFormatConverter()
        converter.OutputPixelFormat = pylon.PixelType_BGR8packed
        converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
        
        # Start video feed
        self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
    
        self.bottomTextBox("escape to stop stream")
        while (self.camera.IsGrabbing() & (not self.stopStream)):
            # Store image data
            self.buffer = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
            if self.buffer.GrabSucceeded():
                # Convert to openCV format
                frame = converter.Convert(self.buffer)
                frame_arr = frame.GetArray()
                gray = cv2.cvtColor(frame_arr, cv2.COLOR_BGR2GRAY)
                # Open window for feed and present frame
                self.im_widget.setImage(cv2.pyrDown(gray.transpose()))
            self.buffer.Release()
            QtCore.QCoreApplication.processEvents()
        # Close procedure
        self.camera.StopGrabbing()
        self.camera.Close()
        
    def stopStream(self):
        self.stopStream = True
        # Close procedure
        self.camera.StopGrabbing()
        self.camera.Close()
    
    def readImage(self):
        pass
    def analyzeImage(self):
        pass
    def saveImage(self):
        pass

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