import os
import sys
import comtypes.client
from config import *
import utils

if __name__ == "__main__":
    dosyaadi = input("Dosya adı girin: ")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    APIPath = os.path.join(current_dir, "examples")
    
    if not os.path.exists(APIPath + os.sep + dosyaadi):
        try:
            os.makedirs(APIPath + os.sep + dosyaadi)
        except OSError:
            pass
    ModelPath = APIPath + os.sep + dosyaadi + os.sep + dosyaadi + ".edb"
    
    # set the following flag to True to attach to an existing instance of the program
    # otherwise a new instance of the program will be started
    AttachToInstance = False
    
    # set the following flag to True to manually specify the path to ETABS.exe
    # this allows for a connection to a version of ETABS other than the latest installation
    # otherwise the latest installed version of ETABS will be launched
    SpecifyPath = False
    
    # if the above flag is set to True, specify the path to ETABS below
    ProgramPath = r'C:\Program Files\Computers and Structures\ETABS 21\ETABS.exe'
    
    
    # create API helper object
    helper = comtypes.client.CreateObject('CSiAPIv1.Helper')
    helper = helper.QueryInterface(comtypes.gen.CSiAPIv1.cHelper)
    if AttachToInstance:
        #attach to a running instance of ETABS
        try:
            #get the active ETABS object
            myETABSObject = helper.GetObject("CSI.ETABS.API.ETABSObject")
        except (OSError, comtypes.COMError):
            print("No running instance of the program found or failed to attach.")
            sys.exit(-1)
    else:
        if not SpecifyPath:
            try:
                # create an instance of the ETABS object from the latest installed ETABS
                myETABSObject = helper.CreateObjectProgID("CSI.ETABS.API.ETABSObject")
            except (OSError, comtypes.COMError):
                print("Cannot start a new instance of the program.")
                sys.exit(-1)
        else:
            try:
                # 'create an instance of the ETABS object from the specified path
                myETABSObject = helper.CreateObject(ProgramPath)
            except (OSError, comtypes.COMError):
                print("Cannot start a new instance of the program from " + ProgramPath)
                sys.exit(-1)
    
    # start ETABS application
    ret = myETABSObject.ApplicationStart()
    
    # create SapModel object
    SapModel = myETABSObject.SapModel
    
    # initialize model
    ret = SapModel.InitializeNewModel(eUnits)
    
    # Create Grid
    utils.Grid(SapModel, hm, h, axe, l, axel)
    SapModel.File.Save(ModelPath)
    
    
