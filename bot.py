import cv2 as cv
import numpy as np
import pyautogui, random
from time import sleep, time
from math import sqrt
from threading import Thread, Lock
from windowcapture import WindowCapture
import os


class BotState:
    INITIALIZING = 0
    IN_CITY = 1
    IN_DUNGEON = 2

class LABot:

    # constants
    INITIALIZING_SECONDS = 5
    REPAIR_COOLDOWN_SECONDS = 500

    # threading properties
    stopped = True
    lock = None

    # properties
    targets = []
    window_offset = (0,0)
    window_h = 0
    window_w = 0
    screenshot = None
    wincap = WindowCapture('LOST ARK (64-bit, DX11) v.2.2.1.3')

    # image file paths
    accept_button = "images/accept.jpg"
    dead_button_button = "images/base_res_unhighlited.png"
    dead_status_img = "images/dead.png"
    enter_button = "images/enter.jpg"
    hand_icon = "images/hand_icon.jpg"
    in_city_status = "images/in_city.jpg"
    in_combat_status = "images/in_combat.jpg"
    repair_icon = "images/pet_menu_repair_icon.jpg"
    leave_combat = "images/leave_dungeon.jpg"
    ok_leave = "images/ok_leave.jpg"
    # need_repair = "images/repair_indicator.jpg"
    # repair_gear_button = "images/repair_equipped_gear.png"
    # repair_leave_button = "images/repair_leave_button.png"
    
    MOVE = False
    available_spells = []
    method = cv.TM_CCOEFF_NORMED

    def __init__(self, window_offset, window_size):
        # create thread lock object
        self.lock = Lock()

        # for translating window positions into screen positions, it's easier to just
        # get  the offsets and window size from WindowCapture rather than passing in
        # the whole object
        self.window_offset = window_offset
        self.window_w = window_size[0]
        self.window_h = window_size[1]

        self.state = BotState.INITIALIZING
        self.timestamp = time()
        self.record = time()
        self.need_repair = False
        self.time_to_leave = False
        self.dungeon_begin = True

    def targets_ordered_by_distance(self, targets):
        # character is always in the center of the screen
        my_pos = (self.window_w /2, self.window_h / 2)

        def pythagorean_distance(pos):
            return sqrt((pos[0] - my_pos[0])**2 + (pos[1] - my_pos[1])**2)
        targets.sort(key=pythagorean_distance)

        targets = [t for t in targets]

        return targets

    # translate a pixel position on a screenshot image to a pixel position on the screen.
    # pos = (x, y)
    # WARNING: if you move the window being captured after execution is started, this will
    # return incorrect coordinates, because the window position is only calculated in
    # the WindowCapture __init__ constructor.
    def get_screen_position(self, pos):
        return (pos[0] + self.window_offset[0], pos[1] + self.window_offset[1])

    def waitRandomizedTime(self,min,max):
        sleep(random.uniform(min,max))
    
    def find_pos(self, file_path, threshhold, method):
        # load in the reference image
        find = cv.imread(file_path, cv.IMREAD_UNCHANGED)
        # find it on the screen
        result = cv.matchTemplate(self.screenshot, find, method)
        # retrieve the top left coordinate where reference image is located and
        # confidence value
        _, maxVal, _, maxLoc = cv.minMaxLoc(result)
        
        # width and height of reference image to calculate the center point 
        w = find.shape[1]
        h = find.shape[0]
        pre_offset = maxLoc[0] + int(w/2), maxLoc[1] + int(h/2)
        
        # check if confidence is above the input threshold
        if maxVal > threshhold:
            # print("maxLoc:", maxLoc, "maxVal:", maxVal)
            # get position on screen and return it to click
            (x, y) = self.wincap.get_screen_position(pre_offset)
            # print(x, y)
            return x, y

    def repair_gear(self):
        pyautogui.hotkey("alt","p")
        self.waitRandomizedTime(1,2)
        x, y = self.find_pos(self.repair_icon, 0.9, self.method)
        # x, y = self.wincap.get_screen_position((840,469))
        pyautogui.moveTo(x, y, 0.5)
        pyautogui.click()
        self.waitRandomizedTime(2,3)
        x, y = self.wincap.get_screen_position((700, 285))
        pyautogui.moveTo(x,y)
        pyautogui.click()
        self.waitRandomizedTime(1,2)
        x, y = self.wincap.get_screen_position((1180,680))
        pyautogui.moveTo(x, y, 0.5)
        pyautogui.click()
        self.waitRandomizedTime(1,2)
        pyautogui.hotkey("alt","p")
        self.need_repair = False
    
    # def check_available(self,image_path, threshold):
    #     check = cv.imread(image_path, cv.IMREAD_UNCHANGED) 
    #     result = cv.matchTemplate(self.screenshot, check, self.method)
    #     _, _, _, conf = cv.minMaxLoc(result)
    #     if conf > threshold:
    #         return True
    #     else:
    #         return False

    def check_repair(self):
        if time() > self.record + self.REPAIR_COOLDOWN_SECONDS:
            self.need_repair = True
            self.record = time()

    def dungeon_time(self):
        # 5 minutes
        if time() > self.timestamp + 300:
            self.time_to_leave = True
            

    def initialize_dungeon(self):
        pyautogui.hotkey('g')
        self.waitRandomizedTime(1,2)
        # x, y = self.wincap.get_screen_position((945,575))
        x, y = self.find_pos(self.enter_button, 0.9, self.method)
        print(x,y)
        pyautogui.moveTo(x, y)
        pyautogui.click()
        self.waitRandomizedTime(1,2)
        # x, y = self.wincap.get_screen_position((575,405))
        x, y = self.find_pos(self.accept_button, 0.9, self.method)
        pyautogui.moveTo(x, y, 0.5)
        pyautogui.click()
        self.waitRandomizedTime(9,10)

    def leave_dungeon(self):
        x, y = self.find_pos(self.leave_combat, 0.9, self.method)
        pyautogui.moveTo(x,y,0.5)
        pyautogui.click()
        self.waitRandomizedTime(1,2)
        x, y = self.wincap.get_screen_position((600, 400))
        pyautogui.moveTo(x,y,0.5)
        pyautogui.click()
        self.waitRandomizedTime(15,16)

    def enemy_rectangles(self, objects):
        enemies = ['enemy', 'enemygroup', 'miniboss', 'goldroomenemychest', 'goldroomenemytooki']
        enemylist = []

        for enemy in enemies:
            for key, value in objects.items():
                if enemy ==  key:
                    for item in value:
                        x1, y1, x2, y2 = item[0], item[1], item[2], item[3]
                        enemylist.append((x1,y1,x2,y2))

        return enemylist

    def portal_rectangles(self, objects):
        portals = ['stage2portal', 'stage3portal']
        portal_list = []

        for portal in portals:
            for key, value in objects.items():
                if portal == key:
                    for item in value:
                        x1, y1, x2, y2 = item[0], item[1], item[2], item[3]
                        portal_list.append((x1,y1,x2,y2))
        
        return portal_list

    def compute(self, objects):
        portals = ['stage2portal', 'stage3portal']
        if portals[0] in objects.keys() or portals[1] in objects.keys():
            for portal in portals:
                for key, val in .items():
                    




    def update_targets(self, targets):
        self.lock.acquire()
        self.targets = targets
        self.lock.release()

    def update_screenshot(self, screenshot):
        self.lock.acquire()
        self.screenshot = screenshot
        self.lock.release()

    def start(self):
        self.stopped = False
        t = Thread(target = self.run)
        t.start()

    def stop(self):
        self.stopped = True
    
    def run(self):
        while not self.stopped:
            if self.state == BotState.INITIALIZING:
                # do no actions until the startup waiting period is complete
                if time() > self.timestamp + self.INITIALIZING_SECONDS:
                    # start searching when the waiting period is over
                    self.lock.acquire()
                    self.state = BotState.IN_CITY
                    self.lock.release()

            elif self.state == BotState.IN_CITY:
                # check if armor needs repairing
                self.check_repair()
                if self.need_repair == True:
                    self.repair_gear()

                # assumes player is already next to a dungeon monument
                self.initialize_dungeon()
                self.lock.acquire()
                self.state = BotState.IN_DUNGEON
                self.lock.release()

            elif self.state == BotState.IN_DUNGEON:
                # bot actions
                pass
                # first fire weapon to trigger spawn
                if self.dungeon_begin == True:
                    self.dungeon_begin = False
                    self.waitRandomizedTime(2,4)
                    pyautogui.hotkey('c')

                # scan, if no enemies, cast while waiting/scannning
                # first check map for enemies, then check minimap for enemy dots if no enemies
                # for enemies on map, just walk to their position, wait 1 second, then cast/attack
                # if checking minimap, must determine which quadrant enemy dot is
                # take the difference  in x, y values in minimap and apply it to 
                # the center of the screen x 3
                # click, move, wait, attack
                # while happening, same logic is applied to stage1/2 portal
                # prioritize portal over enemies
                

                # leave dungeon
                if self.time_to_leave == True:
                    self.leave_dungeon()
                    self.lock.acquire()
                    self.state = BotState.IN_CITY
                    self.lock.release()