'''
Created on April 19, 2018

@author: Sid/J 
'''

from ScopeFoundry.base_app import BaseMicroscopeApp
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
import logging

logging.basicConfig(level=logging.INFO)

# Define your App that inherits from BaseMicroscopeApp
class CamApp(BaseMicroscopeApp):
    
    # this is the name of the microscope that ScopeFoundry uses 
    # when displaying your app and saving data related to it    
    name = 'MiceTracking'

    # You must define a setup() function that adds all the 
    # capabilities of the microscope and sets default settings    
    def setup(self):

        #Add App wide settings
        #self.settings.New('test1', dtype=int, initial=0)
        
        #Add hardware components
        print("Adding Hardware Components")
        from CamAppHW.flircam.flircam_hw import FLIRCamHW
        Front_cam = FLIRCamHW(self)
        Front_cam.settings.camera_sn.update_value('17550014')
        Front_cam.name = 'Front_cam'
        Top_cam = FLIRCamHW(self)
        Top_cam.settings.camera_sn.update_value('16307752')
        Top_cam.name = 'Top_cam'
        #Side_cam = FLIRCamHW(self)
        #Side_cam.settings.camera_sn.update_value('15420264')
        #Side_cam.name = 'Side_cam'
        self.add_hardware(Top_cam)
        self.add_hardware(Front_cam)
        #self.add_hardware(Side_cam)
        
        from CamAppHW.flircam.flirrec_hw import FLIRRecHW
        self.add_hardware(FLIRRecHW(self))
               
        #Add Measurement components
        print("Create Measurement objects")
        from CamAppMS.Measurements import MiceTrack
        self.add_measurement(MiceTrack(self))
        
        # Connect to custom gui
        
        # load side panel UI
        
        # show ui
        self.ui.show()
        self.ui.activateWindow()
        
        # load side panel UI        
        #quickbar_ui_filename = sibling_path(__file__, "quickbar.ui")        
        #self.add_quickbar( load_qt_ui_file(quickbar_ui_filename) )
        
        # Connect quickbar ui elements to settings
        # self.quickbar.foo_pushButton.connect(self.on_foo)
        
        # load default settings from file
        #self.settings_load_ini(sibling_path(__file__, "defaults.ini"))
        
if __name__ == '__main__':
    
    import sys
    app = CamApp(sys.argv)
    
    app.hardware['Front_cam'].connected.update_value(True)
    app.hardware['Top_cam'].connected.update_value(True)
    app.hardware['Recorder'].connected.update_value(True)
    #app.hardware['Side_cam'].connected.update_value(True)
    #app.hardware['daq_timer'].connected.update_value(True)
    
    sys.exit(app.exec_())
    