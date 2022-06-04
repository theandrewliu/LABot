import keyboard
import cv2 as cv
import win32gui
import numpy as np
from time import time
from windowcapture import WindowCapture
from vision import Vision
from yolovision  import YoloVision
from bot import LABot, BotState

DEBUG = True
# change this based on game version
windowname = 'LOST ARK (64-bit, DX11) v.2.2.1.3'
# sets game as active window
win32gui.SetForegroundWindow(win32gui.FindWindow(None, windowname))

# initialize the WindowCapture class
wincap = WindowCapture(windowname)

# load the yolov5 detection
detector = YoloVision()
# load an empty Vision class
vision = Vision()
# initialize the bot
bot = LABot((wincap.offset_x, wincap.offset_y), (wincap.w, wincap.h))
# load the other stuff

wincap.start()
bot.start()
detector.start()

while(True):

    # if we don't have a screenshot, don't run code below this point
    if wincap.screenshot is None:
        continue

    # give the detector the current screenshot to search objects in
    detector.update(wincap.screenshot)

    # objects = detector.get_objects(screenshot)

    # bot stuff
    if bot.state == BotState.INITIALIZING:
        # while bot is waiting to start, begin by giving it targets to work on
        # when it does start
        enemy_rectangles = vision.enemy_rectangles(detector.objects)
        targets = vision.get_click_points(enemy_rectangles)
        bot.update_targets(targets)
    elif bot.state == BotState.IN_CITY:
        # when searching for something to click on, the bot needs to know what the click point are
        # for the current detection results. It also needs an updated screenshot
        detector.update(wincap.screenshot)
        enemy_rectangles = vision.enemy_rectangles(detector.objects)
        targets = vision.get_click_points(enemy_rectangles)
        bot.update_targets(targets)
        bot.update_screenshot(wincap.screenshot)
    elif bot.state == BotState.IN_DUNGEON:
        detector.update(wincap.screenshot)
        bot.update_targets(detector.objects)
        bot.update_screenshot(wincap.screenshot)

    if DEBUG:
        # draw the detection results onto the original image
        detection_image = vision.draw_rectangles(wincap.screenshot, detector.objects)
        cv.imshow('Matches', detection_image)


    # press 'q' with the output window focused to exit.
    # waits 1ms every loop to process key presses
    # only works with debug = true
    key = cv.waitKey(1)
    if key == ord('q'):
        wincap.stop()
        detector.stop()
        bot.stop()
        cv.destroyAllWindows()
        break

    if keyboard.is_pressed("q"):
        wincap.stop()
        detector.stop()
        bot.stop()
        break

print('Done.')
