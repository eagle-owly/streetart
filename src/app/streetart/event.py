from enum import Enum


class Event(Enum):
    PAGE_OPEN = 1
    VIDEO_SHOWN = 2
    VIDEO_REJECTED = 3
    VIDEO_UNSUPPORTED = 4
    VIDEO_LOADED = 5
    VIDEO_ERROR = 6
    INSTAGRAM_CLICK = 7
    WINDOW_FOCUS = 8
    WINDOW_BLUR = 9
