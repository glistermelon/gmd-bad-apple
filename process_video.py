import cv2
import numpy
import itertools

class Run():
    def __init__(self, x, y, len):
        self.x = x
        self.y = y
        self.len = len

def get_frames(video_file_name : str):

    video = cv2.VideoCapture(video_file_name)
    while not video.isOpened():
        pass

    frame_runs = []
    success, frame = video.read()
    i = 0

    last = None
    WHITE = 0
    BLACK = 1
    inverts = 0

    while (success):

        frame = cv2.threshold(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), 128, 255, cv2.THRESH_BINARY)[1]

        print(i, "frames,", inverts, "inverts", end = '\r')
        i += 1

        rows = numpy.ndarray.tolist(frame)
        w_runs = []
        b_runs = []
        cum_y = 0
        for row in rows:
            cum_x = 0
            for px, group in itertools.groupby(row):
                run = len(list(group))
                if px:
                    # add a rectangle with left-most pixel at (cum_x, cum_y) and width 'run'
                    # center aligned
                    w_runs.append(Run(cum_x + run / 2, cum_y, run))
                else:
                    b_runs.append(Run(cum_x + run / 2, cum_y, run))
                cum_x += run
            cum_y += 1
        if len(w_runs) < len(b_runs):
            frame_runs.append({
                "invert": last == BLACK,
                "runs": w_runs
            })
            if last == BLACK:
                inverts += 1
            last = WHITE
        else:
            frame_runs.append({
                "invert": last == WHITE,
                "runs": b_runs
            })
            if last == WHITE:
                inverts += 1
            last = BLACK

        success, frame = video.read()
    
    print('\n')
    
    return frame_runs