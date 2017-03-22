#********************************************************************************************************************************
# $Id: tailTentacleSystem.py 52150 2017-03-09 20:36:19Z marissa $
#*******************************************************************************
import pymel.core as pm
import maya.mel as mel

from tip.maya.studio.core import *
from tip.maya.studio.nodetypes import attribute
from tip.maya.studio.nodetypes import dagNode
from tip.maya.studio.tipModules import jointChain
from tip.maya.studio.tipModules import controller
from tip.maya.puppet.rigging import ribbonSpine
from tip.maya.studio.animation import joint

class TailTentacleSystem():
    def __init__(self,
                 startJnt,
                 name=None,
                 numFollicles=40,
                 muscle=False,
                 slide=False,
                 wave=False,
                 scale=False):

        # ERRORCHECK ARGS
        try:

            # errorchecks for mel, forces puppet objects to be strings
            self.jntChain = jointChain.JointChain(startJnt, recursive=True)

        except error.ArgumentError, err:
            raise error.ArgumentError, err

        except error.MayaNodeError, err:
            raise error.MayaNodeError, err

        ##########################
        # COMPILE NAMING
        if name:
            self.TipName = naming.TipName(name=name)
        else:
            self.TipName = naming.TipName(name=self.jntChain[0])

        #init variables because sometimes a joint chain will be passed in
        self.autoJnt = None
        self.fkJnts = list()
        self.conJnts = list()
        self.bndJnts = list()
        self.AJnts = list()
        self.BJnts = list()
        self.CJnts = list()
        self.boxAControls = list()
        self.boxBControls = list()
        self.boxCControls = list()

        #Check if it's already a tentacle jnt chain
        passed = self.checkJntChain()
        #get correct chain length
        if passed:
            if self.jntChain[0].hasAttr("FK"):
                self.jntChain = jointChain.JointChain(self.jntChain[0].getParent(), recursive=True, endJoints=self.AJnts)
            else:
                self.jntChain = jointChain.JointChain(self.jntChain[0], recursive=True, endJoints=self.AJnts)
            length = self.jntChain.chainLength()
        else:
            length = self.jntChain.chainLength()

        self.createRibbonSpine(numFollicles, length)
        self.connectAllScale()

        #create joints if not already
        if not passed:
            for jnt in self.jntChain:
                jnt.rename("TEMP%s" % jnt)
            self.createControlJnts()
            self.createBndJnts()
            self.createControls()
            self.createAutoJnt()
        if muscle:
            self.create_muscleSystem()
        if slide:
            self.create_slideSystem()
        if wave:
            self.create_waveSystem()
        if scale:
            self.create_scaleSystem()

        self.weightFollicle()

        #set Color
        allJnts = jointChain.JointChain(self.fkJnts[0].getParent(), recursive=True)
        for jnt in allJnts:
            jnt.setOverrideColor(self.TipName.getColor())
        #set box color controls
        for ctrl in self.boxAControls:
            ctrl.setOverrideColor(17)
        for ctrl in self.boxBControls:
            ctrl.setOverrideColor(9)


    def checkJntChain(self):
        #get jnts into groups if it's already a tentacle hierarchy
        for jnt in self.jntChain:
            if jnt.hasAttr('BoxC'):
                self.boxCControls.append(jnt)
            elif jnt.hasAttr('BoxB'):
                self.boxBControls.append(jnt)
            elif jnt.hasAttr('FK'):
                self.fkJnts.append(jnt)
            elif jnt.find('BoxA') > -1:
                self.AJnts.append(jnt)
                if jnt.hasAttr('BoxA'):
                    self.boxAControls.append(jnt)
            elif jnt.find('Auto') > -1 and jnt.find('Con') < 0:
                self.autoJnt = jnt
            elif jnt.hasAttr('bound'):
                self.bndJnts.append(jnt)

        if self.boxAControls:
            return True
        else:
            return False


    def createRibbonSpine(self, numFollicles, length):
        rightSide = False

        for jnt in self.jntChain:
            if jnt.nodeDescriptor.get() == 'Con' and jnt.tx.get() < 0:
                rightSide = True

        if rightSide:
            percentage = -length / numFollicles
        else:
            percentage = length / numFollicles


        pm.select(self.jntChain[0])
        jnts = list()
        for x in range(0, numFollicles + 2):
            jnts.append(pm.joint(name='tempJnt_%s' % x))
            jnts[-1].tx.set(percentage)
        jnts[0].tx.set(-percentage/2)
        jnts[0].setParent(world=True)

        #get correct orientation
        jnts[1].setParent(world=True)
        jnts[0].jointOrient.set(self.jntChain[0].jointOrient.get())
        for i, jnt in enumerate(jnts[1:-1]):
            jnt.setParent(jnts[i + 1 - 1])
            jnts[i + 1 + 1].setParent(world=True)
            jnt.jointOrient.set((0, 0, 0))
        jnts[-1].setParent(jnts[-2])

        ribbonJntChain = jointChain.JointChain(jnts[0], recursive=True)

        self.ribbonSystem = ribbonSpine.RibbonSpine(self.jntChain,
                                highResJnt=ribbonJntChain,
                                name=self.TipName,
                                percision=1)
        if pm.objExists(jnts[0]):
            pm.delete(jnts[0])

    def connectAllScale(self):
        try:
            allScale = checks.stringToPyNode('allScaleN_bnd')
            rootLocalScale = checks.stringToPyNode('rootAllLocalScale_1')
            for fol in self.ribbonSystem.folList:
                allScale.scaleX.connect(fol.scaleX)
                allScale.scaleX.connect(fol.scaleY)
                allScale.scaleX.connect(fol.scaleZ)
                fol.scale.set(lock=True)

                for rel in fol.listRelatives(children=True):
                    if rel.find('Shape') < 0:
                        rootLocalScale.scaleX.connect(rel.scaleX, lock=True)
                        rootLocalScale.scaleX.connect(rel.scaleY, lock=True)
                        rootLocalScale.scaleX.connect(rel.scaleZ, lock=True)
                        rel.listRelatives(children=True)[0].segmentScaleCompensate.set(0)

        except:
            pm.warning('allScale does not exist. Cannot connect allScale to follicle Scale')

    def createControlJnts(self):
        controlShape = controller.Controller(controlShape='circle',
                                             positionNode=self.jntChain[0],
                                             orientationNode=self.jntChain[0])
        pm.xform(controlShape, scale=(2, 4, 4))
        controlShape.makeIdentity(apply=True)

        for i, jnt in enumerate(self.jntChain):
            pm.select(jnt)
            self.fkJnts.append(pm.joint())
            self.fkJnts[-1].renameNode(name=self.TipName, index=chr(ord('A') + i))
            self.fkJnts[-1].addCon()
            self.fkJnts[-1].addTagPreset('bound')
            self.fkJnts[-1].addTag('FK')
            self.fkJnts[-1].renameShapeNodes()

            if i:
                self.fkJnts[-1].getParent().setParent(self.fkJnts[-2])

            shapes = jnt.listRelatives(shapes=True)
            if shapes:
                for shape in shapes:
                    shape.copyShapes(self.fkJnts[-1])
            else:
                pm.delete(pm.pointConstraint(self.fkJnts[-1], controlShape, maintainOffset=False))
                controlShape.copyShapes(self.fkJnts[-1])


        pm.delete(controlShape)
        self.fkJnts[0].getParent().setParent(world=True)
        pm.delete(self.jntChain)


    def createBndJnts(self):
        letters = naming.MEL_LETTERS
        letterCount = 0
        for i, jnt in enumerate(self.fkJnts):
            if i == len(self.fkJnts) - 1:
                max = 1
            else:
                max = 4
            for j in range(0, max):
                pm.select(jnt)
                self.conJnts.append(pm.joint())
                self.conJnts[-1].renameNode(name=self.TipName,
                                            base='%s%sBoxA' % (self.TipName.base, letters[letterCount]),
                                            descriptor='con',
                                            descriptorAlpha='A')
                self.conJnts[-1].overrideDisplayType.set(2)

                self.AJnts.append(pm.joint())
                self.AJnts[-1].renameNode(name=self.TipName,
                                          base='%s%sBoxA' % (self.TipName.base, letters[letterCount]),
                                          index=chr(ord('A') + i))

                self.BJnts.append(pm.joint())
                self.BJnts[-1].renameNode(name=self.TipName,
                                          base='%s%sBoxB' % (self.TipName.base, letters[letterCount]),
                                          index=chr(ord('A') + i))

                self.CJnts.append(pm.joint())
                self.CJnts[-1].renameNode(name=self.TipName,
                                      base='%s%sBoxC' % (self.TipName.base, letters[letterCount]),
                                      index=chr(ord('A') + i))

                self.bndJnts.append(pm.joint())
                self.bndJnts[-1].renameNode(name=self.TipName,
                                            base='%s%s' % (self.TipName.base, letters[letterCount]),
                                            index=chr(ord('A') + i))

                #create hierarchy of bnd jnts
                self.AJnts[-1].addTagPreset('bound')
                self.BJnts[-1].addTagPreset('bound')
                self.CJnts[-1].addTagPreset('bound')
                self.AJnts[-1].addTag('ignorePointConstraint')
                self.AJnts[-1].addTag('ignoreOrientConstraint')
                self.BJnts[-1].addTag('ignorePointConstraint')
                self.BJnts[-1].addTag('ignoreOrientConstraint')
                self.CJnts[-1].addTag('ignorePointConstraint')
                self.CJnts[-1].addTag('ignoreOrientConstraint')
                self.CJnts[-1].addTag('BoxC')
                letterCount += 1

            if max > 1:
                pm.delete(pm.pointConstraint(jnt, self.fkJnts[i+1], self.conJnts[-2], maintainOffset=False))
                pm.delete(pm.pointConstraint(jnt, self.conJnts[-2], self.conJnts[-3], maintainOffset=False))
                pm.delete(pm.pointConstraint(self.conJnts[-2], self.fkJnts[i+1], self.conJnts[-1], maintainOffset=False))


    def createControls(self):
        boxShape = controller.Controller(controlShape='box',
                                         positionNode=self.fkJnts[0],
                                         orientationNode=self.fkJnts[0])
        pm.xform(boxShape, scale=(2, 5, 5))
        for x in range(0, len(self.conJnts) + 1, 4):
            pm.delete(pm.pointConstraint(self.AJnts[x], boxShape, maintainOffset=False))
            boxShape.makeIdentity(apply=True)
            boxShape.copyShapes(self.AJnts[x])
            self.boxAControls.append(self.AJnts[x])
            self.AJnts[x].renameShapeNodes()

        pm.delete(boxShape)

        #glitch with pymel makes you create the control again to freeze the transformation
        boxShape = controller.Controller(controlShape='box',
                                            positionNode=self.fkJnts[0],
                                            orientationNode=self.fkJnts[0])
        pm.xform(boxShape, scale=(1.5, 3, 3))
        boxShape.makeIdentity(apply=True)
        for x in range(0, len(self.conJnts) + 1, 2):
            pm.delete(pm.pointConstraint(self.BJnts[x], boxShape, maintainOffset=False))
            boxShape.makeIdentity(apply=True)
            boxShape.copyShapes(self.BJnts[x])
            self.boxBControls.append(self.BJnts[x])
            self.BJnts[x].renameShapeNodes()
        for ctrl in self.boxAControls:
            ctrl.addTag('BoxA')
        for ctrl in self.boxBControls:
            ctrl.addTag('BoxB')

        pm.delete(boxShape)


    def createAutoJnt(self):
        pm.select(self.fkJnts[-1])
        self.autoJnt = pm.joint()
        self.autoJnt.renameNode(name=self.TipName, base='%sAuto')
        self.autoJnt.addTagPreset('bound')
        self.autoJnt.addTag('ignorePointConstraint')
        self.autoJnt.addTag('ignoreOrientConstraint')

        autoControl = controller.Controller(controlShape='sun',
                                            positionNode=self.autoJnt,
                                            orientationNode=self.autoJnt)
        autoControl.makeIdentity(apply=True)
        autoControl.setParent(self.fkJnts[-1])
        autoControl.tx.set(3)
        autoControl.rz.set(90)
        self.autoJnt.addCon()
        autoControl.copyShapes(self.autoJnt)
        self.autoJnt.getParent().setParent(self.conJnts[-1].listRelatives(allDescendents=True)[0])
        pm.delete(autoControl)
        self.autoJnt.lockAndHide(attribute.STANDARD_ATTRIBUTES)
        self.autoJnt.radi.set(channelBox=False)


    def weightFollicle(self):
        pm.select(clear=True)
        for jnt in self.bndJnts:
            pm.select(jnt, add=True)
        pm.select(self.ribbonSystem.nurbsPatch, add=True)
        pm.skinCluster(toSelectedBones=True)


    def create_muscleSystem(self):
        smoothAttr = attribute.addAttr(self.autoJnt, 'smooth', attributeType='float', min=0, max=10, default=0)
        node = mel.eval('cMuscle_makeMuscleSystem(%s)'% self.ribbonSystem.nurbsPatch)
        muscleSystem = checks.stringToPyNode(node)

        smoothAttr.connect(muscleSystem.enableSticky)
        smoothAttr.connect(muscleSystem.enableSmooth)


    def create_slideSystem(self):
        slideAttr = attribute.addAttr(self.autoJnt, 'slide', attributeType='double', min=0, max=10, defaultValue=0, keyable=True)
        slideMD = pm.shadingNode('multiplyDivide', asUtility=True, name=self.autoJnt + '_MD')
        slideREV = pm.shadingNode('reverse', asUtility=True, name=self.autoJnt + '_REV')

        slideAttr.connect(slideMD.input1X)
        slideMD.operation.set(2)
        slideMD.input2X.set(10)
        slideMD.outputX.connect(slideREV.inputX)


        for fol in self.ribbonSystem.folList:
            shapeRel = pm.listRelatives(fol, shapes=True)[0]
            mult = pm.shadingNode("multiplyDivide", asUtility=True, name=fol + "_MD")
            slideREV.outputX.connect(mult.input2X)
            mult.input1X.set(shapeRel.parameterU.get())
            mult.outputX.connect(shapeRel.parameterU)


    def create_waveSystem(self):
        horizAmp = self.autoJnt.addAttr('horizontalAmplitude', attributeType='float',
                                     min=-5, max=5, defaultValue=0, keyable=True)
        horizWaveLength = self.autoJnt.addAttr('horizontalWaveLength', attributeType='float',
                                            min=-.01, max=1, defaultValue=1, keyable=True)
        vertAmp = self.autoJnt.addAttr('verticalAmplitude', attributeType='float',
                                    min=-5, max=5, defaultValue=0, keyable=True)
        vertWaveLength = self.autoJnt.addAttr('verticalWaveLength', attributeType='float',
                                           min=-.01, max=1, defaultValue=1, keyable=True)

        #horizontal deformer
        horizontalWave, horizontalWaveHandle = pm.nonLinear(self.ribbonSystem.nurbsPatch, type='wave')
        horizontalWave.renameNode(name=self.TipName, base="%sWaveDeformerHorizontal_1")
        horizontalWaveHandle.renameNode(name=self.TipName, base="%sWaveDeformerHorizontal_1")

        #vertical deformer
        verticalWave, verticalWaveHandle = pm.nonLinear(self.ribbonSystem.nurbsPatch, type='wave')
        verticalWave.renameNode(name=self.TipName, base="%sWaveDeformerHorizontal")
        verticalWaveHandle.renameNode(name=self.TipName, base="%sWaveDeformerHorizontal")

        pm.delete(pm.orientConstraint(self.fkJnts[0], horizontalWaveHandle, maintainOffset=False))
        pm.delete(pm.orientConstraint(self.fkJnts[0], verticalWaveHandle, maintainOffset=False))

        horizontalWaveHandle.rx.set(horizontalWaveHandle.rx.get() + 90)

        horizAmp.connect(horizontalWave.amp)
        horizWaveLength.connect(horizontalWave.wav)
        vertAmp.connect(verticalWave.amp)
        vertWaveLength.connect(verticalWave.wav)


    def create_scaleSystem(self):
        #get location of follicles relative to all the joints
        locList = list()
        for i, jnt in enumerate(self.ribbonSystem.folJntList):
            jnt.segmentScaleCompensate.set(0)

            locList.append(pm.group(em=True, name='tempFollicle_' + str(i)))
            locList[-1].matchTo(jnt)
            locList[-1].setParent(self.boxAControls[0])
        #get location of box A controls
        controlLocList = list()
        for con in self.boxAControls:
            controlLocList.append(pm.group(em=True, name='tempLoc_' + con))
            pm.delete(pm.parentConstraint(con, controlLocList[-1], maintainOffset=False))
            controlLocList[-1].setParent(self.boxAControls[0])
        controlLocList[0].tx.set(0)

        #parent locs to understand which follicles fall under each box A control
        for loc in locList:
            for i, jnt in enumerate(controlLocList):
                tempList = list()
                if controlLocList[1].tx.get() < 0:
                    if i < (len(controlLocList) - 1):
                        if loc.tx.get() < jnt.tx.get() and loc.tx.get() > controlLocList[i + 1].tx.get():
                            loc.setParent(jnt)
                    else:
                        if loc.tx.get() < jnt.tx.get():
                            loc.setParent(jnt)
                else:
                    if i < (len(controlLocList) - 1):
                        if loc.tx.get() > jnt.tx.get() and loc.tx.get() < controlLocList[i + 1].tx.get():
                            loc.setParent(jnt)
                    else:
                        if loc.tx.get() > jnt.tx.get():
                            loc.setParent(jnt)
        #just in case there's a follicle before or after the chain
        locList[0].setParent(controlLocList[0])
        locList[-1].setParent(controlLocList[-2])

        #create System
        numFollicles = 0
        for i, con in enumerate(self.boxAControls):
            multListA = list()
            multListB = list()
            pmaList = list()
            children = controlLocList[i].listRelatives(children=True)
            if children:
                percentage = 100/len(children) *.01
            else:
                percentage = 0
            curPercent = 0
            for x in range(numFollicles, numFollicles + len(children)):
                multA = pm.shadingNode('multiplyDivide', asUtility=True)
                multA.renameNode(name=self.TipName, base='%s%sScaleUp' % (self.TipName.base, self.ribbonSystem.folJntList[x]))

                multB = pm.shadingNode('multiplyDivide', asUtility=True)
                multB.renameNode(name=self.TipName, base='%s%sScaleDown' % (self.TipName.base, self.ribbonSystem.folJntList[x]))
                pma = pm.shadingNode('plusMinusAverage', asUtility=True,
                                     name=self.ribbonSystem.folJntList[x] + '_scalePMA_1')
                pma.renameNode(name=self.TipName, base='%s%sScale' % (self.TipName.base, self.ribbonSystem.folJntList[x]))

                self.boxAControls[i].scale.connect(multA.input1)
                self.boxAControls[i+1].scale.connect(multB.input1)
                pma.input3D[0].set((0, 0, 0))
                pma.input3D[1].set((0, 0, 0))
                multA.output.connect(pma.input3D[0])
                multB.output.connect(pma.input3D[1])

                if curPercent > 1:
                    curPercent = 1
                multA.input2.set((1 - curPercent, 1 - curPercent, 1 - curPercent))
                multB.input2.set((curPercent, curPercent, curPercent))
                pma.output3Dy.connect(self.ribbonSystem.folJntList[x].getParent().scaleY)
                pma.output3Dz.connect(self.ribbonSystem.folJntList[x].getParent().scaleZ)
                curPercent += percentage
            numFollicles += (len(children))


        pm.delete(controlLocList)



