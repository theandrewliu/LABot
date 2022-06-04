import numpy as np
import win32.lib.win32con as win32con
import win32.win32gui as win32gui
import pythonwin.win32ui as win32ui
from threading import Thread, Lock

class WindowCapture:

    #threading properties
    stopped = True
    lock = None
    screenshot = None
    #properties
    w = 0
    h = 0
    hwnd = None
    cropped_x = 0
    cropped_y = 0
    offset_x = 0
    offset_y = 0

    #constructor
    def __init__(self, window_name=None):
        # create a thread lock object
        self.lock = Lock()

        # find the handle for the window we want to capture.
        # if no window name is given, capture the entire screen.
        if window_name is None:
            self.hwnd = win32gui.GetDesktopWindow()
        else:
            #hwnd = win32gui.FindWindow(None, windowname)
            self.hwnd = win32gui.FindWindow(None, window_name)
            # if window_name is given but cannot find window or window not open 
            # throw exception
            if not self.hwnd:
                raise Exception('Window not found {}'.format(window_name))
        
        # get the window size
        window_rect = win32gui.GetWindowRect(self.hwnd)
        self.w = window_rect[2] - window_rect[0]
        self.h = window_rect[3] - window_rect[1]

        # account for the windeo border and titlebar and cut them off
        border_pixels = 8
        titlebar_pixels = 30
        self.w = self.w - (border_pixels * 2)
        self.h = self.h - titlebar_pixels - border_pixels
        self.cropped_x = border_pixels
        self.cropped_y = titlebar_pixels

        # set the cropped coordinates offset so we can translate screenshot
        # images into the actual screen positions
        self.offset_x = window_rect[0] + self.cropped_x
        self.offset_y = window_rect[1] + self.cropped_y
    
    def get_screenshot(self):

        # w = 1920 # set this
        # h = 1080 # set this
        # bmpfilename = "out.bmp" #set this

        # get the window image data
        wDC = win32gui.GetWindowDC(self.hwnd)
        dcObj=win32ui.CreateDCFromHandle(wDC)
        cDC=dcObj.CreateCompatibleDC()
        dataBitMap = win32ui.CreateBitmap()
        dataBitMap.CreateCompatibleBitmap(dcObj, self.w, self.h)
        cDC.SelectObject(dataBitMap)
        cDC.BitBlt((0,0),(self.w, self.h) , dcObj, (self.cropped_x,self.cropped_y), win32con.SRCCOPY)

        # save the screenshot
        # dataBitMap.SaveBitmapFile(cDC, 'debug.bmp')
        signedIntsArray = dataBitMap.GetBitmapBits(True)
        img = np.fromstring(signedIntsArray, dtype= 'uint8')
        img.shape = (self.h, self.w , 4)

        # Free Resources
        dcObj.DeleteDC()
        cDC.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, wDC)
        win32gui.DeleteObject(dataBitMap.GetHandle())

        # drop the alpha channel, or cv.matchTemplate() will throw an error like:
        # error: (-215:Assertion failed) (depth == CV_8U || depth == CV_32F) && type == _temp1.type()
        # && _img.dims() <= 2 in function 'cv::matchTemplate'
        img = img[...,:3]

        # make image C_CONTIGUOUS to avoid errors that look like:
        # File ... in draw_rectangles
        # TypeError: an integer is required (got type tuple)
        # see the discussion here:
        # https://github.com/opencv/opencv/issues/14866#issuecomment-580207109
        img = np.ascontiguousarray(img)

        return img

    # find the name of the window you're interested in.
    # once you have it, update window_capture()
    # https://stackoverflow.com/questions/55547940/how-to-get-a-list-of-the-name-of-every-open-window
    @staticmethod
    def list_window_names():
        def winEnumHandler(hwnd, ctx):
            if win32gui.IsWindowVisible(hwnd):
                print(hex(hwnd), win32gui.GetWindowText(hwnd))
        win32gui.EnumWindows(winEnumHandler, None)
    # call like this:
    # list_window_names()

    def get_screen_position(self, pos):
        return (pos[0] + self.offset_x, pos[1] + self.offset_y)

    # threading methods
    def start(self):
        self.stopped = False
        t = Thread(target = self.run)
        t.start()
    
    def stop(self):
        self.stopped = True
    
    def run(self):
        while not self.stopped:
            # get an updated image of the game
            screenshot = self.get_screenshot()
            # lock the thread while updating the results
            self.lock.acquire()
            self.screenshot = screenshot
            self.lock.release()