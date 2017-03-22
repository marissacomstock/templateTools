#********************************************************************************************************************************
# $Id$
# TEMPLATE TOOLS:
# Marissa
# _________________________________________________________________________
# == DESCRIPTION ==========================================================
# This tool deals with all the systems associated with the template file of our puppets.
# It automates the different deformation systems.
# _________________________________________________________________________
# == HOW TO ===============================================================
# TWIST JOINT SYSTEM:
# POLE VECTOR SYSTEM
# FACE SYSTEM
# Eye Rig:
# Lip Rig:
# Face Rig:
# SPINE AND KNEE SYSTEM:
# Spine Shapes:
# Knee Rig:
# _________________________________________________________________________
# == TO DO ================================================================
# Get script to work with different anim layers.
# Get script to work with smart bake so each frame not keyed
# _________________________________________________________________________
# == VERSIONS =============================================================
# 2.0 Template Tools
# *******************************************************************************

from tip.maya.puppet.qt import mayaQtUi
from tip.maya.puppet.tools.templateTools.templateWidgets import poleVectorWidget
from tip.maya.puppet.tools.templateTools.templateWidgets import twistWidget
from tip.maya.puppet.tools.templateTools.templateWidgets import faceWidget
from tip.maya.puppet.tools.templateTools.templateWidgets import otherDeformationWidget
from tip.qt.pkg import QtCore, QtGui, uic

import maya.cmds

from tip.qt.pkg import QtCore, QtGui, uic

MAYA_WINDOW = mayaQtUi.getMayaMainWindow()

class TabTemplateWindow(QtGui.QDialog):
    def __init__(self, parent = MAYA_WINDOW):
        super(TabTemplateWindow, self).__init__(parent)
        self.layout = QtGui.QFormLayout()
        self.setLayout(self.layout)
        self.setObjectName('thetemplateWindow')

        self.setWindowTitle("Template Tools")
        self.setMinimumSize(500, 500)
        self.setMaximumSize(500, 500)

        self.tabWidget = QtGui.QTabWidget()
        self.layout.addWidget(self.tabWidget)

        twWindow = twistWidget.TwistWidget()
        pvWindow = poleVectorWidget.PoleVectorWidget()
        fWindow = faceWidget.FaceWidget()
        skWindow = otherDeformationWidget.OtherDeformationWidget()

        self.tabWidget.addTab(twWindow, "Twist System")
        self.tabWidget.addTab(pvWindow, "Pole Vector System")
        self.tabWidget.addTab(fWindow, "Face System")
        self.tabWidget.addTab(skWindow, "Other Deformation Systems")

        screenWidth, screenHeight = self.screenCenter()
        self.move(QtCore.QPoint(screenWidth, screenHeight))

    def screenCenter(self):
        resolution = QtGui.QDesktopWidget().screenGeometry()
        width = (resolution.width() / 2) - (self.frameSize().width() / 2)
        height = (resolution.height() / 2) - (self.frameSize().height() / 2)
        return width, height

def loadTabTemplateWindow():
    ''' Create and show a corrective utility window.  Works in maya 2009+. '''

    if maya.cmds.about(apiVersion=True) >= 201100:

        dialog = mayaQtUi.getMayaWindow('thetemplateWindow')

        if not dialog:
            # global __dialogs
            dialog = TabTemplateWindow()
            dialog.show()
        else:
            dialog.showNormal()
            dialog.raise_()

    else:
        import tip.maya.qtBridge
        tip.maya.qtBridge.init()



