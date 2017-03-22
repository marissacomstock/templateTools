#********************************************************************************************************************************
# Copyright (c) 2013 Tippett Studio. All rights reserved.
# $Id: twistWidget.py 52150 2017-03-09 20:36:19Z marissa $
#*******************************************************************************

import os, sys, re
import pymel.core as pm
from tip.qt.pkg import QtCore, QtGui, uic

from tip.maya.studio.core import *
from tip.maya.puppet.utils.decorators import undoable
from tip.maya.puppet.tools.templateTools.templateSystems import twistSystem
from tip.maya.puppet.tools.templateTools.templateSystems import muscleTwistSystem

FILEPATH = os.path.dirname(__file__).replace('templateWidgets', 'templateUIs')
__dialogs = list()

form_class, base_class = uic.loadUiType(os.path.join(FILEPATH, "twistWidget.ui"))


class TwistWidget(form_class, base_class):

    closeSignal = QtCore.Signal()
    refreshSignal = QtCore.Signal()

    def __init__(self):
        super(TwistWidget, self).__init__()
        self.setupUi(self)
        self.setObjectName('TwistTool')
        self.setWindowTitle('Twist Tool')

        self.reset()

        #check boxes
        self.all_checkBox.clicked.connect(self.assignObject)
        self.armShoulderLf_checkBox.clicked.connect(self.assignObject)
        self.armShoulderRt_checkBox.clicked.connect(self.assignObject)
        self.handWristLf_checkBox.clicked.connect(self.assignObject)
        self.handWristRt_checkBox.clicked.connect(self.assignObject)
        self.legHipLf_checkBox.clicked.connect(self.assignObject)
        self.legHipRt_checkBox.clicked.connect(self.assignObject)
        self.footAnkleLf_checkBox.clicked.connect(self.assignObject)
        self.footAnkleRt_checkBox.clicked.connect(self.assignObject)
        #load buttons
        self.startJoint_pushButton.clicked.connect(self.assignObject)
        self.endJoint_pushButton.clicked.connect(self.assignObject)
        #Text changed custom
        self.systemName_lineEdit.textChanged.connect(self.assignObject)
        self.startJoint_lineEdit.textChanged.connect(self.assignObject)
        self.endJoint_lineEdit.textChanged.connect(self.assignObject)
        #execute buttons
        self.create_pushButton.clicked.connect(self.assignObject)
        self.delete_pushButton.clicked.connect(self.assignObject)
        self.reset_pushButton.clicked.connect(self.assignObject)
        #muscle System
        self.createMuscles_pushButton.clicked.connect(self.assignObject)

    def assignObject(self):

        sender = self.sender()

        #checkboxes
        if sender is self.all_checkBox:
            self.uncheck_indivBoxes()
        elif sender is self.armShoulderLf_checkBox:
            self.all_checkBox.setChecked(False)
        elif sender is self.armShoulderRt_checkBox:
            self.all_checkBox.setChecked(False)
        elif sender is self.handWristLf_checkBox:
            self.all_checkBox.setChecked(False)
        elif sender is self.handWristRt_checkBox:
            self.all_checkBox.setChecked(False)
        elif sender is self.legHipLf_checkBox:
            self.all_checkBox.setChecked(False)
        elif sender is self.legHipRt_checkBox:
            self.all_checkBox.setChecked(False)
        elif sender is self.footAnkleLf_checkBox:
            self.all_checkBox.setChecked(False)
        elif sender is self.footAnkleRt_checkBox:
            self.all_checkBox.setChecked(False)

        #load buttons
        elif sender is self.startJoint_pushButton:
            self.all_checkBox.setChecked(False)
            self.loadSelection(self.startJoint_lineEdit)
        elif sender is self.endJoint_pushButton:
            self.all_checkBox.setChecked(False)
            self.loadSelection(self.endJoint_lineEdit)

        #text changed
        elif sender is self.systemName_lineEdit:
            self.all_checkBox.setChecked(False)
        elif sender is self.startJoint_lineEdit:
            self.all_checkBox.setChecked(False)
        elif sender is self.endJoint_lineEdit:
            self.all_checkBox.setChecked(False)

        #execute buttons
        elif sender is self.create_pushButton:
            self.create()
        elif sender is self.delete_pushButton:
            self.delete()
        elif sender is self.reset_pushButton:
            self.reset()

        #muscleSystem
        elif sender is self.createMuscles_pushButton:
            self.createMuscleSystem()

    def uncheck_indivBoxes(self):
        self.armShoulderLf_checkBox.setChecked(False)
        self.armShoulderRt_checkBox.setChecked(False)
        self.handWristLf_checkBox.setChecked(False)
        self.handWristRt_checkBox.setChecked(False)
        self.legHipLf_checkBox.setChecked(False)
        self.legHipRt_checkBox.setChecked(False)
        self.footAnkleLf_checkBox.setChecked(False)
        self.footAnkleRt_checkBox.setChecked(False)

    def loadSelection(self, lineEdit):
        try:
            sel = pm.ls(selection=True)
            lineEdit.setText(checks.pyNodeToString(sel[0]))
        except IndexError, TypeError:
            pm.error("Select one joint")

    def reset(self):
        self.all_checkBox.setChecked(True)
        self.systemName_lineEdit.clear()
        self.startJoint_lineEdit.clear()
        self.endJoint_lineEdit.clear()
        self.uncheck_indivBoxes()

    @undoable
    def create(self):
        if self.all_checkBox.isChecked():
            armShoulderLf = True
            armShoulderRt = True
            handWristLf = True
            handWristRt = True
            legHipLf = True
            legHipRt = True
            footAnkleLf = True
            footAnkleRt = True
        else:
            armShoulderLf = self.armShoulderLf_checkBox.isChecked()
            armShoulderRt = self.armShoulderRt_checkBox.isChecked()
            handWristLf = self.handWristLf_checkBox.isChecked()
            handWristRt = self.handWristRt_checkBox.isChecked()
            legHipLf = self.legHipLf_checkBox.isChecked()
            legHipRt = self.legHipRt_checkBox.isChecked()
            footAnkleLf = self.footAnkleLf_checkBox.isChecked()
            footAnkleRt = self.footAnkleRt_checkBox.isChecked()

        if armShoulderLf:
            #check to make sure joints in scene or system doesn't already exist
            exists = self.checkScene('armShoulder', 'armJALf_bnd', 'armJBLf_bnd', 'clavicleJALf_bnd')

            if not exists:
                twistSystem.TwistSystem(base='armShoulder',
                                        baseJoint='armJALf_bnd',
                                        aimLocation='armJBLf_bnd',
                                        twistParent='clavicleJALf_bnd')
        if armShoulderRt:
            #check to make sure joints in scene or system doesn't already exist
            exists = self.checkScene('armShoulder', 'armJARt_bnd', 'armJBRt_bnd', 'clavicleJARt_bnd')

            if not exists:
                twistSystem.TwistSystem(base='armShoulder',
                                        baseJoint='armJARt_bnd',
                                        aimLocation='armJBRt_bnd',
                                        twistParent='clavicleJARt_bnd')
        if handWristLf:
            #check to make sure joints in scene or system doesn't already exist
            exists = self.checkScene('handWrist', 'armJBLf_bnd', 'armJBLf_bnd', 'handJBLf_bnd')

            if not exists:
                twistSystem.TwistSystem(base='handWrist',
                                        baseJoint='armJBLf_bnd',
                                        aimLocation='armJBLf_bnd',
                                        twistParent='handJBLf_bnd')
        if handWristRt:
            #check to make sure joints in scene or system doesn't already exist
            exists = self.checkScene('handWrist', 'armJBRt_bnd', 'armJBRt_bnd', 'handJBRt_bnd')

            if not exists:
                twistSystem.TwistSystem(base='handWrist',
                                        baseJoint='armJBRt_bnd',
                                        aimLocation='armJBRt_bnd',
                                        twistParent='handJBRt_bnd')
        if legHipLf:
            #check to make sure joints in scene or system doesn't already exist
            exists = self.checkScene('legHip', 'legJALf_bnd', 'legJBLf_bnd', 'pelvisJA_bnd')

            if not exists:
                twistSystem.TwistSystem(base='legHip',
                                        baseJoint='legJALf_bnd',
                                        aimLocation='legJBLf_bnd',
                                        twistParent='pelvisJA_bnd')
        if legHipRt:
            #check to make sure joints in scene or system doesn't already exist
            exists = self.checkScene('legHip', 'legJARt_bnd', 'legJBRt_bnd', 'pelvisJA_bnd')

            if not exists:
                twistSystem.TwistSystem(base='legHip',
                                        baseJoint='legJARt_bnd',
                                        aimLocation='legJBRt_bnd',
                                        twistParent='pelvisJA_bnd')
        if footAnkleLf:
            #check to make sure joints in scene or system doesn't already exist
            exists = self.checkScene('footAnkle', 'legJBLf_bnd', 'legJBLf_bnd', 'footJALf_bnd')

            if not exists:
                twistSystem.TwistSystem(base='footAnkle',
                                        baseJoint='legJBLf_bnd',
                                        aimLocation='legJBLf_bnd',
                                        twistParent='footJALf_bnd')
        if footAnkleRt:
            #check to make sure joints in scene or system doesn't already exist
            exists = self.checkScene('footAnkle', 'legJBRt_bnd', 'legJBRt_bnd', 'footJARt_bnd')

            if not exists:
                twistSystem.TwistSystem(base='footAnkle',
                                        baseJoint='legJBRt_bnd',
                                        aimLocation='legJBRt_bnd',
                                        twistParent='footJARt_bnd')

        if self.systemName_lineEdit.text():
            baseJoint, aimLocation, twistParent = self.getTwistJnts()

            name = self.systemName_lineEdit.text()
            if baseJoint.find("Lf") > -1:
                side = "Lf"
            elif baseJoint.find("Rt") > -1:
                side = "Rt"
            else:
                side = ""
            exists = self.checkScene([name, side, baseJoint, aimLocation, twistParent])

            if not exists:
                twistSystem.TwistSystem(name=name,
                                            side=side,
                                            baseJoint=baseJoint,
                                            aimLocation=aimLocation,
                                            twistParent=twistParent)

    def getTwistJnts(self):

        try:
            startJoint = pm.PyNode(self.startJoint_lineEdit.text())
            endJoint = pm.PyNode(self.endJoint_lineEdit.text())
        except error.ArgumentError, err:
            raise error.ArgumentError, err

        except error.MayaNodeError, err:
            raise error.MayaNodeError, err
        pm.select('allScaleN_bnd', hierarchy=True)

        jntHier = pm.ls(selection=True)

        startIndex = jntHier.index(startJoint)
        endIndex = jntHier.index(endJoint)

        #Upward Chain
        if startIndex > endIndex:
            baseJoint=endJoint
            aimLocation=endJoint
            twistParent = startJoint
        #Downward Chain
        else:
            temp = startJoint
            while temp.nodeBase.get() == temp.getParent().nodeBase.get():
                temp = temp.getParent()
            baseJoint = startJoint
            aimLocation = endJoint
            twistParent = temp.getParent()

        return [baseJoint, aimLocation, twistParent]

    def checkScene(self, systemName, aim, twist, aimAt):

        try:
            aim = pm.PyNode(aim)
            twist = pm.PyNode(twist)
            aimAt = pm.PyNode(aimAt)

        except pm.MayaNodeError as e:
            pm.warning("Node Doesn't exist: ")
            return 1

        aimName = naming.TipName(name=twist, base=systemName, suffix='1')
        twistName = naming.TipName(name=twist, base='%sTwist' % systemName, suffix='1')
        aimAtName = naming.TipName(name=twist, base='%sAimAt' % systemName, suffix='1')


        try:
            pm.PyNode(aimName.name)
            pm.PyNode(twistName.name)
            pm.PyNode(aimAtName.name)
            return 1
        except:
            return 0

    @undoable
    def delete(self):
        if self.all_checkBox.isChecked():
            armShoulderLf = True
            armShoulderRt = True
            handWristLf = True
            handWristRt = True
            legHipLf = True
            legHipRt = True
            footAnkleLf = True
            footAnkleRt = True
        else:
            armShoulderLf = self.armShoulderLf_checkBox.isChecked()
            armShoulderRt = self.armShoulderRt_checkBox.isChecked()
            handWristLf = self.handWristLf_checkBox.isChecked()
            handWristRt = self.handWristRt_checkBox.isChecked()
            legHipLf = self.legHipLf_checkBox.isChecked()
            legHipRt = self.legHipRt_checkBox.isChecked()
            footAnkleLf = self.footAnkleLf_checkBox.isChecked()
            footAnkleRt = self.footAnkleRt_checkBox.isChecked()

        if armShoulderLf:
            if pm.objExists('armShoulderJAConALf_1'):
                pm.delete('armShoulderJAConALf_1')
            if pm.objExists('armShoulderAimAtJAConALf_1'):
                pm.delete('armShoulderAimAtJAConALf_1')

        if armShoulderRt:
            if pm.objExists('armShoulderJAConARt_1'):
                pm.delete('armShoulderJAConARt_1')
            if pm.objExists('armShoulderAimAtJAConARt_1'):
                pm.delete('armShoulderAimAtJAConARt_1')


        if handWristLf:
            if pm.objExists('handWristJAConALf_1'):
                pm.delete('handWristJAConALf_1')
            if pm.objExists('handWristAimAtJAConALf_1'):
                pm.delete('handWristAimAtJAConALf_1')


        if handWristRt:
            if pm.objExists('handWristJAConARt_1'):
                pm.delete('handWristJAConARt_1')
            if pm.objExists('handWristAimAtJAConARt_1'):
                pm.delete('handWristAimAtJAConARt_1')

        if legHipLf:
            if pm.objExists('legHipJAConALf_1'):
                pm.delete('legHipJAConALf_1')
            if pm.objExists('legHipAimAtJAConALf_1'):
                pm.delete('legHipAimAtJAConALf_1')

        if legHipRt:
            if pm.objExists('legHipJAConARt_1'):
                pm.delete('legHipJAConARt_1')
            if pm.objExists('legHipAimAtJAConARt_1'):
                pm.delete('legHipAimAtJAConARt_1')

        if footAnkleLf:
            if pm.objExists('footAnkleJAConALf_1'):
                pm.delete('footAnkleJAConALf_1')
            if pm.objExists('footAnkleAimAtJAConALf_1'):
                pm.delete('footAnkleAimAtJAConALf_1')

        if footAnkleRt:
            if pm.objExists('footAnkleJAConARt_1'):
                pm.delete('footAnkleJAConARt_1')
            if pm.objExists('footAnkleAimAtJAConARt_1'):
                pm.delete('footAnkleAimAtJAConARt_1')

    def createMuscleSystem(self):

        sel = pm.ls(selection=True)
        pm.select(clear=True)

        if sel:
            if len(sel) != 2:
                pm.error('Select start and end joint')
            else:
                startJoint = sel[0]
                endJoint = sel[1]

        else:
            startJoint = None
            endJoint = None

        if not sel:
            name = self.name_lineEdit.text()
            if self.center_radioButton.isChecked():
                side = None
            elif self.left_radioButton.isChecked():
                side = 'left'
            else:
                side = 'right'

            TipName = naming.TipName(base=name, side=side, index='A', suffix='bnd')
        else:
            TipName = naming.TipName(name=startJoint)

        offset = self.offset_checkBox.isChecked()
        scale = self.scale_checkBox.isChecked()
        flex = self.flex_checkBox.isChecked()
        planar = self.planar_checkBox.isChecked()

        muscleTwistSystem.MuscleTwistSystem(startJoint=startJoint,
                                            endJoint=endJoint,
                                            name=TipName,
                                            scale=True,
                                            offset=True,
                                            planar=True,
                                            flex=False)

        pm.select(clear=True)