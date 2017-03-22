#*******************************************************************************
# Copyright (c) 2012 Tippett Studio. All rights reserved.
# $Id: muscleTwistSystem.py 52150 2017-03-09 20:36:19Z marissa $
#*******************************************************************************

import pymel.core as pm

from tip.maya.studio.core import *
from tip.maya.studio.tipModules import constraint
from tip.maya.studio.animation import joint

class MuscleTwistSystem():

    def __init__(self,
                 startJoint=None,
                 endJoint=None,
                 name=None,
                 scale=True,
                 offset=True,
                 planar=True,
                 flex=False):

        if startJoint:
            self.positionNode = pm.PyNode(startJoint)
            self.endNode = pm.PyNode(endJoint)
        else:
            self.positionNode = None
            self.endNode = None

        self.TipName = naming.TipName(name=name, suffix='1')

        self.create_baseJnts(scale, flex)

        self.create_aimJnts(offset)
        self.constrain_baseSystem(offset)
        self.multSystem(self.twistJnt)

        if planar:
            self.create_planarJnts()
            self.constrain_planarSystem()
        if scale:
            self.multSystem(self.scale)
        if flex:
            self.multSystem(self.flex)


    def create_baseJnts(self, scale, flex):
        '''create the weighting joints for the system'''
        # rename the startJoint

        if self.positionNode:
            pm.select(self.positionNode)

        self.startJnt = pm.joint()
        self.startJnt.renameNode(name=self.TipName)
        self.startJnt.addCon()
        self.twistJnt = pm.joint()
        self.twistJnt.renameNode(name=self.TipName, base='%sTwist')
        self.startJnt.getParent().setParent(world=True)

        if self.endNode:
            pm.select(self.endNode)
        else:
            pm.select(self.startJnt)
        self.endJnt = pm.joint()
        self.endJnt.renameNode(name=self.TipName, index='end')
        self.endJnt.setParent(self.startJnt)

        if not self.endNode:
            self.endJnt.translateX.set(20)

        if scale:
            pm.select(self.startJnt)
            self.scale = pm.joint()
            self.scale.renameNode(name=self.TipName, base='%sScale')

        if flex:
            pm.select(self.startJnt)
            self.flex = pm.joint()
            self.flex.renameNode(name=self.TipName, base='%sFlex')

    def create_aimJnts(self, offset=True):
        '''create the joint for the system to aim at,
        the simplest system will have this joint'''
        pm.select(self.endJnt)
        self.aimAt = pm.joint()
        self.aimAt.renameNode(name=self.TipName, base='%sAimAt')
        self.aimAt.setParent(world=True)
        self.aimAt.addCon()

        if offset:
            pm.select(self.endJnt)
            self.aimAtOffset = pm.joint()
            self.aimAtOffset.renameNode(name=self.TipName, base='%sAimAtOffset')
            self.aimAtOffset.setParent(world=True)
            self.aimAtOffset.addCon()

    def constrain_baseSystem(self, offset):
        if offset:
            aimJoint = self.aimAtOffset
        else:
            aimJoint = self.aimAt

        #constrain end joint
        constraint.Constraint(driven=self.endJnt,
                              drivers=aimJoint,
                              maintainPosition=False,
                              maintainOffset=False,
                              orient=False,
                              scale=False,
                              closed=False)

        #constrain twist
        constraint.Constraint(driven=self.twistJnt,
                              drivers=[self.startJnt, aimJoint],
                              maintainPosition=False,
                              maintainOffset=False,
                              orient=False,
                              scale=False,
                              closed=False)

        constraint.Constraint(driven=self.twistJnt,
                              drivers=[self.startJnt, aimJoint],
                              maintainPosition=False,
                              maintainOffset=False,
                              point=False,
                              scale=False,
                              closed=False,
                              skip=['y', 'z'])


        #put aim constraint on startJnt
        constraint.Constraint(driven=self.startJnt,
                              drivers=aimJoint,
                              maintainPosition=False,
                              maintainOffset=False,
                              point=False,
                              orient=False,
                              scale=False,
                              aim=True,
                              closed=False)

        if offset:
            #constrain aim offset
            constraint.Constraint(driven=self.aimAtOffset,
                                  drivers=self.aimAt,
                                  maintainPosition=False,
                                  maintainOffset=False,
                                  orient=False,
                                  scale=False,
                                  closed=False,
                                  skip='y',)



    def create_planarJnts(self):
        pm.select(self.startJnt)
        self.planar = pm.joint()
        self.planar.renameNode(name=self.TipName, base='%sPlanar')
        self.planar.setParent(world=True)
        self.planar.addCon()

        pm.select(self.startJnt)
        self.planarOffset = pm.joint()
        self.planarOffset.renameNode(name=self.TipName, base='%sPlanarOffset')
        self.planarOffset.setParent(world=True)
        self.planarOffset.addCon()

    def constrain_planarSystem(self):
        #constrain start joint con
        constraint.Constraint(driven=self.startJnt.getParent(),
                              drivers=self.planarOffset,
                              maintainPosition=False,
                              maintainOffset=False,
                              point=False,
                              orient=False,
                              scale=False,
                              parent=True,
                              closed=False)

        #constrain planar offset
        constraint.Constraint(driven=self.planarOffset,
                              drivers=self.planar,
                              maintainPosition=False,
                              maintainOffset=False,
                              orient=False,
                              scale=False,
                              closed=False,
                              skip='y',)


    def multSystem(self, jnt):

        divLength = pm.shadingNode('multiplyDivide', asUtility=True)
        divLength.operation.set(2)
        divLength.renameNode(name=self.TipName, base='%Length')

        divRev = pm.shadingNode('multiplyDivide', asUtility=True)
        divRev.operation.set(2)
        divRev.renameNode(name=self.TipName, base='%Reverse')

        self.endJnt.translateX.connect(divLength.input1X)
        divLength.input2X.set(self.endJnt.translateX.get())

        self.endJnt.translateX.connect(divRev.input2X)
        divRev.input1X.set(self.endJnt.translateX.get())

        divLength.outputX.connect(jnt.scaleX)
        divRev.outputX.connect(jnt.scaleY)
        divRev.outputX.connect(jnt.scaleZ)