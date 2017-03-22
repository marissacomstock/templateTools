#********************************************************************************************************************************
# Copyright (c) 2013 Tippett Studio. All rights reserved.
# $Id: eyeSystem.py 52150 2017-03-09 20:36:19Z marissa $
#*******************************************************************************

import pymel.core as pm
from tip.maya.studio.core import *
from tip.maya.studio.animation import joint
from tip.maya.studio.nodetypes import attribute
from tip.maya.studio.tipModules import constraint
from tip.maya.studio.nodetypes import dependNode
from tip.maya.studio.nodetypes import plusMinusAverage
from tip.maya.studio.nodetypes import multiplyDivide
from tip.maya.studio.nodetypes import condition

EYEAREA_DICT = {'eye': 0.01,
                'skinSlide': 0.02,
                'membrane':0.03}

OUTERMULT_DICT = {'Rt': 1,
                  'Lf': -1}

INNERMULT_DICT = {'Rt': -1,
                  'Lf': 1}

class EyeSystem():
    def __init__(self,
            startJoint,
            socketJoint,
            endJoint,
            mainEye,
            name=None,
            eye=True,
            slideEye=False,
            membrane=False):

        # ERRORCHECK ARGS
        try:
            self.startJoint = checks.stringToPyNode(startJoint)
            self.socketJoint = checks.stringToPyNode(socketJoint)
            self.endJoint = checks.stringToPyNode(endJoint)

            naming.checkForNamingAttrs([self.startJoint, self.socketJoint, self.endJoint])

        except error.ArgumentError, err:
            raise error.ArgumentError, err

        except error.MayaNodeError, err:
            raise error.MayaNodeError, err

        #get area
        if eye:
            self.eyeArea = 'eye'
            system = ''
        if slideEye:
            self.eyeArea = 'skinSlide'
            system = 'SkinSlide'
        elif membrane:
            self.eyeArea = 'membrane'
            system = 'Membrane'

        #get naming for system
        if name and isinstance(name, naming.TipName):
            name = name
            self.TipName = naming.TipName(name=name, base='%s%s' % (name.base, system), suffix="1")
        else:
            name = startJoint
            self.TipName = naming.TipName(name=name, base='%s%s' % (name.nodeBase.get(), system), suffix="1")

        self.topName = naming.TipName(name=name, descriptor='rig', index='A', suffix='1')
        self.sysName = '%s%s' % (self.TipName.base, self.TipName.side)

        #add attrs
        if not pm.objExists(self.topName.name):
            self.rigGrp = pm.group(em=True)
            naming.TipName(self.rigGrp, name=self.topName)
            pm.delete(pm.parentConstraint(mainEye, self.rigGrp))
            self.rigGrp.setParent(self.socketJoint)
        else:
            self.rigGrp = pm.PyNode(self.topName.name)
            self.rigGrp.unlockAndShow(attribute.STANDARD_ATTRIBUTES)

        self.createMainNodes()
        self.createFollowNodes()
        self.constraintSystem()
        self.addAttrsToRig()
        self.setDefaultValues()
        self.createMainSystemNodes()

        if self.eyeArea == 'eye' or self.eyeArea == 'membrane':
            self.connectMainSystemAttrs_Rot()
            self.createOffsetSystem_Rot()
        else:
            self.connectMainSystemAttrs_Trans()
            self.createOffsetSystem_Trans()

        self.rigGrp.lockAndHide(attribute.STANDARD_ATTRIBUTES)
        pm.select(self.rigGrp)

    def addAttrsToRig(self):

        if not self.rigGrp.hasAttr(self.sysName):
            self.enum = self.rigGrp.addAttr(self.sysName, at="enum", en="________")
            self.enum.set(channelBox=True)
            #directional
            self.upper_up = self.rigGrp.addAttr("%s_upper_up" % self.eyeArea,
                                                attributeType='float', keyable=True)
            self.upper_down = self.rigGrp.addAttr("%s_upper_down" % self.eyeArea,
                                                attributeType='float', keyable=True)
            self.lower_up = self.rigGrp.addAttr("%s_lower_up" % self.eyeArea,
                                                attributeType='float', keyable=True)
            self.lower_down = self.rigGrp.addAttr("%s_lower_down" % self.eyeArea,
                                                attributeType='float', keyable=True)
            self.inner_in = self.rigGrp.addAttr("%s_inner_in" % self.eyeArea,
                                              attributeType='float', keyable=True)
            self.inner_out = self.rigGrp.addAttr("%s_inner_out" % self.eyeArea,
                                               attributeType='float', keyable=True)
            self.outer_in = self.rigGrp.addAttr("%s_outer_in" % self.eyeArea,
                                              attributeType='float', keyable=True)
            self.outer_out = self.rigGrp.addAttr("%s_outer_out" % self.eyeArea,
                                               attributeType='float', keyable=True)
            #follow
            self.InnerOuter_follow = self.rigGrp.addAttr("%s_InnerOuter_follow" % self.eyeArea,
                                                       attributeType='float', keyable=True)
            self.UpperLower_follow = self.rigGrp.addAttr("%s_UpperLower_follow" % self.eyeArea,
                                                                              attributeType='float', keyable=True)

            #blink falloff
            self.blinkFallOff = self.rigGrp.addAttr("%s_BlinkFalloff" % self.eyeArea,
                                                  attributeType='float', keyable=True,
                                                  minValue=0, maxValue=1)

    def createMainNodes(self):
        #grps
        #chain grp
        self.chainGrp = pm.duplicate(self.rigGrp, parentOnly=True)[0]
        self.chainGrp.renameNode(name=self.TipName, nodeType='chain')
        self.chainGrp.setParent(self.rigGrp)

        #horizontal driver
        self.horizontalDriver = pm.duplicate(self.chainGrp, parentOnly=True)[0]
        self.horizontalDriver.renameNode(name=self.TipName, nodeType='horizDriver')
        pm.delete(pm.pointConstraint(self.startJoint, self.horizontalDriver))

        #vertical driver
        self.verticalDriver = pm.duplicate(self.horizontalDriver, parentOnly=True)[0]
        self.verticalDriver.renameNode(name=self.TipName, nodeType='vertDriver')

        #main
        pm.select(self.horizontalDriver)
        self.driver = pm.joint()
        self.driver.renameNode(name=self.TipName, nodeType='driver')
        self.driver.addCon()
        self.driver.getParent().setParent(self.chainGrp)
        self.driver.getParent().visibility.set(0)

        pm.select(self.driver)
        self.main = pm.joint()
        self.main.renameNode(name=self.TipName, descriptor='system')

        pm.select(self.endJoint)
        self.eff = pm.joint()
        self.eff.renameNode(name=self.TipName, nodeType='effector')
        self.eff.setParent(self.driver)

        self.horizontalDriver.setParent(self.chainGrp)
        self.verticalDriver.setParent(self.chainGrp)

        #connectEye
        self.startJoint.rotate.connect(self.driver.getParent().rotate)

    def createFollowNodes(self):
        offset = EYEAREA_DICT[self.eyeArea]
        outerMult = OUTERMULT_DICT[self.TipName.side]
        innerMult = INNERMULT_DICT[self.TipName.side]

        #outer follow
        pm.select(self.driver.getParent())
        self.outer = pm.joint()
        self.outer.renameNode(name=self.TipName, base='%sOuter')
        self.outer.addCon()
        self.outer.translateZ.set(offset*outerMult)
        self.outer.getParent().setParent(self.chainGrp)

        #inner follow
        pm.select(self.driver.getParent())
        self.inner = pm.joint()
        self.inner.renameNode(name=self.TipName, base='%sInner')
        self.inner.addCon()
        self.inner.translateZ.set(offset*innerMult)
        self.inner.getParent().setParent(self.chainGrp)

        #upper follow
        pm.select(self.driver.getParent())
        self.upper = pm.joint()
        self.upper.renameNode(name=self.TipName, base='%sUpper')
        self.upper.addCon()
        self.upper.translateY.set(offset)
        self.upper.getParent().setParent(self.chainGrp)

        #lower follow
        pm.select(self.driver.getParent())
        self.lower = pm.joint()
        self.lower.renameNode(name=self.TipName, base='%sLower')
        self.lower.addCon()
        self.lower.translateY.set(offset)
        self.lower.getParent().setParent(self.chainGrp)

    def constraintSystem(self):
        #constrain drivers
        if self.eyeArea == 'eye' or self.eyeArea == 'membrane':
            constraint.Constraint(driven=self.horizontalDriver,
                              drivers=self.driver,
                              maintainPosition=False,
                              point=False,
                              orient=True,
                              scale=False,
                              lockWeights=False,
                              closed=False)
            constraint.Constraint(driven=self.verticalDriver,
                              drivers=self.driver,
                              maintainPosition=False,
                              point=False,
                              orient=True,
                              scale=False,
                              lockWeights=False,
                              closed=False)
        else:
            constraint.Constraint(driven=self.horizontalDriver,
                                  drivers=self.endJoint,
                                  maintainPosition=False,
                                  point=True,
                                  orient=False,
                                  scale=False,
                                  lockWeights=False,
                                  closed=False)
            constraint.Constraint(driven=self.verticalDriver,
                                  drivers=self.endJoint,
                                  maintainPosition=False,
                                  point=True,
                                  orient=False,
                                  scale=False,
                                  lockWeights=False,
                                  closed=False)


    def createMainSystemNodes(self):
        #multNodes
        #outer
        self.outerMULT = pm.shadingNode("multiplyDivide", asUtility=True)
        self.outerMULT.renameNode(name=self.TipName, base="%sOuter")
        self.outerMULT.addTag(self.rigGrp)
        #inner
        self.innerMULT = pm.shadingNode("multiplyDivide", asUtility=True)
        self.innerMULT.renameNode(name=self.TipName, base="%sInner")
        self.innerMULT.addTag(self.rigGrp)
        #upper
        self.upperMULT = pm.shadingNode("multiplyDivide", asUtility=True)
        self.upperMULT.renameNode(name=self.TipName, base="%sUpper")
        self.upperMULT.addTag(self.rigGrp)
        #lower
        self.lowerMULT = pm.shadingNode("multiplyDivide", asUtility=True)
        self.lowerMULT.renameNode(name=self.TipName, base="%sLower")
        self.lowerMULT.addTag(self.rigGrp)
        #outer
        self.outerCOND = pm.shadingNode("condition", asUtility=True)
        self.outerCOND.renameNode(name=self.TipName, base="%sOuter")
        self.outerCOND.addTag(self.rigGrp)
        #inner
        self.innerCOND = pm.shadingNode("condition", asUtility=True)
        self.innerCOND.renameNode(name=self.TipName, base="%sInner")
        self.innerCOND.addTag(self.rigGrp)
        #upper
        self.upperCOND = pm.shadingNode("condition", asUtility=True)
        self.upperCOND.renameNode(name=self.TipName, base="%sUpper")
        self.upperCOND.addTag(self.rigGrp)
        #lower
        self.lowerCOND = pm.shadingNode("condition", asUtility=True)
        self.lowerCOND.renameNode(name=self.TipName, base="%sLower")
        self.lowerCOND.addTag(self.rigGrp)

    def connectMainSystemAttrs_Rot(self):
        if self.TipName.side == 'Rt':
            inputOuter1 = self.outerMULT.input2Y
            inputOuter2 = self.outerMULT.input2X
            inputInner1 = self.innerMULT.input2X
            inputInner2 = self.innerMULT.input2Y
        else:
            inputOuter1 = self.outerMULT.input2X
            inputOuter2 = self.outerMULT.input2Y
            inputInner1 = self.innerMULT.input2Y
            inputInner2 = self.innerMULT.input2X

        #outer
        self.horizontalDriver.rotateY.connect(self.outerMULT.input1X)
        self.horizontalDriver.rotateY.connect(self.outerMULT.input1Y)
        self.outer_out.connect(inputOuter1)
        self.outer_in.connect(inputOuter2)
        self.horizontalDriver.rotateY.connect(self.outerCOND.firstTerm)
        self.outerCOND.operation.set(2)
        self.outerMULT.outputX.connect(self.outerCOND.colorIfTrueR)
        self.outerMULT.outputY.connect(self.outerCOND.colorIfFalseR)
        self.outerCOND.outColorR.connect(self.outer.getParent().rotateY)

        #inner
        self.horizontalDriver.rotateY.connect(self.innerMULT.input1X)
        self.horizontalDriver.rotateY.connect(self.innerMULT.input1Y)
        self.inner_out.connect(inputInner1)
        self.inner_in.connect(inputInner2)
        self.horizontalDriver.rotateY.connect(self.innerCOND.firstTerm)
        self.innerCOND.operation.set(4)
        self.innerMULT.outputX.connect(self.innerCOND.colorIfTrueR)
        self.innerMULT.outputY.connect(self.innerCOND.colorIfFalseR)
        self.innerCOND.outColorR.connect(self.inner.getParent().rotateY)

        #upper
        self.verticalDriver.rotateZ.connect(self.upperMULT.input1X)
        self.verticalDriver.rotateZ.connect(self.upperMULT.input1Y)
        self.upper_up.connect(self.upperMULT.input2X)
        self.upper_down.connect(self.upperMULT.input2Y)
        self.verticalDriver.rotateZ.connect(self.upperCOND.firstTerm)
        self.upperCOND.operation.set(2)
        self.upperMULT.outputX.connect(self.upperCOND.colorIfTrueR)
        self.upperMULT.outputY.connect(self.upperCOND.colorIfFalseR)
        self.upperCOND.outColorR.connect(self.upper.getParent().rotateZ)

        #lower
        self.verticalDriver.rotateZ.connect(self.lowerMULT.input1X)
        self.verticalDriver.rotateZ.connect(self.lowerMULT.input1Y)
        self.lower_up.connect(self.lowerMULT.input2Y)
        self.lower_down.connect(self.lowerMULT.input2X)
        self.verticalDriver.rotateZ.connect(self.lowerCOND.firstTerm)
        self.lowerCOND.operation.set(4)
        self.lowerMULT.outputX.connect(self.lowerCOND.colorIfTrueR)
        self.lowerMULT.outputY.connect(self.lowerCOND.colorIfFalseR)
        self.lowerCOND.outColorR.connect(self.lower.getParent().rotateZ)


    def connectMainSystemAttrs_Trans(self):
        if self.TipName.side == 'Rt':
            inputOuter1 = self.outerMULT.input2Y
            inputOuter2 = self.outerMULT.input2X
            inputInner1 = self.innerMULT.input2X
            inputInner2 = self.innerMULT.input2Y
        else:
            inputOuter1 = self.outerMULT.input2X
            inputOuter2 = self.outerMULT.input2Y
            inputInner1 = self.innerMULT.input2Y
            inputInner2 = self.innerMULT.input2X

        #outer
        self.horizontalDriver.translateZ.connect(self.outerMULT.input1X)
        self.horizontalDriver.translateZ.connect(self.outerMULT.input1Y)
        self.outer_out.connect(inputOuter2)
        self.outer_in.connect(inputOuter1)
        self.horizontalDriver.translateZ.connect(self.outerCOND.firstTerm)
        self.outerCOND.operation.set(2)
        self.outerMULT.outputX.connect(self.outerCOND.colorIfTrueR)
        self.outerMULT.outputY.connect(self.outerCOND.colorIfFalseR)
        self.outerCOND.outColorR.connect(self.outer.getParent().translateZ)

        #inner
        self.horizontalDriver.translateZ.connect(self.innerMULT.input1X)
        self.horizontalDriver.translateZ.connect(self.innerMULT.input1Y)
        self.inner_out.connect(inputInner2)
        self.inner_in.connect(inputInner1)
        self.horizontalDriver.translateZ.connect(self.innerCOND.firstTerm)
        self.innerCOND.operation.set(4)
        self.innerMULT.outputX.connect(self.innerCOND.colorIfTrueR)
        self.innerMULT.outputY.connect(self.innerCOND.colorIfFalseR)
        self.innerCOND.outColorR.connect(self.inner.getParent().translateZ)

        #upper
        self.verticalDriver.translateY.connect(self.upperMULT.input1X)
        self.verticalDriver.translateY.connect(self.upperMULT.input1Y)
        self.upper_up.connect(self.upperMULT.input2X)
        self.upper_down.connect(self.upperMULT.input2Y)
        self.verticalDriver.translateY.connect(self.upperCOND.firstTerm)
        self.upperCOND.operation.set(2)
        self.upperMULT.outputX.connect(self.upperCOND.colorIfTrueR)
        self.upperMULT.outputY.connect(self.upperCOND.colorIfFalseR)
        self.upperCOND.outColorR.connect(self.upper.getParent().translateY)

        #lower
        self.verticalDriver.translateY.connect(self.lowerMULT.input1X)
        self.verticalDriver.translateY.connect(self.lowerMULT.input1Y)
        self.lower_up.connect(self.lowerMULT.input2Y)
        self.lower_down.connect(self.lowerMULT.input2X)
        self.verticalDriver.translateY.connect(self.lowerCOND.firstTerm)
        self.lowerCOND.operation.set(4)
        self.lowerMULT.outputX.connect(self.lowerCOND.colorIfTrueR)
        self.lowerMULT.outputY.connect(self.lowerCOND.colorIfFalseR)
        self.lowerCOND.outColorR.connect(self.lower.getParent().translateY)

    def createOffsetSystem_Rot(self):
        #inner outer offset
        self.innerOuterPMA = pm.shadingNode('plusMinusAverage', asUtility=True)
        self.innerOuterPMA.renameNode(name=self.TipName, base="%sInnerOuterOffsetRot")
        self.innerOuterPMA.addTag(self.rigGrp)
        self.innerOuterMD = pm.shadingNode('multiplyDivide', asUtility=True)
        self.innerOuterMD.renameNode(name=self.TipName, base="%sInnerOuterOffsetRot")
        self.innerOuterMD.addTag(self.rigGrp)

        self.innerOuterPMA.input1D[0].set(2)
        self.upper.getParent().rotateZ.connect(self.innerOuterPMA.input1D[0])
        self.innerOuterPMA.input1D[1].set(2)
        self.lower.getParent().rotateZ.connect(self.innerOuterPMA.input1D[1])
        self.innerOuterPMA.output1D.connect(self.innerOuterMD.input1X)
        self.InnerOuter_follow.connect(self.innerOuterMD.input2X)
        self.innerOuterMD.outputX.connect(self.inner.getParent().rotateZ)
        self.innerOuterMD.outputX.connect(self.outer.getParent().rotateZ)

        #upper lower offset
        self.upperLowerPMA = pm.shadingNode('plusMinusAverage', asUtility=True)
        self.upperLowerPMA.renameNode(name=self.TipName, base="%sUpperLowerOffsetRot")
        self.upperLowerPMA.addTag(self.rigGrp)
        self.upperLowerMD = pm.shadingNode('multiplyDivide', asUtility=True)
        self.upperLowerMD.renameNode(name=self.TipName, base="%sUpperLowerOffsetRot")
        self.upperLowerMD.addTag(self.rigGrp)

        self.upperLowerPMA.input1D[0].set(2)
        self.inner.getParent().rotateY.connect(self.upperLowerPMA.input1D[0])
        self.upperLowerPMA.input1D[1].set(2)
        self.outer.getParent().rotateY.connect(self.upperLowerPMA.input1D[1])
        self.upperLowerPMA.output1D.connect(self.upperLowerMD.input1X)
        self.UpperLower_follow.connect(self.upperLowerMD.input2X)
        self.upperLowerMD.outputX.connect(self.upper.getParent().rotateY)
        self.upperLowerMD.outputX.connect(self.lower.getParent().rotateY)


    def createOffsetSystem_Trans(self):
        #inner outer offset
        self.innerOuterPMA = pm.shadingNode('plusMinusAverage', asUtility=True)
        self.innerOuterPMA.renameNode(name=self.TipName, base="%sInnerOuterOffsetTrans")
        self.innerOuterPMA.addTag(self.rigGrp)
        self.innerOuterMD = pm.shadingNode('multiplyDivide', asUtility=True)
        self.innerOuterMD.renameNode(name=self.TipName, base="%sInnerOuterOffsetTrans")
        self.innerOuterMD.addTag(self.rigGrp)

        self.innerOuterPMA.input1D[0].set(2)
        self.upper.getParent().translateY.connect(self.innerOuterPMA.input1D[0])
        self.innerOuterPMA.input1D[1].set(2)
        self.lower.getParent().translateY.connect(self.innerOuterPMA.input1D[1])
        self.innerOuterPMA.output1D.connect(self.innerOuterMD.input1X)
        self.InnerOuter_follow.connect(self.innerOuterMD.input2X)
        self.innerOuterMD.outputX.connect(self.inner.getParent().translateY)
        self.innerOuterMD.outputX.connect(self.outer.getParent().translateY)

        #upper lower offset
        self.upperLowerPMA = pm.shadingNode('plusMinusAverage', asUtility=True)
        self.upperLowerPMA.renameNode(name=self.TipName, base="%sUpperLowerOffsetTrans")
        self.upperLowerPMA.addTag(self.rigGrp)
        self.upperLowerMD = pm.shadingNode('multiplyDivide', asUtility=True)
        self.upperLowerMD.renameNode(name=self.TipName, base="%sUpperLowerOffsetTrans")
        self.upperLowerMD.addTag(self.rigGrp)

        self.upperLowerPMA.input1D[0].set(2)
        self.inner.getParent().translateZ.connect(self.upperLowerPMA.input1D[0])
        self.upperLowerPMA.input1D[1].set(2)
        self.outer.getParent().translateZ.connect(self.upperLowerPMA.input1D[1])
        self.upperLowerPMA.output1D.connect(self.upperLowerMD.input1X)
        self.UpperLower_follow.connect(self.upperLowerMD.input2X)
        self.upperLowerMD.outputX.connect(self.upper.getParent().translateZ)
        self.upperLowerMD.outputX.connect(self.lower.getParent().translateZ)

    def setDefaultValues(self):
        if self.eyeArea == 'eye' or self.eyeArea == 'membrane':
            self.upper_up.set(.75)
            self.upper_down.set(.5)
            self.lower_up.set(.4)
            self.lower_down.set(.1)
            self.inner_in.set(.1)
            self.inner_out.set(.2)
            self.outer_in.set(.3)
            self.outer_out.set(.1)
        else:
            self.upper_up.set(.25)
            self.upper_down.set(.5)
            self.lower_up.set(.25)
            self.lower_down.set(.5)
            self.inner_in.set(.05)
            self.inner_out.set(.01)
            self.outer_in.set(.05)
            self.outer_out.set(.15)

        self.InnerOuter_follow.set(.5)
        self.UpperLower_follow.set(.5)


    ############# TALK TO ERIC REWRITE
    '''
    def createBlinkFalloffSystem(self):

        #upper and lower falloff
        condList = [self.upperCOND, self.lowerCOND]

        for i, cond in enumerate(condList):
            jntConnection = pm.listConnections(cond, plugs=True, destination=True, source=False,
                                                 skipConversionNodes=True)[1]

            nodeName = naming.TipName(name=self.TipName,
                                       base='%sblinkFalloff' % cond.nodeBase.get(),
                                       nodeType='remapColor')
            remap = pm.shadingNode('remapColor', asUtility=True, name=nodeName)
            naming.addNamingAttrs(remap, tipName=nodeName)
            nodeName.setNodeType('multiply')
            mult = pm.shadingNode('multiplyDivide', asUtility=True, name=nodeName)
            naming.addNamingAttrs(mult, tipName=nodeName)

            remap.outColorR.connect(mult.input2X)
            cond.outColorR.connect(mult.input1X)

            attribute.forceConnect(mult.outputX, jntConnection)

            remap.colorR.set(0)
            remap.colorR.set(0)

            remap.red[0].red_Interp.set(2)
            remap.red[0].red_FloatValue.set(1)
            remap.red[1].red_Interp.set(2)
            remap.red[1].red_Position.set(10)
            self.blinkFallOff.connect(remap.red[1].red_FloatValue)
            if self.eyeArea == 'eye' or self.eyeArea == 'membrane':
                self.blinkFallOff.set(.5)
            else:
                self.blinkFallOff.set(0)

        #inner/Outer offset
        nodeName.setBase('%sInnerOuterOffsetUpper_blinkFalloff' % self.TipName.base)
        nodeName.setNodeType('rempapColor')
        remapUpper = pm.shadingNode('remapColor', asUtility=True, name=nodeName)
        naming.addNamingAttrs(remapUpper, tipName=nodeName)
        nodeName.setBase('%sInnerOuterOffsetLower_blinkFalloff' % self.TipName.base)
        remapLower = pm.shadingNode('remapColor', asUtility=True, name=nodeName)
        naming.addNamingAttrs(remapLower, tipName=nodeName)
        nodeName.setNodeType('plusMinusAverage')
        pma = pm.shadingNode('plusMinusAverage', asUtility=True, name=nodeName)
        naming.addNamingAttrs(pma, nodeName)
        nodeName.setNodeType('multiply')
        nodeName.setBase('%sInnerOuterOffset_BlinkFalloff' % self.TipName.base)
        mult = pm.shadingNode('multiplyDivide', asUtility=True, name=nodeName)
        naming.addNamingAttrs(mult, tipName=nodeName)
        nodeName.setBase('%sInnerOuterOffset_multHalfBlinkFalloff' % nodeName)
        multHalf = pm.shadingNode('multiplyDivide', asUtility=True, name=nodeName)


        remapUpper.colorR.set(0)
        remapLower.colorR.set(0)
        self.blinkFallOff.connect(multHalf.input1X)
        multHalf.outputX.connect(remapUpper.red[1].red_FloatValue)
        multHalf.outputX.connect(remapLower.red[1].red_FloatValue)
        remapUpper.red[0].red_Interp.set(2)
        remapUpper.red[0].red_FloatValue.set(.5)
        remapUpper.red[1].red_Interp.set(2)
        remapUpper.red[1].red_Position.set(10)
        remapLower.red[0].red_Interp.set(2)
        remapLower.red[0].red_FloatValue.set(.5)
        remapLower.red[1].red_Interp.set(2)
        remapLower.red[1].red_Position.set(10)

        pma.input1D[0].set(0)
        pma.input1D[1].set(0)
        remapUpper.outColorR.connect(pma.input1D[0])
        remapLower.outColorR.connect(pma.input1D[1])
        pma.output1D.connect(mult.input2X)
        self.InnerOuter_follow.connect(mult.input1X)
        attribute.forceConnect(mult.outputX, self.innerOuterMD.input2X)
    '''
