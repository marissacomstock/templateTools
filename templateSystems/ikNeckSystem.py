#********************************************************************************************************************************
# Copyright (c) 2013 Tippett Studio. All rights reserved.
# $Id: ikNeckSystem.py 52150 2017-03-09 20:36:19Z marissa $
#*******************************************************************************

import pymel.core as pm

from tip.maya.studio.core import *
from tip.maya.studio.tipModules import constraint
from tip.maya.studio.tipModules import controller
from tip.maya.studio.animation import joint
from tip.maya.studio.nodetypes import dagNode
from tip.maya.studio.nodetypes import dependNode


class IkNeckSystem():
    def __init__(self,
                 neck,
                 neckEnd,
                 head,
                 headEnd):
        try:

            # errorchecks for mel, forces puppet objects to be strings
            self.neck = checks.stringToPyNode(neck)
            self.head = checks.stringToPyNode(head)
            self.neckEnd = checks.stringToPyNode(neckEnd)
            self.headEnd = checks.stringToPyNode(headEnd)

            # make sure root index and blendControl index cannot go out of scope

        except error.ArgumentError, err:
            raise error.ArgumentError, err

        except error.MayaNodeError, err:
            raise error.MayaNodeError, err

        #make sure that head and neck have con
        if not self.neck.getParent() or not self.neck.getParent().nodeDescriptor.get() == 'Con':
            self.neck.addCon()
        if not self.head.getParent() or not self.head.getParent().nodeDescriptor.get() == 'Con':
            self.head.addCon()

        self.neck.addTag('neck')
        self.head.addTag('head')

        self.TipName = naming.TipName(name=self.neck)

        self.createJnts()
        self.constrainSys()
        self.addTransControl()

        #tag all nodes with default bound tags
        neckList = [self.aim, self.tip, self.blend, self.base, self.trans,
                           self.head, self.neck, self.headEnd, self.neckEnd]
        for jnt in neckList:
            jnt.addTagPreset(preset='bound')


    def createJnts(self):

        pm.select(self.neck)
        #jntName = naming.TipName(name=self.TipName, base='%sAim' % self.TipName.base)
        self.aim = pm.joint()
        self.aim.renameNode(name=self.TipName, base='%sAim')
        self.aim.addCon()
        self.aim.addTag('aim')

        self.twist = pm.joint()
        self.twist.renameNode(name=self.TipName, base='%sTwist')
        self.twist.addTag('twist')

        pm.select(self.head)
        self.tip = pm.joint()
        self.tip.renameNode(name=self.TipName, base='%Tip')
        self.tip.addCon()
        self.tip.addTag('tip')

        self.blend = pm.joint()
        self.blend.renameNode(name=self.TipName, base='%sTipBlend')
        self.blend.addCon()
        self.blend.addTag('blend')

        self.base = pm.joint()
        self.base.renameNode(name=self.TipName, base='%sBase')
        self.base.addCon()
        self.base.addTag('base')

        self.trans = pm.joint()
        self.trans.renameNode(name=self.head, base='%sTrans')
        self.trans.addCon()
        self.trans.addTag('trans')

        self.aim.getParent().setParent(self.neck)
        self.tip.getParent().setParent(self.aim)
        self.head.getParent().setParent(self.aim)
        self.blend.getParent().setParent(self.aim)
        self.base.getParent().setParent(self.neck)
        self.trans.getParent().setParent(self.neck)

    def constrainSys(self):
        #point constrain twist
        constraint.Constraint(driven=self.twist,
                              drivers=[self.neck, self.tip],
                              node=self.twist,
                              point=True,
                              orient=False,
                              scale=False,
                              maintainPosition=False,
                              lockWeights=False,
                              closed=False,
                              maintainOffset=False)

        #orient x of twist
        constraint.Constraint(driven=self.twist,
                              drivers=[self.neck, self.trans],
                              node=self.twist,
                              point=False,
                              orient=True,
                              scale=False,
                              maintainPosition=False,
                              lockWeights=False,
                              closed=False,
                              skip=['y', 'z'])


    def addTransControl(self):
        ctrl = controller.Controller(name=naming.truncLongName(self.trans),
                                      controlShape=0,
                                      controlScale=10,
                                      color=18,
                                      positionNode=self.trans,
                                      orientationNode=self.trans)
        ctrl.copyShapes(self.trans)
        pm.delete(ctrl)
        self.trans.renameShapeNodes()
