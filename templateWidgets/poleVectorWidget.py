#********************************************************************************************************************************
# $Id: poleVectorWidget.py 52150 2017-03-09 20:36:19Z marissa $
#*******************************************************************************

import os, sys, re
import pymel.core as pm
from tip.qt.pkg import QtCore, QtGui, uic

from tip.maya.studio.core import *
from tip.maya.puppet.utils.decorators import undoable
from tip.maya.puppet.tools.templateTools.templateSystems import poleVectorSystem

FILEPATH = os.path.dirname(__file__).replace('templateWidgets', 'templateUIs')
__dialogs = list()

form_class, base_class = uic.loadUiType(os.path.join(FILEPATH, "poleVectorWidget.ui"))


class PoleVectorWidget(form_class, base_class):

    closeSignal = QtCore.Signal()
    refreshSignal = QtCore.Signal()

    def __init__(self):
        super(PoleVectorWidget, self).__init__()
        self.setupUi(self)
        self.setObjectName('poleVectorTool')
        self.setWindowTitle('Pole Vector Tool')

        self.reset()

        #check boxes
        self.all_checkBox.clicked.connect(self.assignObject)
        self.armLf_checkBox.clicked.connect(self.assignObject)
        self.armRt_checkBox.clicked.connect(self.assignObject)
        self.legLf_checkBox.clicked.connect(self.assignObject)
        self.legRt_checkBox.clicked.connect(self.assignObject)
        #load buttons
        self.startJoint_pushButton.clicked.connect(self.assignObject)
        self.endJoint_pushButton.clicked.connect(self.assignObject)
        #execute buttons
        self.create_pushButton.clicked.connect(self.assignObject)
        self.delete_pushButton.clicked.connect(self.assignObject)
        self.reset_pushButton.clicked.connect(self.assignObject)


    def assignObject(self):

        sender = self.sender()

        #checkboxes
        if sender is self.all_checkBox:
            self.uncheck_indivBoxes()
        elif sender is self.armLf_checkBox:
            self.all_checkBox.setChecked(False)
        elif sender is self.armRt_checkBox:
            self.all_checkBox.setChecked(False)
        elif sender is self.legLf_checkBox:
            self.all_checkBox.setChecked(False)
        elif sender is self.legRt_checkBox:
            self.all_checkBox.setChecked(False)

        #load buttons
        elif sender is self.startJoint_pushButton:
            self.loadSelection(self.startJoint_lineEdit)
        elif sender is self.endJoint_pushButton:
            self.loadSelection(self.endJoint_lineEdit)

        #execute buttons
        elif sender is self.create_pushButton:
            self.create()
        elif sender is self.delete_pushButton:
            self.delete()
        elif sender is self.reset_pushButton:
            self.reset()


    def reset(self):
        self.all_checkBox.setChecked(True)
        self.controlOffset_doubleSpinBox.setValue(10)
        self.sizeOfControl_doubleSpinBox.setValue(1)
        self.customSysName_lineEdit.clear()
        self.startJoint_lineEdit.clear()
        self.endJoint_lineEdit.clear()
        self.uncheck_indivBoxes()


    def uncheck_indivBoxes(self):
        self.armLf_checkBox.setChecked(False)
        self.armRt_checkBox.setChecked(False)
        self.legLf_checkBox.setChecked(False)
        self.legRt_checkBox.setChecked(False)


    def loadSelection(self, lineEdit):
        try:
            sel = pm.ls(selection=True)
            lineEdit.setText(checks.pyNodeToString(sel[0]))
        except IndexError, TypeError:
            pm.error("Select one joint")

    @undoable
    def create(self):
        if self.all_checkBox.isChecked():
            armLf = True
            armRt = True
            legLf = True
            legRt = True
        else:
            armLf = self.armLf_checkBox.isChecked()
            armRt = self.armRt_checkBox.isChecked()
            legLf = self.legLf_checkBox.isChecked()
            legRt = self.legRt_checkBox.isChecked()

        if armLf:
            #check to make sure joints in scene or system doesn't already exist
            exists = self.checkScene('arm', 'armJALf_bnd', 'handJBLf_bnd', 'armJBLf_bnd')

            if not exists:
                poleVectorSystem.PoleVectorSystem(base='arm',
                                                  startJoint='armJALf_bnd',
                                                  lastJoint='handJBLf_bnd',
                                                  midJoint='armJBLf_bnd',
                                                  pv='elbow',
                                                  offset=self.controlOffset_doubleSpinBox.value(),
                                                  size=self.sizeOfControl_doubleSpinBox.value())

        if armRt:
            #check to make sure joints in scene or system doesn't already exist
            exists = self.checkScene('arm', 'armJARt_bnd', 'handJBRt_bnd', 'armJBRt_bnd')

            if not exists:
                poleVectorSystem.PoleVectorSystem(base='arm',
                                                  startJoint='armJARt_bnd',
                                                  lastJoint='handJBRt_bnd',
                                                  midJoint='armJBRt_bnd',
                                                  pv='elbow',
                                                  offset=self.controlOffset_doubleSpinBox.value(),
                                                  size=self.sizeOfControl_doubleSpinBox.value())

        if legLf:
            #check to make sure joints in scene or system doesn't already exist
            exists = self.checkScene('leg', 'legJALf_bnd', 'footJALf_bnd', 'legJBLf_bnd')

            if not exists:
                poleVectorSystem.PoleVectorSystem(base='leg',
                                                  startJoint='legJALf_bnd',
                                                  lastJoint='footJALf_bnd',
                                                  midJoint='legJBLf_bnd',
                                                  pv='knee',
                                                  offset=self.controlOffset_doubleSpinBox.value(),
                                                  size=self.sizeOfControl_doubleSpinBox.value())

        if legRt:
            #check to make sure joints in scene or system doesn't already exist
            exists = self.checkScene('leg', 'legJARt_bnd', 'footJARt_bnd', 'legJBRt_bnd')

            if not exists:
                poleVectorSystem.PoleVectorSystem(base='leg',
                                                  startJoint='legJARt_bnd',
                                                  lastJoint='footJARt_bnd',
                                                  midJoint='legJBRt_bnd',
                                                  pv='knee',
                                                  offset=self.controlOffset_doubleSpinBox.value(),
                                                  size=self.sizeOfControl_doubleSpinBox.value())

        if self.customSysName_lineEdit.text():
            startJoint = self.startJoint_lineEdit.text()
            endJoint = self.endJoint_lineEdit.text()
            midJoint = self.getMidJoint(startJoint, endJoint)

            base = self.customSysName_lineEdit.text()

            exists = self.checkScene([base, startJoint, endJoint, midJoint])

            if not exists:
                poleVectorSystem.PoleVectorSystem(customSysName_lineEditbase=base,
                                                  startJoint=startJoint,
                                                  midJoint=midJoint,
                                                  lastJoint=endJoint,
                                                  pv=None,
                                                  offset=self.controlOffset_doubleSpinBox.value(),
                                                  size=self.sizeOfControl_doubleSpinBox.value())


    def getMidJoint(self, topJoint, targetJoint):


         #get Top Rel Joint
         rel = pm.listRelatives(topJoint, parent=True)[0]
         relOri = rel.jointOrient.get()
         while relOri[0] == 0 and relOri[1] == 0 and relOri[2] == 0:
             rel = pm.listRelatives(rel, parent=True)[0]
             relOri = rel.jointOrient.get()

         topJointParent = rel

         #get end rel Joint
         rel = pm.listRelatives(targetJoint, parent=True)[0]
         relOri = rel.jointOrient.get()
         while relOri[0] == 0 and relOri[1] == 0 and relOri[2] == 0:
             rel = pm.listRelatives(rel, parent=True)[0]
             relOri = rel.jointOrient.get()

         targetJointParent = rel

         counter = 0
         if topJointParent == targetJointParent:
             rel = pm.listRelatives(targetJoint, parent=True)[0]
             while rel != topJoint:
                 rel = pm.listRelatives(rel, parent=True)[0]
                 counter += 1

             index = 0
             rel = pm.listRelatives(targetJoint, parent=True)[0]
             while index < (counter - 1):
                 rel = pm.listRelatives(rel, parent=True)[0]
                 index +=1
         else:
             rel = pm.listRelatives(targetJointParent, parent=True)[0]
             while relOri[0] == 0 and relOri[1] == 0 and relOri[2] == 0:
                 rel = pm.listRelatives(rel, parent=True)[0]
                 relOri = rel.jointOrient.get()

         return rel


    def checkScene(self, sysName, startJnt, midJnt, endJnt):

        try:
            startJnt = pm.PyNode(startJnt)
            midJnt = pm.PyNode(midJnt)
            endJnt = pm.PyNode(endJnt)

        except pm.MayaNodeError as e:
            pm.warning("Joint Doesn't exist: ")
            return 1

        topNode = naming.TipName(name=startJnt, base='%sRig' % sysName, nodeType='node', index='A', suffix='1')
        target = naming.TipName(name=startJnt, base='%sTargetNul' % sysName, nodeType='node', index='A', suffix='1')

        try:
            pm.PyNode(topNode)
            pm.PyNode(target)
            return 1
        except:
            return 0
        
    @undoable
    def delete(self):
        if self.all_checkBox.isChecked():
            armLf = armRt = legLf = legRt = True
        else:
            armLf = self.armLf_checkBox.isChecked()
            armRt = self.armRt_checkBox.isChecked()
            legLf = self.legLf_checkBox.isChecked()
            legRt = self.legRt_checkBox.isChecked()

        if armLf:
            if pm.objExists("armRigNALf_1"):
                pm.delete("armRigNALf_1")
            if pm.objExists("armTargetNulNALf_1"):
                pm.delete("armTargetNulNALf_1")

        if armRt:
            if pm.objExists("armRigNARt_1"):
                pm.delete("armRigNARt_1")
            if pm.objExists("armTargetNulNARt_1"):
                pm.delete("armTargetNulNARt_1")

        if legLf:
            if pm.objExists("legRigNALf_1"):
                pm.delete("legRigNALf_1")
            if pm.objExists("legTargetNulNALf_1"):
                pm.delete("legTargetNulNALf_1")

        if legRt:
            if pm.objExists("legRigNARt_1"):
                pm.delete("legRigNARt_1")
            if pm.objExists("legTargetNulNARt_1"):
                pm.delete("legTargetNulNARt_1")

        


