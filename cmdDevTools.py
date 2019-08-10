"""
This is the Development Tools Command Line Interface. It will have controls for:
1) Generating a cropped region for pattern matching an array area
2) Clicking the window displays clicked region and brightnesses
3) Clicking two points will display the distance between the two
"""

import cv2
import numpy as np
from pypylon import pylon
import easygui
import json
from scipy import ndimage

imgScaleDown = 1
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

automaticPattern = True
houghParams = {"minDist": 60,
               "param1" : 12,
               "param2" : 17,
               "minRadius": 24,
               "maxRadius": 29}


arrayCoords = []
def mouseLocationClick(event, x, y, flags, param):
    """
        displays the active clicked location, and the distance between two clicked locations, specifically in pixels.
        Does not correct for downsampled images.
    """
    if event == cv2.EVENT_LBUTTONDOWN:
        print("click identified at: " + str([x,y]))
        arrayCoords.append([x,y])
    if event == cv2.EVENT_RBUTTONDOWN:
        if len(arrayCoords) > 1:
            locOne = arrayCoords.pop()
            locTwo = arrayCoords.pop()
            distance = np.linalg.norm(np.array(locOne)-np.array(locTwo))
            print("distance: " + str(distance))
        else:
            print("click 2 places first")

def cvWindow(name, image, keypressBool):
    print("---Displaying: "
          +  str(name)
          + "  ---")
    cv2.namedWindow(name, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(name, mouseLocationClick)
    cv2.imshow(name, image)
    pressedKey = cv2.waitKey(0)
    cv2.destroyAllWindows()
    if keypressBool:
        return pressedKey
    
def circlePixelID(circleList): # output pixel locations of all circles within the list,
    circleIDpointer = 0
    pixelLocations = []
    for eachCircle in circleList:
#        print("this circle is being analyzed in circle pixel ID")
#        print(eachCircle)
        xCoordCirc = eachCircle[0] # separates the x and y coordinates of the center of the circles and the circle radius 
        yCoordCirc = eachCircle[1]
        radiusCirc = eachCircle[2]
        for exesInCircle in range(( xCoordCirc - radiusCirc ),( xCoordCirc + radiusCirc )):
            whyRange = np.sqrt(pow(radiusCirc,2) - pow((exesInCircle - xCoordCirc),2)) #calculates the y-coordinates that define the top and bottom bounds of a slice (at x position) of the circle 
            discreteWhyRange = int(whyRange) 
            for whysInCircle in range(( yCoordCirc - discreteWhyRange),( yCoordCirc + discreteWhyRange)):
                pixelLocations.append([exesInCircle,whysInCircle, radiusCirc, circleIDpointer])
        circleIDpointer = circleIDpointer + 1 
    return pixelLocations

def circlePixelIDSingle(circleData):
    """Identifies all pixels within a circle

    Takes one circle centerpoint location and radius and calculates all pixel
    coords within the radius from that center location.

    Args:
        circleData (list): centerpoint row, centerpoint col, and radius
            for a circle in pattern

    Returns:
        pixelLocations (list): list of all pixel locations within a circle

    """
    pixelLocations = []
    # separates the x and y coordinates of the center of the circles and the
    # circle radius
    xCoordCirc = circleData[0]
    yCoordCirc = circleData[1]
    radiusCirc = circleData[2]
    for exesInCircle in range((xCoordCirc - radiusCirc),
                              (xCoordCirc + radiusCirc + 1)):
        # Calculates the y-coordinates that define the top and bottom bounds
        # of a slice (at x position) of the circle
        whyRange = np.sqrt(
            pow(radiusCirc, 2) - pow((exesInCircle - xCoordCirc), 2))
        discreteWhyRange = int(whyRange)
        for whysInCircle in range((yCoordCirc - discreteWhyRange),
                                  (yCoordCirc + discreteWhyRange + 1)):
            pixelLocations.append([exesInCircle, whysInCircle])
    return pixelLocations

def optionSelect():
    clearPrompt()
    print("Welcome to the D4Scope Development Tools Command line interface")
    print("by Jason Liu, August 7, 2019")
    optionLoop = True
    while optionLoop:
        print("    ")
        print("Image Analysis: 'A'")
        print("Camera Control: 'B'")
        print("Circle Pattern Generation: 'C'")
        print("Exit: 'X' or 'x'")
        cmdInput = input("Type in your desired selection and press enter to start: ")
        if cmdInput == 'X'or cmdInput == 'x':
            print("exiting program")
            break
        if cmdInput == 'A':
            imageAnalysis()
        if cmdInput == 'B':
            cameraControl()
        if cmdInput == 'C':
            patternGen()

def imageAnalysis():
    """ Image analysis downsamples the image by a factor set in the code
        this is important because sometimes the display may not be
        able to handle the full image displayed-- keep this in mind.

    """
    print("Image Analysis selected. Select and open an image")
    filePath = openImgFile()
    if filePath:
        print("Opening " + str(filePath))
        image = cv2.imread(filePath, -1)
        for each in range(imgScaleDown-1):
            image = cv2.pyrDown(image)
        print("Bitdepth: " + str(np.amax(image)))
        print("Size: " + str(np.shape(image)))
        print("Lclick to display location")
        print("Rclick to calculate distance between two previous clicks")
        print("press any key to leave image analysis")
        cvWindow(filePath.split('.')[0].split("/")[-1], image, False)            
    else:
        print("Invalid File Path")

def openImgFile():
    filePath = easygui.fileopenbox()
    if filePath == None:
        return []
    # elif filePath.split('.')[-1] != ".tiff":
    #     print("only .tiff files can be opened")
    return filePath
    
def clearPrompt():
    for each in range(3):
        print("")

def buffer2image(buffer):
    converter = pylon.ImageFormatConverter()
    converter.OutputPixelFormat = pylon.PixelType_Mono8
    converter.OutputBitalignment = pylon.OutputBitAlignment_MsbAligned
    img = converter.Convert(buffer)
    image = img.GetArray()
    return image
    
def cameraControl():
    clearPrompt()
    print("Camera Control selected. Camera will connect")
    camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
    print("connected Device model: " +
          str(camera.GetDeviceInfo().GetModelName()))
    camera.Open()

    print("Live stream: 'L'; Single Capture: 'S'")
    optionSelect = input("Select Option: ")
    if optionSelect == 'L':
        liveStream(camera)
    if optionSelect == 'S':
        singleCapture(camera)

def cameraSetVals(camera, config):
    camera.Gain = config['gain']
    camera.ExposureTime = config['expo']
    camera.DigitalShift = config['digshift']
    camera.PixelFormat = config['pixelform']
    camera.BinningVertical.SetValue(config['binval'])
    camera.BinningHorizontal.SetValue(config['binval'])
    return camera
    
def liveStream(camera):
    clearPrompt()
    camera = cameraSetVals(camera, videoConfig)
    print("livestream activating. 'x' exit, 's' save last image")
    camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
    windowName = "live stream"
    cv2.namedWindow(windowName, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(windowName, mouseLocationClick)
    while camera.IsGrabbing():
        buffer = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
        if buffer.GrabSucceeded():
            frame = buffer2image(buffer)
            cv2.imshow(windowName, frame)
            keypress = cv2.waitKey(1)
            if keypress == ord('x'):
                cv2.destroyAllWindows()
                camera.StopGrabbing()
                break
            elif keypress == ord('s'):
                cv2.destroyAllWindows()
                camera.StopGrabbing()
                saveFName = input("Filename to save as (.tiff will be added)? ")
                cv2.imwrite(str(saveFName) + ".tiff", frame)
                print(saveFName + " saved.")
                break
        buffer.Release()
    camera.Close()

def singleCapture(camera):
    clearPrompt()
    camera = cameraSetVals(camera, singleConfig)
    buffer = camera.GrabOne(int(expo * 1.1))
    if not buffer:
        raise RuntimeError("Camera failed to capture single image")
    image = buffer2image(buffer)
    cvWindow("single capture result", image, False)
    saveFName = input("Filename to save as (.tiff will be added)? ")
    cv2.imwrite(str(saveFName) + ".tiff", image)
    print(saveFName + " saved.")
    camera.Close()

def patternGen():
    filePath = openImgFile()
    print("Opening " + str(filePath))
    image = cv2.imread(filePath, 0)
    
    # crops input image to array area, output = subImg
    print("leftclick positions (2) top left and bottom right corner bounds for the std. press d when done")
    keyPress= cvWindow('Raw Image',image, True)
    if keyPress == ord('d'):
        arrayBotRigCoords = arrayCoords.pop()
        arrayTopLefCoords = arrayCoords.pop()
        print("subplot coordinates: " + str(arrayBotRigCoords)+ " " + str(arrayTopLefCoords))
    cropXCoords = sorted([arrayBotRigCoords[0],arrayTopLefCoords[0]])
    cropYCoords = sorted([arrayBotRigCoords[1],arrayTopLefCoords[1]])
    print(str(cropXCoords))
    print(str(cropYCoords))
    subImg = image[cropYCoords[0]:cropYCoords[1],cropXCoords[0]:cropXCoords[1]].copy()
    cvWindow("test subimg", subImg, False)
    
    if automaticPattern:
        smoothImg = cv2.medianBlur(subImg, 3)
        circlesD = cv2.HoughCircles(smoothImg,
                                    cv2.HOUGH_GRADIENT,1,
                                    minDist = houghParams["minDist"],
                                    param1 = houghParams["param1"],
                                    param2 = houghParams["param2"],
                                    minRadius = houghParams["minRadius"],
                                    maxRadius = houghParams["maxRadius"])
        circlesX = np.uint(np.around(circlesD))
        circleLocs = circlesX[0]

        verImg = cv2.cvtColor(subImg.copy(), cv2.COLOR_GRAY2RGB)
        idealStdImg = np.zeros(subImg.shape, dtype = np.uint8)
        circlePixels = circlePixelID(circleLocs)
        for eachPixel in circlePixels:
            idealStdImg[eachPixel[1], eachPixel[0]] = 100

        for eachCircle in circleLocs:
            cv2.circle(verImg,
                       (eachCircle[0], eachCircle[1]),
                       eachCircle[2]+4,
                       (30,30,255),
                       3)
            cv2.circle(verImg,
                       (eachCircle[0], eachCircle[1]),
                       2,
                       (30,30,255),
                       2)
            cv2.circle(idealStdImg,
                       (eachCircle[0], eachCircle[1]),
                       eachCircle[2],
                       255,
                       3)
        cvWindow("verification image", verImg, False)
        cvWindow("pattern generated", idealStdImg, False)
    else:
        print("click centers of circles, then click (2) points that establish a horiz diameter of one circle. press x when done")
        keyPress= cvWindow('Cropped Image', subImg, True)

        diam1 = arrayCoords.pop()
        diam2 = arrayCoords.pop()
        fullDiam = abs(diam1[0]-diam2[0])
        circleLocs = []
        for each in range(numSpots):
            coords = arrayCoords.pop()
            circleLocs.append([coords[0],
                               coords[1],
                               round(fullDiam/2)])

        # Generates the ideal std image from the cropped array image
        idealStdImg = np.zeros(subImg.shape, dtype=np.uint8)
        circlePixels = circlePixelID(circleLocs)
        for eachPixel in circlePixels:
            idealStdImg[eachPixel[1], eachPixel[0]] = 50
        cvWindow("testIdeal", idealStdImg, False)
    print("pattern generated and saving now...")
    imageOutName = "standard_image.tiff"
    cv2.imwrite(imageOutName, idealStdImg)
    stdSpotDict = {"batch" : "cassio-EBOV",
                   "spot_info": circleLocs.tolist(),
                   "shape": [idealStdImg.shape[0],idealStdImg.shape[1]]}
    jsonFileOutName = "standard_image.json"
    out_file = open(jsonFileOutName, "w")
    json.dump(stdSpotDict, out_file)
    out_file.close()

def generatePatternMasks(spot_info, shape):
    """Creates masks from the pattern for later analysis of image

    Generates pattern from JSON encoded circle locations and generates masks
    for spots and bgMask. This is important for efficient quantification of
    brightness in the spots and background within the image.

    Args:
        spot_info (list): encoded circle coordinates within the pattern

        shape (list): encoded shape of the pattern, circles are relative to
            this.
    Returns:
        pattern (np array): the pattern to be found within the image

        spotsMask (np array): the masks for the spots within the image

        bgMask (np array): the masks for the background wihin the image

    """
    pattern = np.zeros(shape, dtype=np.uint8)
    spotsMask = pattern.copy()
    bgMask = 255 * np.ones(shape, dtype=np.uint8)
    for eachCircle in spot_info:
        circlePixels = circlePixelIDSingle(eachCircle)
        for eachPixel in circlePixels:
            pattern[eachPixel[1], eachPixel[0]] = 50
            spotsMask[eachPixel[1], eachPixel[0]] = 255
            bgMask[eachPixel[1], eachPixel[0]] = 0
        cv2.circle(pattern,
                   (eachCircle[0], eachCircle[1]),
                   eachCircle[2],
                   100,
                   3)
    return pattern, spotsMask, bgMask

def templateMatch8b(image, pattern):
    """ Core template matching algorithm to compare image to pattern

    Calculates the correlation between the pattern and the image at all points
    in 2d sliding window format weighs the correlations higher in the center of
    the image where the spots should be.

    Args:
        image (np array): the image to be processed

        pattern (np array): the pattern to be found in the image (circles)

    Returns:
        topLeftMatch (list): location of the best fit defined as the top left
            coordinate within the image

        verImg (np array): copy of the image in color with a rectangle drawn
            where the pattern was best fit

    """
    imageCols, imageRows = image.shape[::-1]
    stdCols, stdRows = pattern.shape[::-1]
    print("pattern std shape: " + str(pattern.shape[::-1]))
    # grab dimensions of input image and convert to 8bit for manipulation
    image8b = cv2.normalize(image.copy(),
                            np.zeros(shape=(imageRows, imageCols)),
                            0, 255,
                            norm_type=cv2.NORM_MINMAX,
                            dtype=cv2.CV_8U)
    verImg = cv2.cvtColor(image8b.copy(), cv2.COLOR_GRAY2RGB)

    res = cv2.matchTemplate(image8b, pattern, cv2.TM_CCORR_NORMED)
    _, _, _, max_loc = cv2.minMaxLoc(res)
    gausCols, gausRows = res.shape[::-1]
    print("max location REAL: " + str(max_loc))
    print("gaus img shape: " + str(res.shape[::-1]))

    x, y = np.meshgrid(range(gausCols), range(gausRows))
    centerRow = int((imageRows - stdRows)/2) - 200
    centerCol = int((imageCols - stdCols)/2)
    print("center row and col" + " " + str(centerRow) + " " + str(centerCol))
    # draws circle where the gaussian is centered.
    cv2.circle(verImg, (centerCol, centerRow), 3, (0, 0, 255), 3)
    sigma = 400  # inverse slope-- smaller = sharper peak, larger = dull peak
    gausCenterWeight = np.exp(-((x-centerCol)**2 + (y-centerRow)**2) /
                              (2.0 * sigma**2))
    _, _, _, testCenter = cv2.minMaxLoc(gausCenterWeight)
    print("gaussian center: " + str(testCenter))
    weightedRes = res * gausCenterWeight
    _, _, _, max_loc = cv2.minMaxLoc(weightedRes)
    print(max_loc)  # max loc is reported as written as column,row...
    bottomRightPt = (max_loc[0] + stdCols,
                     max_loc[1] + stdRows)
    # cv2.rectangle takes in positions as (column, row)....
    cv2.rectangle(verImg,
                  max_loc,
                  bottomRightPt,
                  (0, 105, 255),
                  15)
    # cvWindow("rectangle drawn", verImg, False)
    topLeftMatch = max_loc  # col, row
    return topLeftMatch, verImg

def patternMatching(rawImg16b, patternDict):
    """ Performs pattern matching algorithm on uploaded image

    Takes the input image to be processed and the pattern, and finds the
    circles, draws circles on a copy of the original image- on a verification
    image. Then, this program quantifies the brightness of the spot features
    and the background intensity within the pattern (not-spot areas). Spits out
    a downsized verification image (because it doesn't need to be 16 bit or as
    large as the original image to show that circles were found).

    Args:
        rawImg16b: 16 bit raw image to be pattern matched

        patternDict (dictionary): dictionary with encoded pattern

    Returns:
        payload (dictionary): contains verification image and the brightnesses
            of the spots and of the background

    """
    pattern, spotMask, bgMask = generatePatternMasks(patternDict['spot_info'],
                                                     patternDict['shape'])
    print(patternDict['spot_info'])
    max_loc, verImg = templateMatch8b(rawImg16b, pattern)
    stdCols, stdRows = pattern.shape[::-1]

    circleLocs = patternDict['spot_info']

    subImage = rawImg16b[max_loc[1]:max_loc[1] + stdRows,
                         max_loc[0]:max_loc[0] + stdCols].copy()
    for eachCircle in circleLocs:
        drawCircle  = [0,0]
        drawCircle[0] = eachCircle[0] + max_loc[0]
        drawCircle[1] = eachCircle[1] + max_loc[1]
        cv2.circle(verImg,
                   (drawCircle[0], drawCircle[1]),
                   eachCircle[2]+4,
                   (30, 30, 255),
                   3)
        cv2.circle(verImg,
                   (drawCircle[0], drawCircle[1]),
                   2,
                   (30, 30, 255),
                   2)
    print(patternDict['spot_info'])
    label_im, nb_labels = ndimage.label(spotMask)
    spot_vals = ndimage.measurements.mean(subImage, label_im,
                                          range(1, nb_labels+1))
    mean_vals = ndimage.measurements.mean(subImage, label_im)
    print(spot_vals)
    print(mean_vals)
    label_bg, bg_labels = ndimage.label(bgMask)
    mean_bg = ndimage.measurements.mean(subImage, label_bg)
    print(mean_bg)

    verImg = cv2.pyrDown(verImg)  # downsizes
    # cv2.imwrite("verification-img.tiff", verImg)
    payload = {"ver_Img": verImg,
               "intensities": spot_vals.tolist(),
               "background": mean_bg}
    print(patternDict['spot_info'])
    return payload
        
def main():
    optionSelect()

if __name__ == '__main__':
    main()