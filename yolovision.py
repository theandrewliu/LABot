import torch
from threading import Thread, Lock

class YoloVision():

    # threading properties
    stopped = True
    lock = None
    objects = {}
    # properties
    screenshot = None
    model = None
    results = None


    # implements the Yolov5 model to make inferences on window

    # constructor
    def __init__(self):
        # create a thread lock object
        self.lock = Lock()
        # load the model
        self.model = self.load_model()
        self.classes = self.model.names
        # display which device is being used when running the model detector
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print("Using Device: ", self.device)

    def update(self, screenshot):
        self.lock.acquire()
        self.screenshot = screenshot
        self.lock.release()

    def load_model(self):
        # loads the given yolov5 model from pytorch hub
        # and returns a trained model
        return torch.hub.load('yolov5', 'custom', path = "best.pt", source = 'local')

    def grade_image(self):
        # takes a single frame or image as input and scores it using the yolov5 model.
        # input the frame as numpy/list/tuple format
        # returns the labels and coordinates of objects detected in image
        self.model.to(self.device)
        image = [self.screenshot]
        results = self.model(image)
        labels, coord = results.xyxyn[0][:, -1], results.xyxyn[0][:,:-1]
        return labels, coord
    
    def label_class(self, class_num):
        # given a label value from the trained yolov5 model, return the string label 
        # associated with it
        return self.classes[int(class_num)]

    def get_objects(self):
        # takes the results of the graded image and sorts them into a dictionary
        # with key = class name and value = list of coordinates. 
        # will only sort if confidence value is above a certain confidence
        # returns the dictionary with key value pairs
        self.model.to(self.device)
        image = [self.screenshot]
        results = self.model(image)
        labels, coord = results.xyxyn[0][:, -1], results.xyxyn[0][:,:-1]

        n = len(labels)
        x_shape, y_shape = self.screenshot.shape[1], self.screenshot.shape[0]
        objectdict = {}
        for i in range(n):
            points = []
            row = coord[i]
            # here confidence is 0.3
            if row[4] >= 0.3:
                x1, y1, x2, y2 = int(row[0]*x_shape), int(row[1]*y_shape), int(row[2]*x_shape), int(row[3]*y_shape)
                points = [x1, y1, x2, y2]
                label = self.label_class(labels[i])
                if label not in objectdict:
                    objectdict[label] = []
                objectdict[label].append(points)
        # debug
        # print(objectdict)
        return objectdict
        # should be returned like: {"enemy":[[points][morepoints]], "portal":[points]}

    def start(self):
        self.stopped = False
        t = Thread(target = self.run)
        t.start()
    
    def stop(self):
        self.stopped = True
    
    def run(self):
        while not self.stopped:
            if self.screenshot is not None:
                # do object detection
                objects = self.get_objects()
                # lock the thread while updating the results
                self.lock.acquire()
                self.objects = objects
                self.lock.release()
