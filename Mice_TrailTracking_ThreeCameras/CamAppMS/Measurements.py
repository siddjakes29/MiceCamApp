'''
Created on April 19th, 2018

@author:Hao modified by Sid/J 
'''
from ScopeFoundry import Measurement
from ScopeFoundry.measurement import MeasurementQThread
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
from ScopeFoundry import h5_io
import pyqtgraph as pg
import numpy as np
from scipy import ndimage
import time
import PySpin
from qtpy import QtCore
from qtpy.QtCore import QObject
import os
import queue

class SubMeasurementQThread(MeasurementQThread):

    def __init__(self, run_func, parent=None):
        super(MeasurementQThread, self).__init__(parent)
        self.run_func = run_func
        self.interrupted = False
  
    def run(self):
        while not self.interrupted:
            self.run_func()
            if self.interrupted:
                break
            
    @QtCore.Slot()
    def interrupt(self):
        self.interrupted = True
        
class MiceTrack(Measurement):
    
    # this is the name of the measurement that ScopeFoundry uses 
    # when displaying your measurement and saving data related to it    
    name = "Tracking"
    interrupt_subthread = QtCore.Signal(())
    
    def setup(self):
        """
        Runs once during App initialization.
        This is the place to load a user interface file,
        define settings, and set up data structures. 
        """
        
        # Define ui file to be used as a graphical interface
        # This file can be edited graphically with Qt Creator
        # sibling_path function allows python to find a file in the same folder
        # as this python module
        self.ui_filename = sibling_path(__file__, "Mice_Track.ui")
        
        #Load ui file and convert it to a live QWidget of the user interface
        self.ui = load_qt_ui_file(self.ui_filename)

        # Measurement Specific Settings
        # This setting allows the option to save data to an h5 data file during a run
        # All settings are automatically added to the Microscope user interface
        self.settings.New('save_h5', dtype=bool, initial=True)
        self.settings.New('save_video', dtype = bool, initial = True)
        
        # Define how often to update display during a run
        self.display_update_period = 0.005
        
        # Convenient reference to the hardware used in the measurement
        self.Front_cam = self.app.hardware['Front_cam']
        self.Top_cam = self.app.hardware['Top_cam']
        #self.Side_cam = self.app.hardware['Side_cam']
        self.Recorder = self.app.hardware['Recorder']
        
        #setup experiment condition
        self.Front_cam.settings.frame_rate.update_value(30)
        #self.Side_cam.settings.frame_rate.update_value(30)
        self.Top_cam.settings.frame_rate.update_value(30)
        self.Front_cam.read_from_hardware()
        self.Top_cam.read_from_hardware()
        #self.Side_cam.read_from_hardware()
        
    def setup_figure(self):
        """
        Runs once during App initialization, after setup()
        This is the place to make all graphical interface initializations,
        build plots, etc.
        """
        
        # connect ui widgets to measurement/hardware settings or functions
        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)
        
        # Set up pyqtgraph graph_layout in the UI
        self.Top_cam_layout=pg.GraphicsLayoutWidget()
        self.Front_cam_layout=pg.GraphicsLayoutWidget()
        #self.Side_cam_layout=pg.GraphicsLayoutWidget()
        self.ui.Top_cam_groupBox.layout().addWidget(self.Top_cam_layout)
        self.ui.Front_cam_groupBox.layout().addWidget(self.Front_cam_layout)
        #self.ui.Side_cam_groupBox.layout().addWidget(self.Side_cam_layout)
        
        #create camera image graphs
        self.Top_cam_view=pg.ViewBox()
        self.Top_cam_layout.addItem(self.Top_cam_view)
        self.Top_cam_image=pg.ImageItem()
        self.Top_cam_view.addItem(self.Top_cam_image)
        
        self.Front_cam_view=pg.ViewBox()
        self.Front_cam_layout.addItem(self.Front_cam_view)
        self.Front_cam_image=pg.ImageItem()
        self.Front_cam_view.addItem(self.Front_cam_image)
        
        #self.Side_cam_view=pg.ViewBox()
        #self.Side_cam_layout.addItem(self.Side_cam_view)
        #self.Side_cam_image=pg.ImageItem()
        #self.Side_cam_view.addItem(self.Side_cam_image)
        
    def update_display(self):
        """
        Displays (plots) the numpy array self.buffer. 
        This function runs repeatedly and automatically during the measurement run.
        its update frequency is defined by self.display_update_period
        """
        
    def run(self):
        
        """
        Runs when measurement is started. Runs in a separate thread from GUI.
        It should not update the graphical interface directly, and should only
        focus on data acquisition.
        """
        
        # first, create a data file
#         if self.settings['save_h5']:
#             # if enabled will create an HDF5 file with the plotted data
#             # first we create an H5 file (by default autosaved to app.settings['save_dir']
#             # This stores all the hardware and app meta-data in the H5 file
#             self.h5file = h5_io.h5_base_file(app=self.app, measurement=self)
#             
#             # create a measurement H5 group (folder) within self.h5file
#             # This stores all the measurement meta-data in this group
#             self.h5_group = h5_io.h5_create_measurement_group(measurement=self, h5group=self.h5file)
#             
#             # create an h5 dataset to store the data
#             self.buffer_h5 = self.h5_group.create_dataset(name  = 'buffer', 
#                                                           shape = self.buffer.shape,
#                                                           dtype = self.buffer.dtype)
        
        # We use a try/final block, so that if anything goes wrong during a measurement,
        # the final block can clean things up, e.g. close the data file object.
        #self.Side_cam._dev.set_buffer_count(500)
        self.Front_cam._dev.set_buffer_count(500)
        self.Top_cam._dev.set_buffer_count(500)
        print(self.Front_cam._dev.get_buffer_count())
        if self.settings.save_video.value():
            #self.Side_cam._dev.recording = True
            self.Front_cam._dev.recording = True
            self.Top_cam._dev.recording = True
            save_dir = self.app.settings.save_dir.value()
            data_path = os.path.join(save_dir,self.app.settings.sample.value())
            try:
                os.makedirs(data_path)
            except OSError:
                print('directory already exist, writing to existing directory')
            
            self.Recorder.settings.path.update_value(data_path)
        
            frame_rate = self.Top_cam.settings.frame_rate.value()
            frame_rate = self.Front_cam.settings.frame_rate.value()
            self.Recorder.create_file('Front_mov',frame_rate)
            self.Recorder.create_file('Top_mov',frame_rate)
            #self.Recorder.create_file('Side_mov',frame_rate)
            
            self.rec_thread = SubMeasurementQThread(self.record_frame)
            self.interrupt_subthread.connect(self.rec_thread.interrupt)
        
        
        
        self.Front_output_queue = queue.Queue(1000)
        self.Front_disp_queue = queue.Queue(1000)
        self.Top_disp_queue = queue.Queue(1000)
        
        try:
            self.i = 0
            self.Front_cam.config_event(self.Front_repeat)
            self.Top_cam.config_event(self.Top_repeat)
            
            if self.settings.save_video.value():
                self.rec_thread.start()
            
            #self.Side_cam.start()
            self.Front_cam.start()
            self.Top_cam.start()
            # Will run forever until interrupt is called.
            while not self.interrupt_measurement_called:
                time.sleep(0.5)
                
                if self.interrupt_measurement_called:
                    # Listen for interrupt_measurement_called flag.
                    # This is critical to do, if you don't the measurement will never stop.
                    # The interrupt button is a polite request to the 
                    # Measurement thread. We must periodically check for
                    # an interrupt request
                    self.interrupt_subthread.emit()
                    break
        finally:
            
            self.Front_cam.stop()
            self.Top_cam.stop()
            #self.Side_cam.stop()
            self.Front_cam.remove_event()
            self.Top_cam.remove_event()
            #self.Side_cam.remove_event()

            if self.settings.save_video.value():
                self.rec_thread.terminate()
                del self.rec_thread
                self.Recorder.close()
                self.Front_cam._dev.recording = False
                self.Top_cam._dev.recording = False
                #self.Side_cam._dev.recording = False
            
            #self.comp_thread.terminate()
            #del self.comp_thread
            del self.Front_disp_queue
            del self.Top_disp_queue
            del self.Front_output_queue
            #del self.Side_output_queue
            
  
    def Front_repeat(self):
        pass
            
    def Top_repeat(self):
        pass
    
        #def Side_repeat(self):
    #    pass
          
    def record_frame(self):
        if self.settings.save_video.value():
            self.Recorder.save_frame('Front_mov',self.Front_cam._dev.read_record_frame())
            self.Recorder.save_frame('Top_mov',self.Top_cam._dev.read_record_frame())
            #self.recorder.save_frame('Side_mov',self.Side_cam._dev.read_record_frame())