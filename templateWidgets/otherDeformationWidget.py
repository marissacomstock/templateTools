#********************************************************************************************************************************
# $Id: otherDeformationWidget.py 52150 2017-03-09 20:36:19Z marissa $
#*******************************************************************************

import os, sys, re
import pymel.core as pm
from tip.qt.pkg import QtCore, QtGui, uic

from tip.maya.studio.core import *
from tip.maya.puppet.utils.decorators import undoable
from tip.maya.puppet.tools.templateTools.templateSystems import digitSystem
from tip.maya.puppet.tools.templateTools.templateSystems import ikNeckSystem
from tip.maya.puppet.tools.templateTools.templateSystems import tailTentacleSystem

FILEPATH = os.path.dirname(__file__).replace('templateWidgets', 'templateUIs')
__dialogs = list()

form_class, base_class = uic.loadUiType(os.path.join(FILEPATH, "otherDeformationWidget.ui"))


class OtherDeformationWidget(form_class, base_class):

    closeSignal = QtCore.Signal()
    refreshSignal = QtCore.Signal()

    def __init__(self):
        super(OtherDeformationWidget, self).__init__()
        self.setupUi(self)
        self.setObjectName('otherDeformationTool')
        self.setWindowTitle('Other Deformation Tool')

        #ikNeck
        self.neckJnt_pushButton.clicked.connect(self.assignObject)
        self.headJnt_pushButton.clicked.connect(self.assignObject)
        self.ikNeckSystem_pushButton.clicked.connect(self.assignObject)
        #foot and hand System
        self.handFoot_pushButton.clicked.connect(self.assignObject)
        self.createHandFoot_pushButton.clicked.connect(self.assignObject)
        #tail/Tentacle System
        self.createTailSystem_pushButton.clicked.connect(self.assignObject)

    def assignObject(self):

        sender = self.sender()

        #checkboxes
        if sender is self.neckJnt_pushButton:
            sel = pm.ls(selection=True)
            if sel:
                self.neckJnt_lineEdit.setText(str(sel[0]))
        elif sender is self.headJnt_pushButton:
            sel = pm.ls(selection=True)
            if sel:
                self.headJnt_lineEdit.setText(str(sel[0]))
        elif sender is self.ikNeckSystem_pushButton:
            self.create_neckIkSystem()
        elif sender is self.handFoot_pushButton:
            sel = pm.ls(selection=True)
            if sel:
                self.handFoot_lineEdit.setText(str(sel[0]))
        elif sender is self.createHandFoot_pushButton:
            self.create_digitSystem()
        elif sender is self.createTailSystem_pushButton:
            self.create_tentacleSystem()

    @undoable
    def create_tentacleSystem(self):
        jnt = pm.ls(selection=True)
        if not jnt:
            pm.error('Select a joint to create system')

        numFollicles = self.numFollicle_spinBox.value()
        name = self.name_lineEdit.text()
        if self.center_radioButton.isChecked():
            side = None
        elif self.left_radioButton.isChecked():
            side = 'left'
        else:
            side = 'right'

        if name:
            TipName = naming.TipName(base=name, side=side, suffix='bnd')
        else:
            TipName = naming.TipName(name=jnt[0])

        tailTentacleSystem.TailTentacleSystem(startJnt=jnt[0],
                                              name=TipName,
                                              numFollicles=numFollicles,
                                              muscle=False,
                                              slide=False,
                                              wave=False,
                                              scale=False)

    #@undoable
    def create_digitSystem(self):
        controls = self.handFoot_checkBox.isChecked()
        rootJnt = pm.PyNode(self.handFoot_lineEdit.text())
        digitSystem.DigitSystem(rootJnt, controls=controls)

    @undoable
    def create_neckIkSystem(self):
        try:
            neckJnt = pm.PyNode(self.neckJnt_lineEdit.text())
            headJnt = pm.PyNode(self.headJnt_lineEdit.text())
            neckEnd = pm.PyNode(naming.TipName(name=neckJnt, index='end'))
            headEnd = pm.PyNode(naming.TipName(name=headJnt, index='end'))

        except error.ArgumentError, err:
            raise error.ArgumentError, err

        except error.MayaNodeError, err:
            raise error.MayaNodeError, err

        ikNeckSystem.IkNeckSystem(neck=neckJnt,
                                             neckEnd=neckEnd,
                                             head=headJnt,
                                             headEnd=headEnd)


