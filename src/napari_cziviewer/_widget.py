from typing import TYPE_CHECKING

from magicgui import magic_factory
from qtpy.QtWidgets import QHBoxLayout, QPushButton, QWidget, QLineEdit, QVBoxLayout, QFrame, QLabel
import numpy as np
import skimage.util as util
import tifffile
import skimage.data as data
import os
import time
import glob
import tifffile
from matplotlib.figure import Figure
from qtpy.QtCore import Qt
from matplotlib.widgets import LassoSelector, RectangleSelector, SpanSelector
from matplotlib.path import Path
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import pandas as pd
from qtpy.QtWidgets import QComboBox, QCompleter
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QListWidget
from qtpy.QtWidgets import QFileDialog

if TYPE_CHECKING:
    import napari
    
class CziViewerWidget(QWidget):
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer
        self.root_directory = ''

        self.figure = Figure()

        # Create the buttons
        self.initialize_btn = QPushButton("Initialize")
        self.initialize_btn.clicked.connect(self._initialize_click)
        
        layout = QVBoxLayout()
        layout.addWidget(self.initialize_btn)

        # Finish the layout
        self.setLayout(layout)
        
    def _initialize_click(self):
        print("hi bobo")        