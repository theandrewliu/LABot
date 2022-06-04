import cv2 as cv
import numpy as np

class Vision:
    minimap = ['bossicon','enemy_icon','goldenemyicon','minibossicon','portalicon','riftcoreicon','playericon']
    screen = ['player','goldportal','riftcore']
    
    # given a dictionary of key names and point values of 
    # {"enemy":[[x1,y1,x2,y2][x1,y1,x2,y2]], "portal":[x1,y1,x2,y2]}
    # convert the dictionary into center points where we can click.
    def get_click_points(self, rectangles):
        points = []

        for (x1, y1, x2, y2) in rectangles:
            center_x = x2 - x1
            center_y = y2 - y1
            points.append((center_x, center_y))
        
        return points


    def draw_rectangles(self, screenshot, objects):
        # these colors are actually BGR
        line_color = (0, 255, 0)
        line_type = cv.LINE_4

        for key,value in objects.items():
            for item in value:
                top_left = (item[0],item[1])
                bottom_right = (item[2],item[3])
                # draw the box
                cv.rectangle(screenshot, top_left, bottom_right, line_color, lineType=line_type)
                # attach label
                cv.putText(screenshot, key, top_left, cv.FONT_HERSHEY_SIMPLEX, 0.5, line_color, 1)
        
        return screenshot

