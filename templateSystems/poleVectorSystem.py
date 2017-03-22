#********************************************************************************************************************************
# Copyright (c) 2013 Tippett Studio. All rights reserved.
# $Id: poleVectorSystem.py 52150 2017-03-09 20:36:19Z marissa $
#*******************************************************************************

import os
import pymel.core as pm
from maya import OpenMaya
import math
from tip.maya.studio.core import *
from tip.maya.studio.nodetypes import dagNode
from tip.maya.studio.nodetypes import dependNode
from tip.maya.studio.tipModules import constraint
from tip.maya.studio.tipModules import controller


class PoleVectorSystem():
    def __init__(self,
                name=None,
                base=None,
                startJoint=None,
                midJoint=None,
                lastJoint=None,
                pv=None,
                offset=1,
                size=1):

        # ERRORCHECK ARGS
        try:
            self.topJoint = checks.stringToPyNode(startJoint)
            self.halfJoint = checks.stringToPyNode(midJoint)
            self.targetJoint = checks.stringToPyNode(lastJoint)

        except error.ArgumentError, err:
            raise error.ArgumentError, err

        except error.MayaNodeError, err:
            raise error.MayaNodeError, err

        # COMPILE NAMING
        if name:
            self.TipName = naming.TipName(name=name, base=base, nodeType='node', index='A',  suffix='1')
        else:
            self.TipName = naming.TipName(name=self.topJoint, base=base, nodeType='node', index='A',  suffix='1')

        self.ctrlSize = size
        self.offset = offset

        self.create_NulS(pv)
        self.parent_orient_system()
        self.create_and_parent_ctrl()
        self.set_color()
        self.constrain_system()
        pm.select(clear=True)

    def create_NulS(self, pv):
        self.grpRig = pm.group(em=True)
        self.grpRig.renameNode(name=self.TipName, base='%sRig')
        self.grpAim = pm.group(em=True, parent=self.grpRig)
        self.grpAim.renameNode(name=self.TipName, base='%sAim')

        self.grpHalf = pm.group(em=True, parent=self.grpAim)
        self.grpHalf.renameNode(name=self.TipName, base='%sHalfNul')
        self.grpMcNul = pm.group(em=True, parent=self.grpHalf)
        self.grpMcNul.renameNode(name=self.TipName, base='%sMcNul')

        if pv:
            ctrlName = naming.TipName(name=self.TipName, base=pv)
        else:
            ctrlName = self.TipName

        self.grpPV = pm.group(em=True, parent=self.grpMcNul)
        self.grpPV.renameNode(name=ctrlName)
        self.targetNul = pm.group(em=True)
        self.targetNul.renameNode(name=self.TipName, base='%sTargetNul')


    def create_and_parent_ctrl(self):
        ctrl = controller.Controller(name=self.TipName,
                                     controlShape='box',
                                     controlScale=self.ctrlSize,
                                     positionNode=self.grpPV,
                                     orientationNode=self.grpPV)
        ctrl.copyShapes(self.grpPV)
        pm.delete(ctrl)
        self.grpPV.renameShapeNodes()


    def parent_orient_system(self):
        self.grpRig.matchTo(self.topJoint)
        self.grpRig.setParent(self.topJoint)
        self.grpHalf.translateX.set(self.halfJoint.getParent().translateX.get())
        #determine direction
        self.poleVector_direction()

        #targetNul
        self.targetNul.matchTo(self.targetJoint)
        self.targetNul.setParent(self.targetJoint)


    def set_color(self):
        if self.TipName.side == "Lf":
            self.grpPV.setOverrideColor(15)
        elif self.TipName.side == "Rt":
            self.grpPV.setOverrideColor(4)
        else:
            self.grpPV.setOverrideColor(24)


    def constrain_system(self):
        aim = 1
        if self.TipName.side == "Rt":
            aim = -1

        constraint.Constraint(driven=self.grpHalf,
                              drivers=[self.targetNul, self.grpAim],
                              maintainPosition=False,
                              orient=False,
                              scale=False)
        constraint.Constraint(driven=self.grpAim,
                              drivers=self.targetNul,
                              maintainPosition=False,
                              point=False,
                              orient=False,
                              scale=False,
                              aim=True,
                              offset=(0, 0, 0),
                              weight=1,
                              aimVector=(aim, 0, 0),
                              upVector=(0, 1, 0),
                              worldUpType='none')


    def poleVector_direction(self):
        start = pm.xform(self.topJoint, q=1, ws=1, t=1)
        mid = pm.xform(self.halfJoint, q=1, ws=1, t=1)
        end = pm.xform(self.targetJoint, q=1, ws=1, t=1)

        #get postion of joints
        startV = OpenMaya.MVector(start[0], start[1], start[2])
        midV = OpenMaya.MVector(mid[0], mid[1], mid[2])
        endV = OpenMaya.MVector(end[0], end[1], end[2])
        #get vectors from start to end and start to mid
        startEnd = endV - startV
        startMid = midV - startV
        #get the vector between
        dotP = startMid * startEnd
        #get pole vector position
        projLen = float(dotP) / float(startEnd.length())
        startEndN = startEnd.normal()
        projV = startEndN * projLen
        arrowV = startMid - projV
        finalV = arrowV + midV

        cross1 = startEnd - startMid
        cross1.normalize()
        cross2 = cross1 ^ arrowV
        cross2.normalize()
        arrowV.normalize()

        matrixV = [arrowV.x, arrowV.y, arrowV.z, 0,
            cross1.x, cross1.y, cross1.z, 0,
            cross2.x, cross2.y, cross2.z, 0,
            0,0,0,1]

        matrixM = OpenMaya.MMatrix()

        OpenMaya.MScriptUtil.createMatrixFromList(matrixV, matrixM)
        matrixFn = OpenMaya.MTransformationMatrix(matrixM)
        rot = matrixFn.eulerRotation()

        self.loc = pm.spaceLocator(name="%s_DELLOC" % self.grpRig)
        self.locMov = pm.spaceLocator(name="%s_DELLOCPARENT" % self.grpRig)
        self.locMov.setParent(self.loc)
        pm.xform(self.loc, ws=1, t=(finalV.x, finalV.y, finalV.z))
        pm.xform(self.loc, ws=1, rotation=((rot.x/math.pi*180.0),
                                    (rot.y/math.pi*180.0),
                                    (rot.z/math.pi*180.0)))

        self.locMov.translateX.set(self.offset)
        pm.delete(pm.pointConstraint(self.locMov, self.grpMcNul, maintainOffset=False))
        self.grpMcNul.translateX.set(0)
        self.grpMcNul.translateZ.set(0)
        pm.delete(self.loc)

