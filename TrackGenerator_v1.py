import maya.cmds as mc
import math

#from PySide2 import QtWidget as qt

#myWindow = qt.QWidget

#myWindow.show()

def create_track(tempCurve = 'nurbsCircle1', ribbonWidth = 0.75, vehicleWidth = 2.0, jointCount = 12,
                 trackSegmentCount = 120, ctrl = 'CTRL_track_main', prefix = 'track',
                 trackSegmentModel = 'Geo_TrackSegment', side = 'Left', controlMode = None):

    #Create groups
    ribbonGrp = mc.createNode('transform', name = 'grp_{}_{}_Ribbon'.format(prefix, side))
    ctrlGrp = mc.createNode('transform', name = 'gr_{}_{}_RibbonCtrls'.format(prefix, side), parent = ribbonGrp)
    jntGrp = mc.createNode('transform', name = 'grp_{}_{}_RibbonJnts'.format(prefix, side), parent = ribbonGrp)
    locGrp = mc.createNode('transform', name='grp_{}_{}_RibbonLoc'.format(prefix,side), parent=ribbonGrp)

    #Contain nodes that need to follow the system's transform
    nodesLocalGrp = mc.createNode('transform', name = 'grp_{}_{}_RibbonNodesLocal'.format(prefix, side), parent = ribbonGrp)
    mc.setAttr('{}.visibility'.format(nodesLocalGrp), 0)

    #Contain nodes that do not need to follow the system's transform
    nodesWorldGrp = mc.createNode('transform', name = 'grp_{}_{}_RibbonNodesWorld'.format(prefix, side), parent = ribbonGrp)
    mc.setAttr('{}.inheritsTransform'.format(nodesWorldGrp), 0)
    mc.setAttr('{}.visibility'.format(nodesWorldGrp), 0)


    #Create 2 nurbs to form surface
    sideFlag = -1.0 if side == 'Left' else 1.0
    mc.setAttr('{}.translateZ'.format(tempCurve), sideFlag * vehicleWidth*0.5)

    tempCurveDuplicate = mc.duplicate(tempCurve)[0]
    mc.setAttr('{}.translateZ'.format(tempCurveDuplicate), sideFlag * (vehicleWidth*0.5 + ribbonWidth))

    #loft surface
    surface = mc.loft(tempCurveDuplicate, tempCurve, constructionHistory = False, uniform = True, degree = 3, sectionSpans = 1, range = False, polygon = 0,
                      name = '{}_{}_surf_trackRibbon'.format(prefix, side))[0]
    mc.parent(surface, nodesLocalGrp)

    #Create follicles on surface
    folGrp = mc.createNode('transform', name = 'grp_{}_{}_RibbonFollicles'.format(prefix, side),
                           parent = nodesWorldGrp)
    

    mc.setAttr('{}.translateZ'.format(tempCurve), 0)

    
    



    #Get surface's shape node and create Run parameter
    surfaceShapeNode = mc.listRelatives(surface, shapes = True)[0]
    ctrlNode = ctrl
    mc.addAttr(ctrlNode, longName = 'Run', keyable = True)

    # Extract a curve from lofted surface for motion path
    curveFromSurfaceName = '{}_{}_curveFromSurfaceIso'.format(prefix, side)
    curveFromSurfaceNode = mc.createNode('curveFromSurfaceIso', name = curveFromSurfaceName)

    #Ensure this function get the curve in surface's v direction
    mc.setAttr('{}.isoparmDirection'.format(curveFromSurfaceNode), 1)  # 0 = U direction, 1 = V direction

    mc.connectAttr('{}.worldSpace[0]'.format(surfaceShapeNode), '{}.inputSurface'.format(curveFromSurfaceNode))

    curveShapeName = '{}_{}_curveShape'.format(prefix, side)
    curveShapeNode = mc.createNode('nurbsCurve', name = curveShapeName)

    curveNode = mc.listRelatives(curveShapeNode, parent = True)
    mc.rename(curveNode, '{}_{}_curve'.format(prefix, side))

    mc.connectAttr('{}.outputCurve'.format(curveFromSurfaceNode),'{}.create'.format(curveShapeNode))



    #The principle of follicle: when you create a follicle node, you will create a follicle shape node and a follicle transform node.
    #shape node get the information of inputsurface, and you can set parameter U, parameter V here
    #transform node get the transform information of shape node, and put the follicle to right place accourding to parameter U&V
    jnts = []
    for i in range(jointCount):
        folShape = mc.createNode('follicle', name = 'fol_{}_{}_Ribbon_Shape_{}'.format(prefix, side, i+1))

        #rename follicle transform node
        fol = mc.listRelatives(folShape, parent = True)[0]
        fol = mc.rename(fol, 'fol_{}_{}_Ribbon_{}'.format(prefix, side, i+1))
        mc.parent(fol, folGrp)

        #connect surface to fol shape
        mc.connectAttr('{}.worldSpace[0]'.format(surfaceShapeNode), '{}.inputSurface'.format(folShape))
        
        #connect fol shape's translate & rotation to fol transform
        mc.connectAttr('{}.outTranslate'.format(folShape), '{}.translate'.format(fol))
        mc.connectAttr('{}.outRotate'.format(folShape), '{}.rotate'.format(fol))
        
        #set fol shape's uv value
        mc.setAttr('{}.parameterV'.format(folShape), 1.0/(jointCount - 1) * i)
        mc.setAttr('{}.parameterU'.format(folShape), 0.5)

        #Create Joint
        jnt = mc.createNode('joint', name = 'jnt_{}_{}_Ribbon_{}'.format(prefix, side, i+1))
        jntZeroGrp = mc.createNode('transform', name = 'Zero_{}_{}_Ribbon_{}'.format(prefix, side, i+1),
                      parent = jntGrp)
        mc.parent(jnt, jntZeroGrp)

        #Move joints to follicles
        mc.delete(mc.parentConstraint(fol, jntZeroGrp, maintainOffset = False))

        #Put joints in a list for binding
        jnts.append(jnt)


        # Genrate Wheel CTRL
        # Create a cube curve
        ribbonCTRLRadius = 0.1
        ribbonCTRL = mc.curve(d=1, p=[
            (-ribbonCTRLRadius, -ribbonCTRLRadius, -ribbonCTRLRadius),
            (-ribbonCTRLRadius, -ribbonCTRLRadius, ribbonCTRLRadius),
            (-ribbonCTRLRadius, ribbonCTRLRadius, ribbonCTRLRadius),
            (-ribbonCTRLRadius, ribbonCTRLRadius, -ribbonCTRLRadius),
            (-ribbonCTRLRadius, -ribbonCTRLRadius, -ribbonCTRLRadius),
            (ribbonCTRLRadius, -ribbonCTRLRadius, -ribbonCTRLRadius),
            (ribbonCTRLRadius, -ribbonCTRLRadius, ribbonCTRLRadius),
            (-ribbonCTRLRadius, -ribbonCTRLRadius, ribbonCTRLRadius),
            (-ribbonCTRLRadius, ribbonCTRLRadius, ribbonCTRLRadius),
            (ribbonCTRLRadius, ribbonCTRLRadius, ribbonCTRLRadius),
            (ribbonCTRLRadius, -ribbonCTRLRadius, ribbonCTRLRadius),
            (ribbonCTRLRadius, -ribbonCTRLRadius, -ribbonCTRLRadius),
            (ribbonCTRLRadius, ribbonCTRLRadius, -ribbonCTRLRadius),
            (-ribbonCTRLRadius, ribbonCTRLRadius, -ribbonCTRLRadius),
            (-ribbonCTRLRadius, ribbonCTRLRadius, ribbonCTRLRadius),
            (ribbonCTRLRadius, ribbonCTRLRadius, ribbonCTRLRadius),
            (ribbonCTRLRadius, ribbonCTRLRadius, -ribbonCTRLRadius)
        ], name=f"CTRL_Ribbon_{i}")

        # Set the cube curve's color based on the side
        if side == "Left":
            color = 6  # Index for Light Blue
        elif side == "Right":
            color = 13  # Index for Red
        else:
            color = 17  # Default to Yellow for other cases
        
        # Apply color override
        mc.setAttr(f"{ribbonCTRL}.overrideEnabled", 1)
        mc.setAttr(f"{ribbonCTRL}.overrideColor", color)

        # Move cube curve to wheelJnt's position
        mc.delete(mc.pointConstraint(jnt, ribbonCTRL, maintainOffset=False))

        # Create a group for wheelJnt
        ribbonCTRLGroup = mc.createNode("transform", name=f"Zero_Wheel_{i}")
        mc.delete(mc.pointConstraint(jnt, ribbonCTRLGroup, maintainOffset=False))

        # Parent wheelJnt to the group
        mc.parent(ribbonCTRL, ribbonCTRLGroup)

        # Point constrain the wheel to the cube curve
        mc.pointConstraint(ribbonCTRL, jnt, maintainOffset=False)

     
    # Bind Joints to Lofted Suface
    if mc.objExists(surface) and all(mc.objExists(jnt) for jnt in jnts) and controlMode == 'TrackSurfaceControl':
        mc.select(jnts)
        mc.select(surface, add=True)
        mc.skinCluster(toSelectedBones=True, name="TrackSurfaceSkinCluster")


    locList = []
    aimConstraintNodeList = []

    for i in range(trackSegmentCount):

        VValue = (1.0/trackSegmentCount) * i

        #Create Locators
        locatorName = '{}_{}_loc_{}'.format(prefix, side, i)
        loc = mc.spaceLocator(name = locatorName)[0]

        #Put loc into list
        locList.append(loc)
        mc.parent(loc, locGrp)
        mc.setAttr('{}.visibility'.format(loc), 0)


        #record the default parameter V value (default position) of locators
        mc.addAttr(loc, longName = 'default_VValue', keyable = True)
        mc.setAttr('{}.default_VValue'.format(loc), VValue)


        mc.addAttr(loc, longName = 'runInt', at = 'long', keyable = True)


        #Use Run value and shrink it to make the motion smaller
        mdNodeName = '{}_{}_md_{}'.format(prefix, side, i)
        mdNode = mc.createNode('multiplyDivide', name = mdNodeName)

        mc.connectAttr('{}.Run'.format(ctrlNode), '{}.input1X'.format(mdNode))
        mc.setAttr('{}.input2X'.format(mdNode), 0.01)

        #Create plusMinusAverage Node to calculate the value that default parameterU value + Run value, output to parameterU(new position move to)
        pmaName = '{}_{}_pma_{}'.format(prefix, side, i)
        pmaNode = mc.createNode('plusMinusAverage', name = pmaName)

        mc.connectAttr('{}.outputX'.format(mdNode), '{}.input1D[0]'.format(pmaNode))
        mc.connectAttr('{}.default_VValue'.format(loc), '{}.input1D[1]'.format(pmaNode))

        #Use a plusMinusAverage node to get the number of rotation
        pmaGetIntName = '{}_{}_pmaGetInt_{}'.format(prefix, side, i)
        pmaGetIntNode = mc.createNode('plusMinusAverage', name = pmaGetIntName)

        mc.connectAttr('{}.output1D'.format(pmaNode), '{}.runInt'.format(loc))

        #Use a condition node to get the run int
        conditionName = '{}_{}_condition_{}'.format(prefix, side, i)
        conditionNode = mc.createNode('condition', name = conditionName)

        mc.connectAttr('{}.output1D'.format(pmaNode), '{}.firstTerm'.format(conditionNode))
        mc.connectAttr('{}.runInt'.format(loc), '{}.secondTerm'.format(conditionNode))
        mc.setAttr('{}.operation'.format(conditionNode), 2)

        mc.connectAttr('{}.runInt'.format(loc), '{}.colorIfTrueR'.format(conditionNode))

        # Use a pma node to caculate runInt - 1
        pmaMinusOneName = '{}_{}_pmaMinusOne_{}'.format(prefix, side, i)
        pmaMinusOneNode = mc.createNode('plusMinusAverage', name = pmaMinusOneName)

        mc.connectAttr('{}.runInt'.format(loc),'{}.input1D[0]'.format(pmaGetIntNode))
        mc.setAttr('{}.input1D[1]'.format(pmaGetIntNode), -1)

        mc.connectAttr('{}.output1D'.format(pmaGetIntNode), '{}.colorIfFalseR'.format(conditionNode))

        # Create a pma node to get final number of rotations
        pmaGetNumberName = '{}_{}_pmaGetNumber_{}'.format(prefix, side, i)
        pmaGetNumberNode = mc.createNode('plusMinusAverage', name = pmaGetNumberName)

        mc.connectAttr('{}.output1D'.format(pmaNode), '{}.input1D[0]'.format(pmaGetNumberNode))
        mc.connectAttr('{}.outColorR'.format(conditionNode), '{}.input1D[1]'.format(pmaGetNumberNode))

        mc.setAttr('{}.operation'.format(pmaGetNumberNode), 2)


        # Create MotionPath node
        motionPathName = '{}_{}_motionPath_{}'.format(prefix, side, i)
        motionPathNode = mc.createNode('motionPath', name = motionPathName)

        mc.connectAttr('{}.worldSpace[0]'.format(curveShapeNode), '{}.geometryPath'.format(motionPathNode))
        mc.connectAttr('{}.allCoordinates'.format(motionPathNode), '{}.translate'.format(loc))

        mc.connectAttr('{}.output1D'.format(pmaGetNumberNode), '{}.uValue'.format(motionPathNode))

        mc.setAttr('{}.fractionMode'.format(motionPathNode), 1)




        #Duplicate and put track segment model to locs
        trackSegmentName = '{}_{}_Segment_{}'.format(prefix, side, i)
        newTrackSegment = mc.duplicate(trackSegmentModel, name = trackSegmentName)

        mc.makeIdentity(newTrackSegment, apply=True, translate=True, rotate=True, scale=True, normal=False)
        mc.delete(newTrackSegment, constructionHistory=True)

        mc.parentConstraint(loc, newTrackSegment, weight = 1, maintainOffset = False)    


        #######---------------------------------------------------#######
        # Locators' rotation part
        #Create Target Locator to aim constraint locators' rotation
        aimConstraintName = '{}_{}_aimConstraint_{}'.format(prefix, side, i)
        aimConstraintNode = mc.createNode('aimConstraint', name = aimConstraintName)

        #put aim constraint node to list
        aimConstraintNodeList.append(aimConstraintNode)


        # Create PointOnSurfaceInfo
        surfaceInfoNodeName = '{}_{}_pointOnSurfaceInfo_{}'.format(prefix, side, i)
        surfaceInfoNode = mc.createNode('pointOnSurfaceInfo', name = surfaceInfoNodeName)

        # Create ClosestPointOnSurfaceInfo
        closestPointOnSurfaceName = '{}_{}_closestPointOnSurface_{}'.format(prefix, side, i)
        closestPointOnSurfaceNode = mc.createNode('closestPointOnSurface', name = closestPointOnSurfaceName)  

        mc.connectAttr('{}.worldSpace[0]'.format(surfaceShapeNode),'{}.inputSurface'.format(closestPointOnSurfaceNode))
        mc.connectAttr('{}.translate'.format(loc),'{}.inPosition'.format(closestPointOnSurfaceNode)) 

        mc.connectAttr('{}.parameterU'.format(closestPointOnSurfaceNode),'{}.parameterU'.format(surfaceInfoNode))
        mc.connectAttr('{}.parameterV'.format(closestPointOnSurfaceNode),'{}.parameterV'.format(surfaceInfoNode))

        mc.connectAttr('{}.worldSpace[0]'.format(surfaceShapeNode), '{}.inputSurface'.format(surfaceInfoNode))
        mc.connectAttr('{}.normal'.format(surfaceInfoNode), '{}.worldUpVector'.format(aimConstraintNode))

        mc.connectAttr('{}.constraintRotate'.format(aimConstraintNode), '{}.rotate'.format(loc))

    
    for i in range(trackSegmentCount):

        if i == trackSegmentCount - 1:
            aimLoc = locList[0]
        
        else:
            aimLoc = locList[i + 1]
        
        pmaAimVectorName = '{}_{}_pmaAimVector_{}'.format(prefix, side, i)
        pmaAimVectorNode = mc.createNode('plusMinusAverage', name = pmaAimVectorName)

        mc.connectAttr('{}.translate'.format(aimLoc), '{}.input3D[0]'.format(pmaAimVectorNode))
        mc.connectAttr('{}.translate'.format(locList[i]), '{}.input3D[1]'.format(pmaAimVectorNode))

        mc.setAttr('{}.operation'.format(pmaAimVectorNode), 2)

        mc.connectAttr('{}.output3D'.format(pmaAimVectorNode), '{}.target[0].targetTranslate'.format(aimConstraintNodeList[i]))


    #Return Main ctrl node
    return ctrlNode, surface, ribbonGrp

def drivewheelList(ctrlNode, surface, ribbonGrp, wheelList = [], side = 'Left', controlMode = 'WheelControl'):

    #Drive the Wheels via Run parameter
     # 计算 nurbsCircle1 的周长 L
    circumference = mc.arclen("nurbsCircle1")
    
    wheelJnts = []

    for index, wheel in enumerate(wheelList):
        # 检查指定的物体是否存在
        if not mc.objExists(wheel):
            print(f"Object '{wheel}' does not exist.")
            return
        
        # Lock the Rotate X and Rotate Y to avoid Gimbal Lock Problem
        if mc.objExists(wheel):
            mc.setAttr(f"{wheel}.rotateX", lock=True, keyable=False)
            mc.setAttr(f"{wheel}.rotateY", lock=True, keyable=False)
        
        # 获取物体的形状节点
        wheelShapeNode = mc.listRelatives(wheel, shapes=True)[0]
        
        
        # 获取半径和高度（假设它是一个圆柱体）
        if mc.objectType(wheelShapeNode) == "mesh":
            # 获取 bounding box (包围盒) 尺寸
            bbox = mc.exactWorldBoundingBox(wheel)
            height = bbox[4] - bbox[1]  # Y 轴上的高度
            radius = abs(bbox[3] - bbox[0]) / 2  # 计算 X 轴上宽度的一半作为半径
            
            # 计算包围盒中心作为位置
            position = [
                (bbox[0] + bbox[3]) / 2,  # X 轴中心
                (bbox[1] + bbox[4]) / 2,  # Y 轴中心
                (bbox[2] + bbox[5]) / 2   # Z 轴中心
            ]
            
        elif mc.objectType(wheelShapeNode) == "nurbsSurface":
            # 对于 NURBS 圆柱，可以获取半径直接属性（如果适用）
            radius = mc.getAttr(f"{wheelShapeNode}.radius")
            height = mc.getAttr(f"{wheelShapeNode}.heightRatio") * 2 * radius  # 计算高度
            
            # 使用包围盒中心获取位置
            bbox = mc.exactWorldBoundingBox(wheel)
            position = [
                (bbox[0] + bbox[3]) / 2,  # X 轴中心
                (bbox[1] + bbox[4]) / 2,  # Y 轴中心
                (bbox[2] + bbox[5]) / 2   # Z 轴中心
            ]
        else:
            print(f"Object '{wheel}' is not a cylinder or compatible wheelShapeNode.")
            return
        
        # 创建新的圆柱并设置相同的半径和高度
        new_cylinder = mc.polyCylinder(radius=radius, height=height, sx=20, sy=1, sz=1)[0]
        
        # 移动新圆柱到指定位置
        mc.xform(new_cylinder, worldSpace=True, translation=position)

        mc.xform(new_cylinder, worldSpace=True, rotation=(90, 0, 0))
        mc.makeIdentity(new_cylinder, apply=True, translate=True, rotate=True, scale=True, normal=False)
        
        print(f"Created a new cylinder '{new_cylinder}' at position {position} with radius {radius} and height {height}.")
        mc.setAttr('{}.visibility'.format(new_cylinder), 0)

        #Link track's Run attibute to wheel's rotation

        # Create a joint at the same position as the wheel
        jntName = f"JNT_{side}_Wheel_{index}"
        wheelJnt = mc.createNode("joint", name=jntName)
        mc.setAttr('{0}.radius'.format(wheelJnt), 2.0)
        wheelJnts.append(wheelJnt)

        # Match joint's position to the wheel's position
        mc.delete(mc.pointConstraint(wheel, wheelJnt))

        # Create joint for wheel rotation
        rotationJntName = f"rotation_JNT_{side}_Wheel_{index}"
        wheelRotationJnt = mc.createNode("joint", name=rotationJntName)

        mc.delete(mc.pointConstraint(wheel, wheelRotationJnt))

        # Bind the wheel to the rotation joint
        mc.skinCluster(wheelRotationJnt, wheel, toSelectedBones=True)

        # Make the rotation joint follow the elevation of wheelJnt
        mc.pointConstraint(wheelJnt, wheelRotationJnt, maintainOffset=True)


        
        # 计算系数 1.8L / (pi * radius)
        coefficient = (1.8 * circumference) / (math.pi * radius) % 360.0
        
        # 创建 multiplyDivide 节点来存储计算的结果
        md_node = mc.createNode("multiplyDivide", name=f"{wheel}_runMultiplier")
        mc.setAttr(f"{md_node}.input2X", coefficient)  # 将系数设置为 input2X
        
        # 将 Run 属性连接到 multiplyDivide 节点的 input1X
        mc.connectAttr(f"{ctrlNode}.Run", f"{md_node}.input1X")

        
        # 将 multiplyDivide 节点的输出连接到 wheel 的旋转属性（假设为 rotateZ）
        #mc.connectAttr(f"{md_node}.outputX", f"{wheel}.rotateZ")

        # Connect multiplyDivide output to joint's Rotate Z
        mc.connectAttr(f"{md_node}.outputX", f"{wheelRotationJnt}.rotateZ")

        # Genrate Wheel CTRL
        # Create a cube curve
        wheelCTRL = mc.curve(d=1, p=[
            (-radius, -radius, -radius),
            (-radius, -radius, radius),
            (-radius, radius, radius),
            (-radius, radius, -radius),
            (-radius, -radius, -radius),
            (radius, -radius, -radius),
            (radius, -radius, radius),
            (-radius, -radius, radius),
            (-radius, radius, radius),
            (radius, radius, radius),
            (radius, -radius, radius),
            (radius, -radius, -radius),
            (radius, radius, -radius),
            (-radius, radius, -radius),
            (-radius, radius, radius),
            (radius, radius, radius),
            (radius, radius, -radius)
        ], name=f"CTRL_Wheel_{index}")

        # Set the cube curve's color based on the side
        if side == "Left":
            color = 6  # Index for Light Blue
        elif side == "Right":
            color = 13  # Index for Red
        else:
            color = 17  # Default to Yellow for other cases
        
        # Apply color override
        mc.setAttr(f"{wheelCTRL}.overrideEnabled", 1)
        mc.setAttr(f"{wheelCTRL}.overrideColor", color)

        # Move cube curve to wheelJnt's position
        mc.delete(mc.pointConstraint(wheelJnt, wheelCTRL, maintainOffset=False))

        # Create a group for wheelJnt
        wheelCTRLGroup = mc.createNode("transform", name=f"Zero_Wheel_{index}")
        mc.delete(mc.pointConstraint(wheelJnt, wheelCTRLGroup, maintainOffset=False))

        # Parent wheelJnt to the group
        mc.parent(wheelCTRL, wheelCTRLGroup)

        # Point constrain the wheel to the cube curve
        mc.pointConstraint(wheelCTRL, wheelJnt, maintainOffset=False)
        

    #Track Deformation while moving wheels
    # Create a skinCluster for all wheel joints and the surface
    if wheelJnts and mc.objExists(surface) and controlMode == 'WheelControl':
        mc.select(wheelJnts)
        mc.select(surface, add=True)
        mc.skinCluster(toSelectedBones=True, name="WheelSkinCluster")
    


import maya.cmds as mc

def create_ui():
    # Check if the window already exists
    if mc.window("trackSystemUI", exists=True):
        mc.deleteUI("trackSystemUI")

    # Create a new window
    window = mc.window("trackSystemUI", title="Track System UI", widthHeight=(400, 400))
    mc.columnLayout(adjustableColumn=True, rowSpacing=10)

    # Dropdown menu for side selection
    mc.rowLayout(numberOfColumns=2, adjustableColumn=2, columnAlign=(1, 'right'), columnAttach=[(1, 'both', 0), (2, 'both', 5)])
    mc.text(label="Select Side:")
    side_option = mc.optionMenu("sideMenu")
    mc.menuItem(label="Left")
    mc.menuItem(label="Right")
    mc.setParent('..')

    # Input field for Track Shape Curve
    mc.rowLayout(numberOfColumns=2, adjustableColumn=2, columnAlign=(1, 'right'), columnAttach=[(1, 'both', 0), (2, 'both', 5)])
    mc.text(label="Track Shape Curve:")
    track_shape_curve = mc.textField("trackShapeCurveField")
    mc.setParent('..')

    # Input field for Track Segment
    mc.rowLayout(numberOfColumns=2, adjustableColumn=2, columnAlign=(1, 'right'), columnAttach=[(1, 'both', 0), (2, 'both', 5)])
    mc.text(label="Track Segment:")
    track_segment = mc.textField("trackSegmentField")
    mc.setParent('..')

    # Input field for Wheels
    mc.rowLayout(numberOfColumns=2, adjustableColumn=2, columnAlign=(1, 'right'), columnAttach=[(1, 'both', 0), (2, 'both', 5)])
    mc.text(label="Wheels (comma-separated):")
    wheels = mc.textField("wheelsField")
    mc.setParent('..')

    # Input field for Vehicle Width
    mc.rowLayout(numberOfColumns=2, adjustableColumn=2, columnAlign=(1, 'right'), columnAttach=[(1, 'both', 0), (2, 'both', 5)])
    mc.text(label="Vehicle Width:")
    vehicle_width = mc.floatField("vehicleWidthField", value=2.0)
    mc.setParent('..')

    # Dropdown menu for Control Mode
    mc.rowLayout(numberOfColumns=2, adjustableColumn=2, columnAlign=(1, 'right'), columnAttach=[(1, 'both', 0), (2, 'both', 5)])
    mc.text(label="Control Mode:")
    control_mode_option = mc.optionMenu("controlModeMenu")
    mc.menuItem(label="Wheel Control")
    mc.menuItem(label="Track Surface Control")
    mc.setParent('..')

    # Create buttons to run the script
    mc.button(label="Create Track System", command=lambda _: create_track_from_ui())

    mc.showWindow(window)

def create_track_from_ui():
    # Get values from UI
    side = mc.optionMenu("sideMenu", query=True, value=True)
    temp_curve = mc.textField("trackShapeCurveField", query=True, text=True)
    track_segment_model = mc.textField("trackSegmentField", query=True, text=True)
    wheels_input = mc.textField("wheelsField", query=True, text=True)
    vehicle_width = mc.floatField("vehicleWidthField", query=True, value=True)
    control_mode_ui = mc.optionMenu("controlModeMenu", query=True, value=True)

    # Map UI control mode to script values
    control_mode = "WheelControl" if control_mode_ui == "Wheel Control" else "TrackSurfaceControl"

    # Convert wheels input into a list
    wheel_list = [wheel.strip() for wheel in wheels_input.split(",") if wheel.strip()]

    # Validation
    if not mc.objExists(temp_curve):
        mc.warning(f"Curve '{temp_curve}' does not exist!")
        return

    if not mc.objExists(track_segment_model):
        mc.warning(f"Track segment model '{track_segment_model}' does not exist!")
        return

    for wheel in wheel_list:
        if not mc.objExists(wheel):
            mc.warning(f"Wheel '{wheel}' does not exist!")
            return

    # Call the main functions
    ctrl_node, surface, ribbon_grp = create_track(
        tempCurve=temp_curve,
        ribbonWidth=0.75,
        vehicleWidth=vehicle_width,
        jointCount=12,
        trackSegmentCount=120,
        ctrl="CTRL_track_main",
        prefix="track",
        trackSegmentModel=track_segment_model,
        side=side,
        controlMode=control_mode
    )

    drivewheelList(
        ctrlNode="CTRL_track_main",
        surface=surface,
        ribbonGrp=ribbon_grp,
        wheelList=wheel_list,
        side=side,
        controlMode=control_mode
    )

# Show the UI
create_ui()



ctrlNodeR, surfaceR, ribbonGrpR = create_track(tempCurve = 'nurbsCircle1', ribbonWidth = 0.75, vehicleWidth = 2.0, 
                        jointCount = 12, trackSegmentCount = 120, ctrl = 'CTRL_track_main', prefix = 'track', side = 'Right', controlMode = 'WheelControl')
drivewheelList(ctrlNode = 'CTRL_track_main', surface = surfaceR, ribbonGrp = ribbonGrpR,
               wheelList = ['Geo_R_Gear', 
                            'GEO_R_Wheel_A_01', 'GEO_R_Wheel_B_01', 'GEO_R_Wheel_A_02', 'GEO_R_Wheel_B_02', 'GEO_R_Wheel_B_03',
                            'Geo_R_Idler'],
                            controlMode = 'WheelControl')

#Geo_R_Gear, GEO_R_Wheel_A_01, GEO_R_Wheel_B_01, GEO_R_Wheel_A_02, GEO_R_Wheel_B_02, GEO_R_Wheel_B_03, Geo_R_Idler

ctrlNodeL, surfaceL, ribbonGrpL = create_track(tempCurve = 'nurbsCircle1', ribbonWidth = 0.75, vehicleWidth = 2.0, 
                        jointCount = 12, trackSegmentCount = 120, ctrl = 'CTRL_track_main', prefix = 'track', side = 'Left', controlMode = 'WheelControl')
drivewheelList(ctrlNode = 'CTRL_track_main', surface = surfaceL, ribbonGrp = ribbonGrpL,
               wheelList = ['Geo_L_Gear', 
                            'GEO_L_Wheel_A_01', 'GEO_L_Wheel_B_01', 'GEO_L_Wheel_A_02', 'GEO_L_Wheel_B_02', 'GEO_L_Wheel_B_03',
                            'Geo_L_Idler'],
                            controlMode = 'WheelControl')