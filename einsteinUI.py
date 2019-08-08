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
from cmdDevTools import (cvWindow,
                         circlePixelID,
                         openImgFile,
                         buffer2image,
                         cameraSetVals,
                         singleCapture)

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
        self.editTextBox("single image captured")
    
    def saveImage(self):
        fileName = self.lineEdit.text()
        fileName = fileName + ".tiff"
        cv2.imwrite(fileName, self.image)
        self.editTextBox(fileName + " has been saved")

    def openImage(self):
        self.editTextBox("file opened")

    def stopStream(self):
        self.stopStream = True
        # Close procedure
        self.camera.StopGrabbing()
        self.camera.Close()

    def readImage(self):
        self.image = singleCapture(12, 1e4, 4, "Mono12p")
        self.im_widget.setImage(self.image.transpose())
        self.bottomTextBox("image captured")
    
    def circleDictUpload(self):
        self.bottomTextBox("circle dictionary uploaded")

    def autoOn(self):
        pass
    
    def autoOff(self):
        pass

    def analyzeImage(self):
        self.bottomTextBox("Function not yet implemented")
    
        
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

