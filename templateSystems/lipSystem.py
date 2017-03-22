#********************************************************************************************************************************
# $Id: lipSystem.py 52150 2017-03-09 20:36:19Z marissa $
#*******************************************************************************

import pymel.core as pm

from tip.maya.studio.core import checks
from tip.maya.studio.core import error
from tip.maya.studio.core import naming
from tip.maya.studio.nodetypes import attribute
from tip.maya.studio.tipModules import constraint
from tip.maya.studio.nodetypes import dependNode

class LipSystem():
    def __init__(self,
            loc=None,
            head=None,
            jaw=None,
            name=None):

        # ERRORCHECK ARGS
        try:
            self.loc = checks.stringToPyNode(loc)
            self.head = checks.stringToPyNode(head)
            self.jaw = checks.stringToPyNode(jaw)

        except error.ArgumentError, err:
            raise error.ArgumentError, err

        except error.MayaNodeError, err:
            raise error.MayaNodeError, err

        # COMPILE NAMING
        if name and isinstance(name, naming.TipName):
            name=name
        else:
            name=jaw
        self.TipName = naming.TipName(name=name, suffix="1")

        self.create_lipRigJnt()
        self.create_upperJnts()
        self.create_lowerJnts()
        self.create_skinJnts()
        self.constrain_lipJnts()
        self.connect_constraints()
        self.connect_lipSystem()
        self.clamp_sideLipJnts()

        pm.select(self.lipFollowRig)

    def create_lipRigJnt(self):
        self.lipFollowRig = pm.group(em=True)
        self.lipFollowRig.renameNode(name=self.TipName,
                                     base='%sLip',
                                     descriptor='rig')
        self.lipFollowRig.matchTo(self.jaw)

        zOri = self.jaw.getParent().jointOrientZ.get()
        if zOri > -90:
            self.lipFollowRig.rotateY.set(0)
        elif zOri > -180:
            self.lipFollowRig.rotateY.set(-90)
        self.lipFollowRig.makeIdentity(apply=True, translate=False, jointOrient=False)
        self.lipFollowRig.setParent(self.head)

    def create_upperJnts(self):
        #Create upper nodes
        self.headUpperWeight = pm.duplicate(self.lipFollowRig, parentOnly=True)[0]
        self.headUpperWeight.renameNode(name=self.TipName, base='%sHeadUpperWeight')
        self.headUpperWeight.setParent(self.lipFollowRig)

        self.upperLipFollow = pm.duplicate(self.lipFollowRig, parentOnly=True)[0]
        self.upperLipFollow.renameNode(name=self.TipName, base='%sUpperLipFollow')
        self.upperLipFollow.setParent(self.headUpperWeight)

        self.upperLipTrans = pm.duplicate(self.lipFollowRig, parentOnly=True)[0]
        self.upperLipTrans.renameNode(name=self.TipName, base='%sHeadUpperLipTrans')
        self.upperLipTrans.setParent(self.upperLipFollow)

        self.upperLipAim = pm.duplicate(self.lipFollowRig, parentOnly=True)[0]
        self.upperLipAim.renameNode(name=self.TipName, base='%sUpperLipAim')
        self.upperLipAim.setParent(self.upperLipTrans)
        self.upperLipAim.matchTo(self.loc)

        self.upperLipACON = pm.duplicate(self.upperLipAim, parentOnly=True)[0]
        self.upperLipACON.renameNode(name=self.TipName, base='%sUpperLipCon')
        self.upperLipACON.setParent(self.upperLipAim)

        self.upperLipFollowHead = pm.duplicate(self.upperLipAim, parentOnly=True)[0]
        self.upperLipFollowHead.renameNode(name=self.TipName, base='%sUpperLipFollowHead')
        self.upperLipFollowHead.setParent(self.head)

        pm.select(self.upperLipACON)
        self.headUpperLip = pm.joint()
        self.headUpperLip.renameNode(name=self.TipName,
                                     base='%sUpperLip' % self.TipName.base,
                                     index='A',
                                     suffix='bnd')
        self.headUpperLip.matchTo(self.loc)

    def create_lowerJnts(self):
        ##Create lower nodes
        self.headLowerWeight = pm.duplicate(self.lipFollowRig, parentOnly=True)[0]
        self.headLowerWeight.renameNode(name=self.TipName, base='%sHeadLowerWeight')
        self.headLowerWeight.setParent(self.lipFollowRig)

        self.lowerLipFollow = pm.duplicate(self.lipFollowRig, parentOnly=True)[0]
        self.lowerLipFollow.renameNode(name=self.TipName, base='%sLowerLipFollow')
        self.lowerLipFollow.setParent(self.headLowerWeight)

        self.lowerLipTrans = pm.duplicate(self.lipFollowRig, parentOnly=True)[0]
        self.lowerLipTrans.renameNode(name=self.TipName, base='%sHeadLowerLipTrans')
        self.lowerLipTrans.setParent(self.lowerLipFollow)

        self.lowerLipAim = pm.duplicate(self.lipFollowRig, parentOnly=True)[0]
        self.lowerLipAim.renameNode(name=self.TipName, base='%sLowerLipAim')
        self.lowerLipAim.setParent(self.lowerLipTrans)
        self.lowerLipAim.matchTo(self.loc)

        self.lowerLipACON = pm.duplicate(self.upperLipAim, parentOnly=True)[0]
        self.lowerLipACON.renameNode(name=self.TipName, base='%sLowerLipACon')
        self.lowerLipACON.setParent(self.lowerLipAim)

        self.lowerLipFollowJaw = pm.duplicate(self.upperLipAim, parentOnly=True)[0]
        self.lowerLipFollowJaw.renameNode(name=self.TipName, base='%sLowerLipFollowJaw')
        self.lowerLipFollowJaw.setParent(self.jaw)

        self.headLowerLip = pm.duplicate(self.headUpperLip, parentOnly=True)[0]
        self.headLowerLip.renameNode(name=self.TipName, base='%sLowerLipJA_bnd')
        self.headLowerLip.setParent(self.lowerLipACON)

        self.headUpperLipAIM = pm.duplicate(self.headLowerWeight, parentOnly=True)[0]
        self.headUpperLipAIM.renameNode(name=self.TipName, base='%sHeadUpperLipAimAt')
        self.headUpperLipAIM.translateZ.set(20)
        self.headUpperLipAIM.makeIdentity(apply=True)
        self.headUpperLipAIM.setParent(self.headLowerWeight)

        self.headLowerLipAIM = pm.duplicate(self.headLowerWeight, parentOnly=True)[0]
        self.headLowerLipAIM.renameNode(name=self.TipName, base='%sHeadLowerLipAimAt')
        self.headLowerLipAIM.setParent(self.headLowerWeight)

    def create_skinJnts(self):
        #create skin Joints
        pm.select(self.loc)
        self.lowerLipJawOpenOffset = pm.joint()
        self.lowerLipJawOpenOffset.renameNode(name=self.TipName, base='%sLowerLipJawOpenOffset')
        self.lowerLipJawOpenOffset.addCon()
        self.lowerLipJawOpenOffset.getParent().setParent(self.lipFollowRig)

        pm.select(self.lowerLipJawOpenOffset.getParent())
        self.lowerLipJawOpenMulti = pm.joint()
        self.lowerLipJawOpenMulti.renameNode(name=self.TipName, base='%sLowerLipJawOpenJawOpenMulti')

        #lower Left
        self.lowerLipLf = pm.joint()
        self.lowerLipLf.renameNode(name=self.TipName, base='%sLowerLip', side='left')
        self.lowerLipLf.addCon()
        self.lowerLipLf.addXtra()
        self.lowerLipLf.getParent().translateZ.set(-0.01)

        #lower Left
        pm.select(self.lowerLipJawOpenMulti)
        self.lowerLipRt = pm.joint()
        self.lowerLipRt.renameNode(name=self.TipName, base='%sLowerLip', side='right')
        self.lowerLipRt.addCon()
        self.lowerLipRt.addXtra()
        self.lowerLipRt.getParent().translateZ.set(0.01)

        pm.select(self.loc)

        #upper Left
        self.upperLipLf = pm.joint()
        self.upperLipLf.renameNode(name=self.TipName, base='%sUpperLip', side='left')
        self.upperLipLf.setParent(self.lipFollowRig)
        self.upperLipLf.addCon()
        self.upperLipLf.addXtra()
        self.upperLipLf.getParent().translateZ.set(-0.01)

        #upper Left
        self.upperLipRt = pm.joint()
        self.upperLipRt.renameNode(name=self.TipName, base='%sUpperLip', side='right')
        self.upperLipRt.setParent(self.lipFollowRig)
        self.upperLipRt.addCon()
        self.upperLipRt.addXtra()
        self.upperLipRt.getParent().translateZ.set(0.01)

        pm.delete(self.loc)

    def constrain_lipJnts(self):
        #constrain system
        #ori and aim for follow rig

        self.oriUpper = constraint.Constraint(driven=self.headUpperWeight,
                              drivers=[self.jaw, self.lipFollowRig],
                              maintainPosition=False,
                              point=False,
                              scale=False,
                              lockWeights=False,
                              closed=False,
                              maintainOffset=True)

        self.oriLower = constraint.Constraint(driven=self.headLowerWeight,
                              drivers=[self.jaw, self.lipFollowRig],
                              maintainPosition=False,
                              point=False,
                              scale=False,
                              lockWeights=False,
                              closed=False,
                              maintainOffset=True)

        #aims
        self.aimUpper = constraint.Constraint(driven=self.lowerLipFollow,
                              drivers=self.headUpperLipAIM,
                              maintainPosition=False,
                              point=False,
                              orient=False,
                              scale=False,
                              aim=True,
                              lockWeights=False,
                              closed=False,
                              offset=(0, 0, 0),
                              aimVector=(0, 0, 1),
                              upVector=(0, 0, 1))

        self.aimLower = constraint.Constraint(driven=self.upperLipFollow,
                              drivers=[self.headUpperLipAIM, self.headLowerLipAIM],
                              maintainPosition=False,
                              point=False,
                              orient=False,
                              scale=False,
                              aim=True,
                              lockWeights=False,
                              closed=False,
                              offset=(0, 0, 0),
                              aimVector=(0, 0, 1),
                              upVector=(0, 0, 1))

        #constrain for no follow rig
        self.parentUpper = constraint.Constraint(driven=self.upperLipAim,
                              drivers=self.upperLipFollowHead,
                              maintainPosition=False,
                              point=False,
                              orient=False,
                              scale=False,
                              parent=True,
                              lockWeights=False,
                              closed=False,
                              maintainOffset=True)

        self.parentLower = constraint.Constraint(driven=self.lowerLipAim,
                              drivers=self.lowerLipFollowJaw,
                              maintainPosition=False,
                              point=False,
                              orient=False,
                              scale=False,
                              parent=True,
                              lockWeights=False,
                              closed=False,
                              maintainOffset=True)

        #constrain lip side skin joint system
        constraint.Constraint(driven=self.lowerLipJawOpenOffset,
                              drivers=self.headLowerLip,
                              maintainPosition=False,
                              point=False,
                              orient=False,
                              scale=False,
                              parent=True,
                              lockWeights=False,
                              closed=False,
                              maintainOffset=True)

        for driven in [self.lowerLipLf, self.lowerLipRt]:
            constraint.Constraint(driven=driven,
                                  drivers=self.headLowerLip,
                                  maintainPosition=False,
                                  point=False,
                                  orient=False,
                                  scale=False,
                                  parent=True,
                                  lockWeights=False,
                                  closed=False,
                                  maintainOffset=True)

        for driven in [self.upperLipLf, self.upperLipRt]:
            constraint.Constraint(driven=driven,
                                  drivers=self.headUpperLip,
                                  maintainPosition=False,
                                  point=False,
                                  orient=False,
                                  scale=False,
                                  parent=True,
                                  lockWeights=False,
                                  closed=False,
                                  maintainOffset=True)

        #constrain top nodes for follow switch
        self.constraintList = list()
        for driven in [self.upperLipLf.getParent().getParent(), self.upperLipRt.getParent().getParent()]:
            self.constraintList.append(constraint.Constraint(driven=driven,
                                  drivers=self.upperLipFollowHead,
                                  maintainPosition=False,
                                  point=False,
                                  orient=False,
                                  scale=False,
                                  parent=True,
                                  lockWeights=False,
                                  closed=False,
                                  maintainOffset=True))

        for driven in [self.lowerLipLf.getParent().getParent(), self.lowerLipRt.getParent().getParent()]:
            self.constraintList.append(constraint.Constraint(driven=driven,
                                  drivers=self.lowerLipFollowJaw,
                                  maintainPosition=False,
                                  point=False,
                                  orient=False,
                                  scale=False,
                                  parent=True,
                                  lockWeights=False,
                                  closed=False,
                                  maintainOffset=True))


    def connect_constraints(self):

        self.lipFollowRig.lockAndHide(attribute.STANDARD_ATTRIBUTES)
        self.turnOffLipRig = self.lipFollowRig.addAttr('turnOffLipRig', attributeType="double", max=1, min=0)
        self.turnOffLipRig.set(keyable=True)
        self.jawOpenValue = self.lipFollowRig.addAttr('jawOpenValue', attributeType='double')
        self.jawOpenValue.set(20, keyable=True)

        self.reverseNode = pm.shadingNode("reverse", asUtility=True)
        self.reverseNode.renameNode(name=self.TipName, base='%sReverseOnOffLipReverse')
        self.reverseNode.addTag(self.lipFollowRig)

        #connect turnOffLipRig
        self.lipFollowRig.turnOffLipRig.connect(self.oriUpper.getWeights()[0])
        self.lipFollowRig.turnOffLipRig.connect(self.oriUpper.getWeights()[1])
        self.lipFollowRig.turnOffLipRig.connect(self.oriLower.getWeights()[0])
        self.lipFollowRig.turnOffLipRig.connect(self.oriLower.getWeights()[1])

        self.lipFollowRig.turnOffLipRig.connect(self.aimUpper.getWeights()[0])
        self.lipFollowRig.turnOffLipRig.connect(self.aimLower.getWeights()[0])
        self.lipFollowRig.turnOffLipRig.connect(self.aimLower.getWeights()[1])

        self.lipFollowRig.turnOffLipRig.connect(self.reverseNode.inputX)
        self.reverseNode.outputX.connect(self.parentUpper.getWeights()[0])
        self.reverseNode.outputX.connect(self.parentLower.getWeights()[0])

        for constraint in self.constraintList:
            self.reverseNode.outputX.connect(constraint.getWeights()[0])

        self.lipFollowRig.turnOffLipRig.set(1)

    def connect_lipSystem(self):
        self.multUpperPos = pm.shadingNode("multiplyDivide", asUtility=True)
        self.multUpperPos.renameNode(name=self.TipName, base='%sHeadUpperLipPos')
        self.multUpperPos.addTag(self.lipFollowRig)

        self.multUpperFollow = pm.shadingNode("multiplyDivide", asUtility=True)
        self.multUpperFollow.renameNode(name=self.TipName, base='HeadUpperLipFollow%s')
        self.multUpperFollow.addTag(self.lipFollowRig)

        self.multLowerPos = pm.shadingNode("multiplyDivide", asUtility=True)
        self.multLowerPos.renameNode(name=self.TipName, base='%sHeadLowerLipPos')
        self.multLowerPos.addTag(self.lipFollowRig)

        self.multLowerFollow = pm.shadingNode("multiplyDivide", asUtility=True)
        self.multLowerFollow.renameNode(name=self.TipName, base='%sHeadLowerLipFollow')
        self.multLowerFollow.addTag(self.lipFollowRig)

        self.reverseLowerPos = pm.shadingNode("reverse", asUtility=True)
        self.reverseLowerPos.renameNode(name=self.TipName, base='%sHeadLowerPos')
        self.reverseLowerPos.addTag(self.lipFollowRig)

        self.jaw.translate.connect(self.multUpperPos.input1)
        self.multUpperPos.output.connect(self.multUpperFollow.input1)
        self.multUpperFollow.output.connect(self.upperLipTrans.translate)
        self.multUpperPos.input2.set((0.5, 0.5, 0.5))

        self.jaw.translateY.connect(self.multLowerPos.input1.input1Y)
        self.multLowerPos.output.connect(self.reverseLowerPos.input)
        self.multLowerPos.outputY.connect(self.multLowerFollow.input1Y)
        self.multLowerPos.input2.set((0.5, 0.5, 0.5))

        self.jaw.translateX.connect(self.multLowerFollow.input1X)
        self.jaw.translateZ.connect(self.multLowerFollow.input1Z)
        self.reverseLowerPos.output.connect(self.multLowerFollow.input2)
        self.multLowerFollow.output.connect(self.lowerLipTrans.translate)

        #create system for side lip joints
        self.remapJawOpen = pm.shadingNode('remapColor', asUtility=True)
        self.remapJawOpen.renameNode(name=self.TipName, base='%sLowerLipJawOpenMulti')
        self.remapJawOpen.addTag(self.lipFollowRig)

        self.multJawOpen = pm.shadingNode('multiplyDivide', asUtility=True)
        self.multJawOpen.renameNode(name=self.TipName, base='%sLowerLipJawOpenMulti')
        self.multJawOpen.addTag(self.lipFollowRig)

        pm.connectAttr(self.lipFollowRig.jawOpenValue, self.remapJawOpen.red[0].red_Position)
        self.remapJawOpen.red[0].red_FloatValue.set(2)
        self.remapJawOpen.red[0].red_Interp.set(1)
        self.remapJawOpen.outColorR.connect(self.multJawOpen.input2X)
        self.lowerLipJawOpenOffset.translateZ.connect(self.multJawOpen.input1X)
        self.multJawOpen.outputX.connect(self.lowerLipJawOpenMulti.translateZ)

        pm.removeMultiInstance(self.remapJawOpen.red[1], b=True)

        #set 1 to 0
        self.remapJawOpen.red[1].red_FloatValue.set(0)
        self.remapJawOpen.red[1].red_Position.set(0)
        self.remapJawOpen.red[1].red_Interp.set(1)

    def clamp_sideLipJnts(self):
        pm.transformLimits(self.lowerLipLf.getParent(), translationZ=(0,0), enableTranslationZ=(0, 1))
        pm.transformLimits(self.lowerLipLf, translationZ=(0,0), enableTranslationZ=(0, 1))
        pm.transformLimits(self.lowerLipRt.getParent(), translationZ=(0,0), enableTranslationZ=(1, 0))
        pm.transformLimits(self.lowerLipRt, translationZ=(0,0), enableTranslationZ=(1, 0))

        pm.transformLimits(self.upperLipLf.getParent(), translationZ=(0,0), enableTranslationZ=(0, 1))
        pm.transformLimits(self.upperLipLf, translationZ=(0,0), enableTranslationZ=(0, 1))
        pm.transformLimits(self.upperLipRt.getParent(), translationZ=(0,0), enableTranslationZ=(1, 0))
        pm.transformLimits(self.upperLipRt, translationZ=(0,0), enableTranslationZ=(1, 0))
