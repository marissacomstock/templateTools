#*******************************************************************************
# Copyright (c) 2007 Tippett Studio. All rights reserved.
# $Id$
#*******************************************************************************

import pymel.core as pm

from tip.maya.studio.nodetypes import dependNode

def createSpineShapes():
    spineCurves = ["hipShape", "splitShape", "chestShape"]
    if pm.objExists("spineShapes"):
        spineGroup = pm.ls("spineShapes")
    else:
        spineGroup = pm.group(em=True, name="spineShapes")
        if pm.objExists("miscGroup_bnd"):
            spineGroup.setParent("miscGroup_bnd")

    yTrans = 0
    for spine in spineCurves:
        if not pm.objExists(spine):
            crv = pm.curve(name=spine, degree=1, p=[(10, 1, 10), (-10, 1, 10), (-10, 1, -10), (10, 1, -10), (10, 1, 10), (10, -1, 10), (-10, -1, 10),
                (-10, 1, 10), (-10, -1, 10), (-10, -1, -10), (-10, 1, -10), (-10, -1, -10), (10, -1, -10), (10, 1, -10), (10, -1, -10), (10, -1, 10)])

            pm.xform(crv, translation=(0, yTrans, 0), scale = (1, 2, 1))
            crv.makeIdentity(apply=True)
            pm.makeIdentity(spine, apply=True)
            yTrans += 10
            crv.setOverrideColor(crv, 17)
            crv.setParent(spineGroup)
        else:
            pm.warning("%s already exists" %spine)
     
    pm.select(clear=True)
    for spine in spineCurves:
        if pm.objExists(spine):
            pm.select(spine, add=True)

