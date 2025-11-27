from abc import ABC, abstractmethod
from PIL import Image


class IOController(ABC):
    """
    Abstract base class representing the hardware device interface.
    This matches the Adafruit 1.3" Color TFT Bonnet with 240x240 display and 7 buttons.
    """

    def __init__(self):
        # Button event callbacks
        self.on_up = lambda: None
        self.on_down = lambda: None
        self.on_left = lambda: None
        self.on_right = lambda: None
        self.on_center = lambda: None
        self.on_a = lambda: None
        self.on_b = lambda: None

    @abstractmethod
    def draw(self, img: Image.Image):
        """
        Display an image on the device.

        Args:
            img: PIL Image object, must be 240x240 pixels
        """
        pass
