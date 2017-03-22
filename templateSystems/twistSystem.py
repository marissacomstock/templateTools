#*******************************************************************************
# Copyright (c) 2013 Tippett Studio. All rights reserved.
# $Id: twistSystem.py 52150 2017-03-09 20:36:19Z marissa $
#*******************************************************************************

import os, re
import pymel.core as pm
from tip.maya.studio.core import *
from tip.maya.studio.tipModules import jointChain
from tip.maya.studio.tipModules import constraint
from tip.maya.studio.nodetypes import dependNode

class TwistSystem():
    def __init__(self,
                 name=None,
                 base=None,
                 baseJoint=None,
                 aimLocation=None,
                 twistParent=None):

        # ERRORCHECK ARGS
        try:
            self.baseJoint = checks.stringToPyNode(baseJoint)
            self.aimLocation = checks.stringToPyNode(aimLocation)
            self.twistParent = checks.stringToPyNode(twistParent)

        except error.ArgumentError, err:
            raise error.ArgumentError, err

        except error.MayaNodeError, err:
            raise error.MayaNodeError, err

        # COMPILE NAMING
        if name and isinstance(name, naming.TipName):
            self.TipName = naming.TipName(name=name, base=base, index='A', suffix='1')
        else:
            self.TipName = naming.TipName(name=self.baseJoint, base=base, index='A', suffix='1')

        self.create_twistJnts()
        self.position_system()
        self.constrain_system()

    def create_twistJnts(self):
        pm.select(self.baseJoint)

        #create joints all with same orientation as the base joint
        self.aim = pm.joint()
        self.aim.renameNode(name=self.TipName)
        self.aim.addCon()
        self.aim.addTag('twistSystem')
        self.aim.getParent().addTag('twistSystem')

        self.twist = pm.joint()
        self.twist.renameNode(name=self.TipName, base='%sTwist')
        self.twist.addTag('twistSystem')

        self.aimAt = pm.joint()
        self.aimAt.renameNode(name=self.TipName, base='%sAimAt')
        self.aimAt.addCon()
        self.aimAt.addTag('twistSystem')
        self.aimAt.getParent().addTag('twistSystem')


        self.aim.getParent().setParent(self.twistParent)
        self.aimAt.getParent().setParent(self.aimLocation)

    def position_system(self):
        if self.baseJoint == self.aimLocation:
            self.aim.getParent().translate.set((0, 0, 0))
        else:
            self.aimAt.getParent().translate.set((0, 0, 0))

    def constrain_system(self):
        if self.TipName.side == 'Rt':
            self.aim.translateX.set(-.001)
            if self.baseJoint == self.aimLocation:
                aimValue = 1
            else:
                aimValue = -1
        if self.TipName.side == 'Lf':
            self.aim.translateX.set(.001)
            if self.baseJoint == self.aimLocation:
                aimValue = -1
            else:
                aimValue = 1


        ptCon = constraint.Constraint(driven=self.twist,
                              drivers=[self.aimAt, self.aim],
                              maintainPosition=False,
                              orient=False,
                              scale=False,
                              lockWeights=False,
                              closed=False)
        ptCon.pointConstraint.addTag('twistSystem')
        oriCon = constraint.Constraint(driven=self.twist,
                              drivers=[self.aimAt, self.aim],
                              maintainPosition=False,
                              point=False,
                              scale=False,
                              skip=['y', 'z'],
                              lockWeights=False,
                              closed=False)
        oriCon.pointConstraint.addTag('twistSystem')
        aimCon = constraint.Constraint(driven=self.aim,
                              drivers=self.aimAt,
                              maintainPosition=False,
                              point=False,
                              orient=False,
                              scale=False,
                              aim=True,
                              offset=(0, 0, 0),
                              weight=1,
                              aimVector=(aimValue, 0, 0),
                              upVector=(0, 1, 0),
                              worldUpType='none',
                              lockWeights=False,
                              closed=False)
        aimCon.addTag('twistSystem')
