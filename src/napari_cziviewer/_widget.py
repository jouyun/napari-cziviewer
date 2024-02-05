from typing import TYPE_CHECKING

from magicgui import magic_factory
from qtpy.QtWidgets import QHBoxLayout, QPushButton, QWidget, QLineEdit, QVBoxLayout, QFrame, QLabel, QRadioButton
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
from ._cziviewer import CziViewer

if TYPE_CHECKING:
    import napari
    
class CziViewerWidget(QWidget):
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer
        self.root_directory = ''
        self.cziviewer = CziViewer(self.viewer)

        #self.figure = Figure()

        # Create the buttons
        self.load_overview_btn = QPushButton("Load Overview")
        self.load_overview_btn.clicked.connect(self._load_overview_click)

        self.load_zoom_btn = QPushButton("Load Zoom Image(s)")
        self.load_zoom_btn.clicked.connect(self._load_zoom_click)

        self.center_zoom_btn = QPushButton("Center Zoom on Selected Layer")
        self.center_zoom_btn.clicked.connect(self._center_zoom_click)

        self.zoomed_layer_btn = QPushButton("Select Zoomed Layer")
        self.zoomed_layer_btn.clicked.connect(self._select_zoomed_layer)
        
        # Create the radio button
        self.composite_radio_btn = QRadioButton("Load Zoom as Composite", )
        self.composite_radio_btn.setChecked(True)
        
        # Create the user editable textbox
        self.label = QLabel("Name for zoom image (defaults to filename)")
        self.name_textbox = QLineEdit(self)
        self.name_textbox.move(20, 20)
        self.name_textbox.resize(280,40)
        
        # Create the order of the layout
        layout = QVBoxLayout()
        layout.addWidget(self.load_overview_btn)
        layout.addSpacing(200)  # Separate loading the overview from all of the zoom image functionality
        layout.addWidget(self.label)
        layout.addWidget(self.name_textbox)
        layout.addWidget(self.composite_radio_btn)
        layout.addWidget(self.load_zoom_btn)
        layout.addWidget(self.center_zoom_btn)
        layout.addWidget(self.zoomed_layer_btn)

        # Finish the layout
        self.setLayout(layout)
        
    def _load_overview_click(self):
        # Open a file dialog
        file_dialog = QFileDialog()
        
        # Get the selected file
        file_name, _ = file_dialog.getOpenFileName(self, "Open file", "", "All Files (*)")

        if file_name:
            print(f"Selected file: {file_name}")
            self.cziviewer.load_overview(file_name)
        else:
            print("No file selected")    

    def _load_zoom_click(self):
        # Open a file dialog
        file_dialog = QFileDialog()
        
        # Get the selected files
        file_names, _ = file_dialog.getOpenFileNames(self, "Open files", "", "All Files (*)")

        print(len(file_names))
        if file_names:
            if (len(file_names) == 1):
                print(f"Selected file: {file_names[0]}")
                self.cziviewer.load_zoom(file_names[0], name=self.name_textbox.text(), composite=self.composite_radio_btn.isChecked())
            else:
                for file_name in file_names:
                    print(f"Selected file: {file_name}")
                    #self.cziviewer.load_zoom(file_name, composite=self.composite_radio_btn.isChecked())
                    self.cziviewer.load_zoom(file_name, composite=False)
        else:
            print("No files selected")       

    def _center_zoom_click(self):
        current_layer = self.viewer.layers.selection.active.name
        self.cziviewer.focus_on(self.viewer.layers[current_layer]) 

    def _select_zoomed_layer(self):
        self.cziviewer.select_on()