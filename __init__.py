# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Draw2Paint",
    "author": "CDMJ,Lapineige, Spirou4D",
    "version": (3, 8, 0),
    "blender": (4, 1, 0),
    "location": "UI > Draw2Paint",
    "description": "2D Paint in 3D View, Mask Manipulation",
    "warning": "",
    "category": "Paint",
}

import bpy
import bmesh

##### main operators grouped

########### props

########PBRA Adopted

bpy.types.Scene.x_min_pixels = bpy.props.IntProperty(min=0,
                 description="Minimum X value (in pixel) for the render border")
bpy.types.Scene.x_max_pixels = bpy.props.IntProperty(min=0,
                 description="Maximum X value (in pixel) for the render border")
bpy.types.Scene.y_min_pixels = bpy.props.IntProperty(min=0,
                 description="Minimum Y value (in pixel) for the render border")
bpy.types.Scene.y_max_pixels = bpy.props.IntProperty(min=0,
                 description="Maximum Y value (in pixel) for the render border")


########### propertygroup

class MyProperties(bpy.types.PropertyGroup):
    my_string: bpy.props.StringProperty(name="Enter Text")

    # my_float_vector : bpy.props.FloatVectorProperty(name= "Scale", soft_min= 0,
    # soft_max= 1000, default= (1,1,1))
    my_float: bpy.props.FloatProperty(name="CVP Influence", min=0,
                                      max=1.0, default=0.0)

    my_enum: bpy.props.EnumProperty(
        name="",
        description="Choose Curve To Draw",
        items=[('OP1', "Draw Curve", ""),
               ('OP2', "Draw Vector", ""),
               ('OP3', "Draw Square", ""),
               ('OP4', "Draw Circle", "")
               ]
    )


####brush scenes and sculpt scenes

class D2P_OT_MacroCreateBrush(bpy.types.Operator):
    """Image Brush Scene Setup Macro"""
    bl_idname = "d2p.create_brush"
    bl_label = "Setup Scene for Image Brush Maker"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        scene = context.scene
        # add new scene and name it 'Brush'
        bpy.ops.scene.new(type='LINK_COPY')
        bpy.context.scene.name = "Brush"

        bpy.context.scene.render.engine = 'CYCLES'
        bpy.data.worlds[0]

        bpy.ops.object.camera_add(
            align='VIEW',
            enter_editmode=False,
            location=(0, 0, 4),
            rotation=(0, 0, 0)
        )
        # rename selected camera and set to ortho
        bpy.context.object.name = "Tex Camera"
        bpy.context.object.data.type = 'ORTHO'

        # change scene size to 1K
        bpy.context.scene.render.resolution_x = 1024
        bpy.context.scene.render.resolution_y = 1024
        bpy.context.scene.render.resolution_percentage = 100
        # save scene size as preset
        bpy.ops.render.preset_add(name="1K Texture")
        # change to camera view
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                override = bpy.context.copy()
                override['area'] = area
                bpy.ops.view3d.view_camera()  # view3d.view_axis
                break  # this will break the loop after it is first ran

        return {'FINISHED'}


class D2P_OT_CustomFps(bpy.types.Operator):
    """Slow Play FPS"""
    bl_idname = "d2p.slow_play"
    bl_label = "Slow Play FPS Toggle"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = obj.type == 'MESH'
            B = context.mode == 'SCULPT'
            return A and B

    def execute(self, context):
        scene = context.scene
        F = scene.render.fps

        if F == 1:
            scene.render.fps = 30
            scene.render.fps_base = 1
        else:
            scene.render.fps = 1
            scene.render.fps_base = 12

        return {'FINISHED'}


class D2P_OT_RefMakerScene(bpy.types.Operator):
    """Create Reference Scene"""
    bl_description = "Create Scene for Composing Reference Slides"
    bl_idname = "d2p.create_reference_scene"
    bl_label = "Create Scene for Image Reference"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        for sc in bpy.data.scenes:
            if sc.name == "Refmaker":
                return False
        return context.area.type == 'VIEW_3D'

    def execute(self, context):
        _name = "Refmaker"
        for sc in bpy.data.scenes:
            if sc.name == _name:
                return {'FINISHED'}

        bpy.ops.scene.new(type='NEW')
        context.scene.name = _name
        # add camera to center and move up 4 units in Z
        bpy.ops.object.camera_add(view_align=False,
                                  enter_editmode=False,
                                  location=(0, 0, 4),
                                  rotation=(0, 0, 0)
                                  )

        context.object.name = _name + " Camera"  # rename selected camera

        # change scene size to HD
        _RenderScene = context.scene.render
        _RenderScene.resolution_x = 1920
        _RenderScene.resolution_y = 1080
        _RenderScene.resolution_percentage = 100

        # save scene size as preset
        bpy.ops.render.preset_add(name=_name)

        # change to camera view
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                override = bpy.context.copy()
                override['area'] = area
                bpy.ops.view3d.viewnumpad(override, type='CAMERA')
                break

        return {'FINISHED'}


# ------------------------ D2P SCENE
class D2P_OT_D2PaintScene(bpy.types.Operator):
    """Create Draw2Paint Scene"""
    bl_description = "Create Scene for Working in Draw2Paint"
    bl_idname = "d2p.create_d2p_scene"
    bl_label = "Create Scene for Draw2Paint"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        for sc in bpy.data.scenes:
            if sc.name == "Draw2Paint":
                return False
        return context.area.type == 'VIEW_3D'

    def execute(self, context):
        _name = "Draw2Paint"
        for sc in bpy.data.scenes:
            if sc.name == _name:
                return {'FINISHED'}

        bpy.ops.scene.new(type='NEW')
        context.scene.name = _name

        # set to top view
        bpy.ops.view3d.view_axis(type='TOP', align_active=True)
        # set to Eevee
        bpy.context.scene.render.engine = 'BLENDER_EEVEE'

        return {'FINISHED'}


# sculpt the new duplicated canvas
class D2P_OT_SculptView(bpy.types.Operator):
    """Sculpt View Reference Camera"""
    bl_idname = "d2p.sculpt_camera"
    bl_label = "Sculpt Camera"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = obj.type == 'MESH'
            B = context.mode == 'SCULPT'
            return A and B

    def execute(self, context):
        scene = context.scene

        bpy.ops.object.camera_add(align='VIEW',
                                  enter_editmode=False,
                                  location=(0, -4, 0),
                                  rotation=(1.5708, 0, 0)
                                  )
        context.object.name = "Reference Cam"  # add camera to front view
        context.object.data.show_passepartout = False
        context.object.data.lens = 80
        bpy.ops.view3d.object_as_camera()

        # change to camera view
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                override = bpy.context.copy()
                override['area'] = area
                # bpy.ops.view3d.viewnumpad(override, type='CAMERA')
                bpy.ops.view3d.camera_to_view()
                break
        scene.render.resolution_x = 1920
        scene.render.resolution_y = 1080

        bpy.context.object.data.show_name = True

        # collection for sculpt reference

        return {'FINISHED'}


#################### shader applications
###############test material holdout generator
class D2P_OT_holdout_shader(bpy.types.Operator):
    bl_label = "Mask Holdout Shader"
    bl_idname = "d2p.add_holdout"

    @classmethod
    def poll(self, context):
        obj = context.active_object
        A = obj is not None
        if A:
            B = obj.type == 'CURVE' or 'MESH'
            return B

    def execute(self, context):
        mask = bpy.data.materials.new(name="Holdout Mask")
        mask.use_nodes = True

        bpy.context.object.active_material = mask

        mask = bpy.data.materials.new(name="Holdout Mask")

        mask.use_nodes = True

        bpy.context.object.active_material = mask

        ###output node new
        # output = mask.node_tree.nodes.get('ShaderNodeOutputMaterial')
        material_output = bpy.context.active_object.active_material.node_tree.\
                                                nodes.get('Material Output')

        # Principled Main Shader in Tree
        principled_node = mask.node_tree.nodes.get('Principled BSDF')
        mask.node_tree.nodes.remove(principled_node)

        ###Tex Coordinate Node
        hold = mask.node_tree.nodes.new('ShaderNodeHoldout')
        hold.location = (-100, 0)
        hold.label = ("Holdout Mask")

        # output = mask.node_tree.nodes.new('ShaderNodeOutputMaterial')
        # newout = mask.node_tree.nodes.new('ShaderNodeOutputMaterial')

        #####LINKING
        link = mask.node_tree.links.new

        link(hold.outputs[0], material_output.inputs[0])

        return {'FINISHED'}


class D2P_OT_CanvasMaterial(bpy.types.Operator):
    """Adopt Canvas Material"""
    bl_idname = "d2p.canvas_material"
    bl_label = "Set the Material to the same as Main Canvas"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = obj.type == 'MESH' or 'CURVE'
            B = context.mode == 'OBJECT' or 'PAINT_TEXTURE'
            return A and B

    def execute(self, context):
        scene = context.scene

        obj = context.active_object
        canvas = bpy.data.objects['canvas'].material_slots[0].material
        obj.data.materials.append(canvas)

        return {'FINISHED'}


######################## sculpt to liquid
class D2P_OT_SculptDuplicate(bpy.types.Operator):
    """Duplicate Selected Image Plane, Single User for Eraser Paint"""
    bl_idname = "d2p.sculpt_duplicate"
    bl_label = "Sculpt Liquid Duplicate"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene

        bpy.ops.paint.texture_paint_toggle()
        #all this was pulled to the left for pep-8, need to test if ok
        bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":
                                   False, "mode": 'TRANSLATION'},
          TRANSFORM_OT_translate={"value": (0, 0, 0), "orient_axis_ortho": 'X',
                                  "orient_type": 'GLOBAL',
                                  "orient_matrix": ((0, 0, 0), (0, 0, 0),
                                                    (0, 0, 0)),
                                  "orient_matrix_type": 'GLOBAL',
                                  "constraint_axis": (False, False, False),
                                  "mirror": False,
                                  "use_proportional_edit": False,
                                  "proportional_edit_falloff": 'SMOOTH',
                                  "proportional_size": 1,
                                  "use_proportional_connected": False,
                                  "use_proportional_projected": False, "snap":
                                      False,
                                  "snap_target": 'CLOSEST', "snap_point":
                                      (0, 0, 0),
                                  "snap_align": False, "snap_normal": (0, 0, 0),
                                  "gpencil_strokes": False, "cursor_transform":
                                      False,
                                  "texture_space": False, "remove_on_cancel":
                                      False,
                                  "view2d_edge_pan": False, "release_confirm":
                                      False,
                                  "use_accurate": False,
                                  "use_automerge_and_split": False})
        bpy.ops.transform.translate(value=(0, 0, 0.1))
        # context.object.active_material.use_shadeless = True
        # context.object.active_material.use_transparency = True
        # context.object.active_material.transparency_method = 'Z_TRANSPARENCY'
        bpy.ops.view3d.localview()
        bpy.ops.paint.texture_paint_toggle()

        # make ERASER brush or use exisitng
        try:
            context.tool_settings.image_paint.brush = bpy.data.brushes["Eraser"]
            pass
        except:
            context.tool_settings.image_paint.brush = bpy.data.brushes["TexDraw"]
            bpy.ops.brush.add()
            bpy.data.brushes["TexDraw.001"].name = "Eraser"
            # context.scene.tool_settings.unified_\
                          #paint_settings.use_pressure_size = False
            bpy.data.brushes["Eraser"].use_pressure_strength = False
            bpy.data.brushes["Eraser"].blend = 'ERASE_ALPHA'

        # make individual of material AND of image reference inside
        sel = bpy.context.active_object
        mat = sel.material_slots[0].material
        sel.material_slots[0].material = mat.copy()

        material = sel.material_slots[0].material
        node = material.node_tree.nodes['Image Texture']
        new_image = node.image.copy()
        node.image = new_image

        return {'FINISHED'}


class D2P_OT_SculptLiquid(bpy.types.Operator):
    """Convert to Subdivided Plane & Sculpt Liquid"""
    bl_idname = "d2p.sculpt_liquid"
    bl_label = "Sculpt like Liquid"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        # main_canvas = obj.name

        if obj is not None:
            A = context.active_object.type == 'MESH'
            # B = context.active_object.name == obj.name[0]+ '.001'
            return A  # and B

    def execute(self, context):
        scene = context.scene

        bpy.ops.paint.texture_paint_toggle()
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.subdivide(number_cuts=100, smoothness=0)
        bpy.ops.mesh.subdivide(number_cuts=2, smoothness=0)
        bpy.ops.sculpt.sculptmode_toggle()
        bpy.ops.paint.brush_select(sculpt_tool='GRAB', create_missing=False)
        scene.tool_settings.sculpt.use_symmetry_x = False
        bpy.ops.view3d.localview()

        return {'FINISHED'}


############### canvas rotations
# flip horizontal macro
class D2P_OT_CanvasHoriz(bpy.types.Operator):
    """Flip the Canvas Left/Right"""
    bl_idname = "d2p.canvas_horizontal"
    bl_label = "Canvas Horizontal"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = obj.type == 'MESH'
            B = context.mode == 'PAINT_TEXTURE'
            return A and B

    def execute(self, context):
        scene = context.scene
        layer = bpy.context.view_layer
        layer.update()

        # toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()

        scene = bpy.context.scene

        original_area = bpy.context.area.type

        # toggle edit mode
        bpy.ops.object.editmode_toggle()

        #####select all mesh
        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action='SELECT')

        ####change editor to UV Editor
        bpy.context.area.ui_type = 'UV'

        # + select the uvs
        bpy.ops.uv.select_all(action='SELECT')
        bpy.ops.uv.select_all(action='SELECT')

        ######scale -1 on axis
        bpy.ops.transform.resize(value=(-1, 1, 1),
                                 orient_type='GLOBAL',
                                 orient_matrix=((1, 0, 0), (0, 1, 0),
                                                (0, 0, 1)),
                                 orient_matrix_type='GLOBAL',
                                 constraint_axis=(True, False, False),
                                 mirror=True, use_proportional_edit=False,
                                 proportional_edit_falloff='SMOOTH',
                                 proportional_size=1,
                                 use_proportional_connected=False,
                                 use_proportional_projected=False)

        # back to Object mode
        bpy.ops.object.editmode_toggle()

        #####return to original window editor
        bpy.context.area.type = original_area

        bpy.ops.paint.texture_paint_toggle()

        return {'FINISHED'}


# --------------------------------flip vertical macro

class D2P_OT_CanvasVertical(bpy.types.Operator):
    """Flip the Canvas Top/Bottom"""
    bl_idname = "d2p.canvas_vertical"
    bl_label = "Canvas Vertical"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = obj.type == 'MESH'
            B = context.mode == 'PAINT_TEXTURE'
            return A and B

    def execute(self, context):
        scene = context.scene
        layer = bpy.context.view_layer
        layer.update()

        # toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()

        scene = bpy.context.scene

        original_area = bpy.context.area.type

        # toggle edit mode
        bpy.ops.object.editmode_toggle()

        #####select all mesh
        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action='SELECT')

        ####change editor to UV Editor
        bpy.context.area.ui_type = 'UV'

        # + select the uvs
        bpy.ops.uv.select_all(action='SELECT')
        bpy.ops.uv.select_all(action='SELECT')

        ######scale -1 on axis
        bpy.ops.transform.resize(value=(1, -1, 1),
                                 orient_type='GLOBAL',
                                 orient_matrix=((1, 0, 0), (0, 1, 0),
                                                (0, 0, 1)),
                                 orient_matrix_type='GLOBAL',
                                 constraint_axis=(True, False, False),
                                 mirror=True, use_proportional_edit=False,
                                 proportional_edit_falloff='SMOOTH',
                                 proportional_size=1,
                                 use_proportional_connected=False,
                                 use_proportional_projected=False)

        # back to Object mode
        bpy.ops.object.editmode_toggle()

        #####return to original window editor
        bpy.context.area.type = original_area

        bpy.ops.paint.texture_paint_toggle()

        return {'FINISHED'}


# --------------------------ccw15

class D2P_OT_RotateCanvasCCW15(bpy.types.Operator):
    """Rotate Image CounterClockwise 15 degrees"""
    bl_idname = "d2p.rotate_ccw_15"
    bl_label = "Canvas Rotate CounterClockwise 15"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = obj.type == 'MESH'
            B = context.mode == 'PAINT_TEXTURE'
            return A and B

    def execute(self, context):
        scene = context.scene
        layer = bpy.context.view_layer
        layer.update()

        # toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()

        # rotate canvas 15 degrees left
        bpy.ops.transform.rotate(value=0.261799,
                                 orient_axis='Z', orient_type='GLOBAL',
                                 orient_matrix=((1, 0, 0), (0, 1, 0),
                                                (0, 0, 1)),
                                 orient_matrix_type='GLOBAL',
                                 constraint_axis=(False, False, True),
                                 mirror=True,
                                 use_proportional_edit=False,
                                 proportional_edit_falloff='SMOOTH',
                                 proportional_size=1,
                                 use_proportional_connected=False,
                                 use_proportional_projected=False)

        # toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()

        return {'FINISHED'}


# --------------------------cw15

class D2P_OT_RotateCanvasCW15(bpy.types.Operator):
    """Rotate Image Clockwise 15 degrees"""
    bl_idname = "d2p.rotate_cw_15"
    bl_label = "Canvas Rotate Clockwise 15"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = obj.type == 'MESH'
            B = context.mode == 'PAINT_TEXTURE'
            return A and B

    def execute(self, context):
        scene = context.scene
        layer = bpy.context.view_layer
        layer.update()

        # toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()

        # rotate canvas 15 degrees left
        bpy.ops.transform.rotate(value=-0.261799,
                                 orient_axis='Z', orient_type='GLOBAL',
                                 orient_matrix=((1, 0, 0), (0, 1, 0),
                                                (0, 0, 1)),
                                 orient_matrix_type='GLOBAL',
                                 constraint_axis=(False, False, True),
                                 mirror=True,
                                 use_proportional_edit=False,
                                 proportional_edit_falloff='SMOOTH',
                                 proportional_size=1,
                                 use_proportional_connected=False,
                                 use_proportional_projected=False)

        # toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()

        return {'FINISHED'}


# ---------------------------ccw 90

class D2P_OT_RotateCanvasCCW(bpy.types.Operator):
    """Rotate Image CounterClockwise 90 degrees"""
    bl_idname = "d2p.rotate_ccw_90"
    bl_label = "Canvas Rotate CounterClockwise 90"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = obj.type == 'MESH'
            B = context.mode == 'PAINT_TEXTURE'
            return A and B

    def execute(self, context):
        scene = context.scene
        layer = bpy.context.view_layer
        layer.update()

        # toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()

        # rotate canvas 90 degrees left
        bpy.ops.transform.rotate(value=1.5708,
                                 orient_axis='Z', orient_type='GLOBAL',
                                 orient_matrix=((1, 0, 0), (0, 1, 0),
                                                (0, 0, 1)),
                                 orient_matrix_type='GLOBAL',
                                 constraint_axis=(False, False, True),
                                 mirror=True,
                                 use_proportional_edit=False,
                                 proportional_edit_falloff='SMOOTH',
                                 proportional_size=1,
                                 use_proportional_connected=False,
                                 use_proportional_projected=False)

        # toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()

        return {'FINISHED'}


# -----------------------------------cw 90

class D2P_OT_RotateCanvasCW(bpy.types.Operator):
    """Rotate Image Clockwise 90 degrees"""
    bl_idname = "d2p.rotate_cw_90"
    bl_label = "Canvas Rotate Clockwise 90"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = obj.type == 'MESH'
            B = context.mode == 'PAINT_TEXTURE'
            return A and B

    def execute(self, context):
        scene = context.scene
        layer = bpy.context.view_layer
        layer.update()

        # toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()

        # rotate canvas 90 degrees left
        bpy.ops.transform.rotate(value=-1.5708,
                                 orient_axis='Z', orient_type='GLOBAL',
                                 orient_matrix=((1, 0, 0), (0, 1, 0),
                                                (0, 0, 1)),
                                 orient_matrix_type='GLOBAL',
                                 constraint_axis=(False, False, True),
                                 mirror=True,
                                 use_proportional_edit=False,
                                 proportional_edit_falloff='SMOOTH',
                                 proportional_size=1,
                                 use_proportional_connected=False,
                                 use_proportional_projected=False)

        # toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()

        return {'FINISHED'}


# --------------------------------image rotation reset

class D2P_OT_CanvasResetrot(bpy.types.Operator):
    """Reset Canvas Rotation"""
    bl_idname = "d2p.canvas_resetrot"
    bl_label = "Canvas Reset Rotation"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = obj.type == 'MESH'
            B = context.mode == 'PAINT_TEXTURE'
            return A and B

    def execute(self, context):
        scene = context.scene
        layer = bpy.context.view_layer
        layer.update()

        # reset canvas rotation
        bpy.ops.object.rotation_clear()
        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS',
                                  center='MEDIAN')

        return {'FINISHED'}


############# finally got a way to influence the camera constraint
############ ugly but works :P
# bpy.context.object.constraints["Cam Control"].influence == mytool.my_float
'''class D2P_OT_cvp_influence(bpy.types.Operator):
    """Set up influence of Camera View Paint Constraint"""
    bl_idname = "d2p.cvp_influence"
    bl_label = "CVP Influence"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = obj.type == 'MESH'
            B = context.mode == 'PAINT_TEXTURE'
            return A and B

    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool

        # deselect plane 'canvas'
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.selectable_objects
        bpy.ops.object.select_all(action='TOGGLE')

        # select camera 'Camera View Paint'
        bpy.ops.object.select_all(action='DESELECT')
        ob = bpy.data.objects["Camera View Paint"]
        bpy.context.view_layer.objects.active = ob
        # assign mytool.my_float to "cam Control" influence
        bpy.context.object.constraints["Cam Control"].\
                            influence = mytool.my_float

        # deselect camera and reselect plane 'canvas'
        bpy.context.selectable_objects
        bpy.ops.object.select_all(action='TOGGLE')

        bpy.ops.object.select_all(action='DESELECT')
        ob = bpy.data.objects["canvas"]
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.mode_set(mode='TEXTURE_PAINT')
        return {'FINISHED'}'''


######################### image ops to camera

# -----------------------------cameraview paint

class D2P_OT_CameraviewPaint(bpy.types.Operator):
    """Setup A Camera to be Parent of Canvas"""
    bl_idname = "d2p.cameraview_paint"
    bl_label = "Cameraview Paint"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = obj.type == 'MESH' and obj.name != 'canvas'
            B = context.mode == 'OBJECT'
            return A and B

    def execute(self, context):

        scene = context.scene

        # toggle on/off textpaint

        obj = context.active_object

        if obj:
            mode = obj.mode
            # aslkjdaslkdjasdas
            if mode == 'TEXTURE_PAINT':
                bpy.ops.paint.texture_paint_toggle()

        # save selected plane by rename
        bpy.context.object.name = "canvas"
        bpy.ops.object.move_to_collection(collection_index=0, is_new=True,
                                          new_collection_name="canvas view")

        # variable to get image texture dimensions -
        # thanks to Mutant Bob http://blender.stackexchange.com/users/
        # 660/mutant-bob
        # select_mat = bpy.context.active_object.data.materials[0].
        # texture_slots[0].texture.image.size[:]

        # select_mat = []

        for ob in bpy.context.scene.objects:
            for s in ob.material_slots:
                if s.material and s.material.use_nodes:
                    for n in s.material.node_tree.nodes:
                        if n.type == 'TEX_IMAGE':
                            select_mat = n.image.size[:]
                            # print(obj.name,'uses',n.image.name,'saved at',n
                            # .image.filepath)

        # add camera
        bpy.ops.object.camera_add(enter_editmode=False,
                                  align='VIEW',
                                  location=(0, 0, 0),
                                  rotation=(0, -0, 0))

        # ratio full
        bpy.context.scene.render.resolution_percentage = 100

        # name it
        bpy.context.object.name = "Camera View Paint"
        
        


        # switch to camera view
        bpy.ops.view3d.object_as_camera()

        # ortho view on current camera
        bpy.context.object.data.type = 'ORTHO'
        # move cam up in Z by 1 unit
        bpy.ops.transform.translate(value=(0, 0, 1),
                                    orient_type='GLOBAL',
                                    orient_matrix=((1, 0, 0), (0, 1, 0),
                                                   (0, 0, 1)),
                                    orient_matrix_type='GLOBAL',
                                    constraint_axis=(False, False, True),
                                    mirror=True,
                                    use_proportional_edit=False,
                                    proportional_edit_falloff='SMOOTH',
                                    proportional_size=1,
                                    use_proportional_connected=False,
                                    use_proportional_projected=False)

        # switch on composition guides for use in cameraview paint
        # bpy.context.space_data.context = 'DATA'
        bpy.context.object.data.show_composition_thirds = True

        # found on net Atom wrote this simple script

        # image_index = 0

        rnd = bpy.data.scenes[0].render
        rnd.resolution_x, rnd.resolution_y = select_mat
        # bpy.context.object.data.ortho_scale = orthoscale

        rndx = rnd.resolution_x
        rndy = rnd.resolution_y
        # orthoscale = ((rndx - rndy)/rndy)+1

        if rndx >= rndy:
            orthoscale = ((rndx - rndy) / rndy) + 1

        elif rndx < rndy:
            orthoscale = 1

        # set to orthographic
        bpy.context.object.data.ortho_scale = orthoscale

        bpy.context.object.data.show_name = True
        bpy.context.object.data.passepartout_alpha = 0.65

        C = bpy.context

        # List of object references
        objs = C.selected_objects

        # Set target collection to a known collection
        coll_target = C.scene.collection.children.get("canvas view")

        # Set target collection based on the collection in context (selected)
        # coll_target = C.collection

        # If target found and object list not empty
        if coll_target and objs:

            # Loop through all objects
            for ob in objs:
                # Loop through all collections the obj is linked to
                for coll in ob.users_collection:
                    # Unlink the object
                    coll.objects.unlink(ob)

        # Link each object to the target collection
        coll_target.objects.link(ob)

        # hide camera itself
        bpy.ops.object.hide_view_set(unselected=False)

        bpy.context.selectable_objects

        # deselect camera
        bpy.ops.object.select_all(action='TOGGLE')
        # bpy.ops.object.select_all(action='TOGGLE')

        # select plane
        bpy.ops.object.select_all(action='DESELECT')
        ob = bpy.data.objects["canvas"]
        bpy.context.view_layer.objects.active = ob
        # fix alpha blend in eevee
        bpy.context.object.active_material.blend_method = 'HASHED'

        # selection to texpaint toggle
        bpy.ops.paint.texture_paint_toggle()
        # set to Flat Shading Solid and Textured
        bpy.context.space_data.shading.type = 'MATERIAL'

        # set to standard color
        bpy.context.scene.view_settings.view_transform = 'Standard'
        bpy.context.scene.render.film_transparent = True
        
        
        
        #can we make it parent to child canvas?
        child = bpy.data.objects["canvas"]
        parent = bpy.data.objects["Camera View Paint"]
        child.parent = parent
        child.matrix_parent_inverse = parent.matrix_world.inverted()

        return {'FINISHED'}


##################### experimental get UV layout for camera ref

##todo: set up string for file location or code to write to new file

##todo: choose UV layer (get) or make new UV layer with current smart uv

######: need second operator for placing the resulting image
# as current camera background


class D2P_OT_getuvlayout(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "d2p.getuvlayout"
    bl_label = "Get UV Layout for Selected Object"

    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = obj.type == 'MESH'
            B = context.mode == 'OBJECT'
            return A and B

    def execute(self, context):
        scene = context.scene
        layer = bpy.context.view_layer
        layer.update()

        if bpy.context.active_object.data.uv_layers:
            print("we have UVs")

        else:
            self.report({"WARNING"}, "Please Create UV Layer")
            return {"CANCELLED"}

        selObj = bpy.context.active_object

        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.select_all(action='SELECT')

        f = "C:\\tmp\\" + selObj.name
        bpy.ops.uv.export_layout(filepath=f, mode='PNG', opacity=0)
        bpy.ops.object.mode_set(mode='OBJECT')

        C = bpy.context

        # List of object references
        objs = C.selected_objects

        # Set target collection to a known collection
        coll_target = C.scene.collection.children.get("object view")
        if not coll_target:
            bpy.ops.object.move_to_collection(collection_index=0, is_new=True,
                                              new_collection_name="object view")

        # Set target collection based on the collection in context (selected)
        # coll_target = C.collection

        # If target found and object list not empty
        if coll_target and objs:

            # Loop through all objects
            for ob in objs:
                # Loop through all collections the obj is linked to
                for coll in ob.users_collection:
                    # Unlink the object
                    coll.objects.unlink(ob)

        return {'FINISHED'}


class D2P_OT_loadbgcam(bpy.types.Operator):
    """apply uv layout to Camera View Paint"""
    bl_idname = "d2p.loadbgcam"
    bl_label = "UV Layout to Camera View Paint"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = obj.type == 'MESH'
            B = context.mode == 'OBJECT'
            return A and B

    def execute(self, context):
        scene = context.scene
        # new code
        ob = bpy.context.active_object

        cam = bpy.context.scene.camera
        filepath = "C:/tmp/" + str(ob.name) + ".png"

        img = bpy.data.images.load(filepath)
        cam.data.show_background_images = True
        bg = cam.data.background_images.new()
        bg.image = img
        bg.alpha = (1.0)
        bg.display_depth = 'FRONT'

        bpy.context.selectable_objects

        # deselect plane
        bpy.ops.object.select_all(action='TOGGLE')
        # bpy.ops.object.select_all(action='TOGGLE')

        # select camera
        bpy.ops.object.select_all(action='DESELECT')
        ob = bpy.data.objects["Camera View Paint"]
        bpy.context.view_layer.objects.active = ob

        # unhide camera itself
        bpy.ops.object.hide_view_clear()

        # deselect camera
        bpy.ops.object.select_all(action='TOGGLE')
        # bpy.ops.object.select_all(action='TOGGLE')

        # select plane
        bpy.ops.object.select_all(action='DESELECT')
        ob = bpy.data.objects["canvas"]
        bpy.context.view_layer.objects.active = ob

        # selection to texpaint toggle
        bpy.ops.paint.texture_paint_toggle()

        return {'FINISHED'}


class D2P_OT_isolate_2d(bpy.types.Operator):
    """Push to Isolate 2D Paint View"""
    bl_idname = "d2p.swapcollview2d"
    bl_label = "Toggle 2D View"
    bl_options = {'REGISTER', 'UNDO'}

    # @classmethod
    # def poll(cls, context):
    # return context.active_object is not None

    def execute(self, context):
        scene = context.scene
        # new code

        eye = bpy.context.view_layer.layer_collection.children["object view"]
        sore = bpy.context.view_layer.layer_collection.children["canvas view"]
        if eye.hide_viewport == False:
            eye.hide_viewport = True
            sore.hide_viewport = False
        bpy.ops.view3d.view_camera()
        bpy.context.space_data.shading.type = 'MATERIAL'

        #bpy.context.space_data.shading.light = 'FLAT'

        return {'FINISHED'}


class D2P_OT_isolate_3d(bpy.types.Operator):
    """Push to Isolate 3D Paint View"""
    bl_idname = "d2p.swapcollview3d"
    bl_label = "Toggle 3D View"
    bl_options = {'REGISTER', 'UNDO'}

    # @classmethod
    # def poll(cls, context):
    # return context.active_object is not None

    def execute(self, context):
        scene = context.scene
        # new code

        eye = bpy.context.view_layer.layer_collection.children["object view"]
        sore = bpy.context.view_layer.layer_collection.children["canvas view"]
        if sore.hide_viewport == False:
            sore.hide_viewport = True
            eye.hide_viewport = False

        bpy.ops.view3d.view_axis(type='FRONT', align_active=True)
        bpy.context.space_data.shading.type = 'MATERIAL'

        bpy.context.space_data.shading.light = 'STUDIO'

        return {'FINISHED'}


################------------------------Precision Render Border Adjust Imported
class D2P_OT_PixelsToBorder(bpy.types.Operator):
    """ Convert the pixel value into the proportion needed
        by the Blender native property """
    bl_idname = "d2p.pixelstoborder"
    bl_label = "Convert Pixels to Border proportion"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        C = bpy.context

        X = C.scene.render.resolution_x
        Y = C.scene.render.resolution_y

        C.scene.render.border_min_x = C.scene.x_min_pixels / X
        C.scene.render.border_max_x = C.scene.x_max_pixels / X
        C.scene.render.border_min_y = C.scene.y_min_pixels / Y
        C.scene.render.border_max_y = C.scene.y_max_pixels / Y

        if C.scene.x_min_pixels > X:
            C.scene.x_min_pixels = X
        if C.scene.x_max_pixels > X:
            C.scene.x_max_pixels = X
        if C.scene.y_min_pixels > Y:
            C.scene.y_min_pixels = Y
        if C.scene.y_max_pixels > Y:
            C.scene.y_max_pixels = Y

        return {'FINISHED'}


class D2P_OT_BorderToPixels(bpy.types.Operator):
    """ Convert the Blender native property value to pixels"""
    bl_idname = "d2p.bordertopixels"
    bl_label = "Convert border values to pixels"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        C = bpy.context

        X = C.scene.render.resolution_x
        Y = C.scene.render.resolution_y

        C.scene.x_min_pixels = int(C.scene.render.border_min_x * X)
        C.scene.x_max_pixels = int(C.scene.render.border_max_x * X)
        C.scene.y_min_pixels = int(C.scene.render.border_min_y * Y)
        C.scene.y_max_pixels = int(C.scene.render.border_max_y * Y)

        return {'FINISHED'}


######################## bordercrop from ez-draw panel revised
############## haven't decided on setting this up as toggle or not,
# missing scene preferences stored in addon like ez-draw did
# ---------------------------------------------------------------BORDER CROP ON
class D2P_OT_BorderCrop(bpy.types.Operator):
    """Turn on Border Crop in Render Settings"""
    bl_description = "Border Crop ON"
    bl_idname = "d2p.border_crop"
    bl_label = ""
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        rs = context.scene.render
        rs.use_border = True
        rs.use_crop_to_border = True
        return {'FINISHED'}


# --------------------------------------------------------------BORDER CROP OFF
class D2P_OT_BorderUnCrop(bpy.types.Operator):
    """Turn off Border Crop in Render Settings"""
    bl_description = "Border Crop OFF"
    bl_idname = "d2p.border_uncrop"
    bl_label = ""
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        rs = context.scene.render
        rs.use_border = False
        rs.use_crop_to_border = False
        return {'FINISHED'}


# -------------------------------------------------------------BORDER CROP TOGGLE
class D2P_OT_BorderCropToggle(bpy.types.Operator):
    """Set Border Crop in Render Settings"""
    bl_description = "Border Crop On/Off TOGGLE"
    bl_idname = "d2p.border_toggle"
    bl_label = ""
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        return poll_apt(self, context)

    def execute(self, context):
        scene = context.scene
        rs = context.scene.render

        if not (scene.prefs_are_locked):
            if rs.use_border and rs.use_crop_to_border:
                bpy.ops.d2p.border_uncrop()
                scene.bordercrop_is_activated = False
            else:
                bpy.ops.d2p.border_crop()
                scene.bordercrop_is_activated = True
        return {'FINISHED'}


# ------------------------------try new image make
class D2P_OT_NewImage(bpy.types.Operator):
    """New Image"""
    bl_idname = "d2p.new_image"
    bl_label = "New Image"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        layer = bpy.context.view_layer
        layer.update()
        # original_type = bpy.context.area.type
        # bpy.context.area.type = 'IMAGE_EDITOR'
        # Call user prefs window
        bpy.ops.screen.userpref_show('INVOKE_DEFAULT')
        # Change area type
        area = context.window_manager.windows[-1].screen.areas[0]
        area.type = 'IMAGE_EDITOR'

        # new image
        bpy.ops.image.new()

        # bpy.context.area.type = original_type

        return {'FINISHED'}


# -----------------------------image save

class D2P_OT_SaveImage(bpy.types.Operator):
    """Save Image"""
    bl_idname = "d2p.save_current"
    bl_label = "Save Image Current"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = obj.type == 'MESH'
            B = context.mode == 'PAINT_TEXTURE'
            return A and B

    def execute(self, context):
        scene = context.scene
        layer = bpy.context.view_layer
        layer.update()
        original_type = bpy.context.area.type
        bpy.context.area.type = 'IMAGE_EDITOR'

        # return image to last saved state
        bpy.ops.image.save()

        bpy.context.area.type = original_type

        return {'FINISHED'}


####experiment fix - doesn't work yet
class D2P_OT_SaveIncrem(bpy.types.Operator):
    """Save Incremential Images - MUST SAVE SESSION FILE FIRST"""
    bl_description = ""
    bl_idname = "d2p.save_increm"
    bl_label = "Save incremential Image Current"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = obj.type == 'MESH'
            B = context.mode == 'PAINT_TEXTURE'
            return A and B

    def execute(self, context):
        scene = context.scene
        main_canvas = main_canvas_data(self, context)

        if main_canvas[0] != '':  # if main canvas isn't erased
            for obj in scene.objects:
                if obj.name == main_canvas[0]:  # if mainCanvas Mat exist
                    scene.objects.active = obj
                    break
        else:
            return {'FINISHED'}

        # init
        obj = context.active_object
        original_type = context.area.ui_type
        context.area.ui_type = 'IMAGE_EDITOR'

        # verify the brushname
        _tempName = [main_canvas[0] + '_001' + main_canvas[1]]
        _Dir = os.path.realpath(main_canvas[2])
        l = os.listdir(_Dir)
        brushesName = [f for f in l if os.path.isfile(os.path.join(_Dir, f))]
        brushesName = sorted(brushesName)

        i = 1
        for x in _tempName:
            for ob in brushesName:
                if ob == _tempName[-1]:
                    i += 1
                    _tempName = _tempName + [main_canvas[0] + '_' + \
                                             '{:03d}'.format(i) + main_canvas[1]]

        # return image to last saved state
        filepath = os.path.join(_Dir, _tempName[-1])
        ima = obj.data.materials[0].texture_slots[0].texture.image
        context.space_data.image = ima
        bpy.ops.image.save_as(filepath=filepath,
                              check_existing=False,
                              relative_path=True)

        context.area.ui_type = original_type
        return {'FINISHED'}


# -----------------------------------reload image

class D2P_OT_ImageReload(bpy.types.Operator):
    """Reload Image Last Saved State"""
    bl_idname = "d2p.reload_saved_state"
    bl_label = "Reload Image Save Point"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = obj.type == 'MESH'
            B = context.mode == 'PAINT_TEXTURE'
            return A and B

    def execute(self, context):
        original_type = context.area.ui_type
        context.area.ui_type = 'IMAGE_EDITOR'

        obdat = context.active_object.data
        ima = obdat.materials[0].texture_paint_images[0]
        context.space_data.image = ima
        bpy.ops.image.reload()  # return image to last saved state

        context.area.ui_type = original_type
        return {'FINISHED'}


########### pivot works
class D2P_OT_EmptyGuides(bpy.types.Operator):
    """experimental- create new empty guide or selected guide relocate origin"""
    bl_idname = "d2p.empty_guides"
    bl_label = "Empty Guides Constrained"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        A = obj is not None
        if A:
            B = obj.type == 'MESH' or 'EMPTY'
            return B

    def execute(self, context):

        scene = context.scene
        layer = bpy.context.view_layer
        layer.update()

        # toggle texpaint and deselect
        obj = context.active_object

        if obj == bpy.data.objects['canvas']:
            bpy.ops.paint.texture_paint_toggle()
            bpy.ops.object.select_all(action='DESELECT')
            # need check here for ['Symmetry Guide']

            for ob in bpy.data.objects:
                if ob.type == 'EMPTY' and ob.name == 'Symmetry Guide':
                    # need to set the symmmetry empty as active
                    bpy.ops.object.select_all(action='DESELECT')
                    bpy.data.objects['Symmetry Guide'].select_set(True)
                    # need to snap cursor to it
                    bpy.ops.view3d.snap_cursor_to_selected()
                    # need to set the canvas as active again
                    bpy.data.objects['Symmetry Guide'].select_set(False)
                    bpy.data.objects['canvas'].select_set(True)

                    pass
                else:
                    # add empty here
                    bpy.ops.object.empty_add(type='SPHERE', location=(0, 0, 0),
                                             radius=0.01)
                    # add empty for reference and movement of origin

                    # rename new empty to Symmetry Guide
                    bpy.context.object.name = "Symmetry Guide"

                    bpy.ops.transform.resize(value=(10, 10, 10))
                    # scale up past the normal range of image plane
                    # add constraint to follow canvas rotation
                    bpy.ops.object.parent_set(type='OBJECT', keep_transform=False)
                    
                    # snap cursor to empty
                    bpy.ops.view3d.snap_cursor_to_selected()

                    bpy.ops.object.select_all(action='DESELECT')
                    bpy.data.objects['Symmetry Guide'].select_set(False)
                    bpy.data.objects['canvas'].select_set(True)
                    bpy.context.view_layer.objects.active = \
                        bpy.data.objects['canvas']

                    bpy.ops.paint.texture_paint_toggle()

                    return {'FINISHED'}



        elif obj == bpy.data.objects['Symmetry Guide']:
            # already have empty, will work for cursors :D
            bpy.ops.view3d.snap_cursor_to_selected()

            # here to set origin of canvas
            bpy.ops.object.select_all(action='DESELECT')
            bpy.data.objects['Symmetry Guide'].select_set(False)
            bpy.data.objects['canvas'].select_set(True)
            bpy.context.view_layer.objects.active = bpy.data.objects['canvas']
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
            # bpy.ops.object.select_all(action='DESELECT')
            bpy.data.objects['canvas'].select_set(False)
            bpy.data.objects['Symmetry Guide'].select_set(True)

            # bpy.ops.paint.texture_paint_toggle()

            return {'FINISHED'}
        else:
            return {'FINISHED'}

        return {'FINISHED'}


class D2P_OT_center_object(bpy.types.Operator):
    """Snaps cursor and Selected Object to World Center"""
    bl_idname = "d2p.center_object"
    bl_label = "Center Object to World"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        # cursor to world origin
        bpy.ops.view3d.snap_cursor_to_center()
        # selected object origin to geometry - SYMMETRY GUIDE
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
        bpy.ops.view3d.snap_selected_to_cursor(use_offset=True)
        #need to deselect Guide and select canvas
        #need to toggle canvas to OBJECT MODE
        #need to set origin of canvas to cursor
        #need to toggle to texture paint
        #need guide as selected in case new move intended?
        return {'FINISHED'}


################ legacy

############################################################
# -------------------LEGACY FOR ADDITION TO PANEL OPERATORS
############################################################
# ----------------------------------------------------------------FRONT OF PAINT
class D2P_OT_FrontOfPaint(bpy.types.Operator):
    """fast front of face view paint"""
    bl_description = ""
    bl_idname = "d2p.frontof_paint"
    bl_label = "Front Of Paint"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = context.mode == 'PAINT_TEXTURE'
            B = obj.type == 'MESH'
            return A and B

    def execute(self, context):
        # init
        paint = bpy.ops.paint
        object = bpy.ops.object
        contextObj = context.object

        #context.space_data.viewport_shade = 'TEXTURED'  # texture draw
        paint.texture_paint_toggle()
        object.editmode_toggle()
        #previous was view3d.numpad()
        bpy.ops.view3d.view_axis(type='TOP', align_active=True)
        object.editmode_toggle()
        paint.texture_paint_toggle()
        contextObj.data.use_paint_mask = True
        return {'FINISHED'}


# -----------------------------------------------------------\BORDER CROP TOGGLE
class D2P_OT_BorderCropToggle(bpy.types.Operator):
    """Set Border Crop in Render Settings"""
    bl_description = "Border Crop On/Off TOGGLE"
    bl_idname = "d2p.border_toggle"
    bl_label = ""
    bl_options = {'REGISTER', 'UNDO'}

    # @classmethod
    # def poll(self, context):
    # return poll_apt(self, context)

    def execute(self, context):
        scene = context.scene
        rs = context.scene.render

        if not (scene.prefs_are_locked):
            if rs.use_border and rs.use_crop_to_border:
                bpy.ops.ez_draw.border_uncrop()
                scene.bordercrop_is_activated = False
            else:
                bpy.ops.ez_draw.border_crop()
                scene.bordercrop_is_activated = True
        return {'FINISHED'}


#################### mask specials

class D2P_OT_ReprojectMask(bpy.types.Operator):
    """Reproject Mask"""
    bl_idname = "d2p.reproject_mask"
    bl_label = "Reproject Mask to UV from Camera View"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        A = obj is not None
        if A:
            B = obj.type == 'CURVE' or 'MESH'
            return B

    def execute(self, context):
        scene = context.scene

        obj = context.active_object

        if obj.type == 'CURVE' and obj.mode == 'EDIT':

            bpy.ops.object.editmode_toggle()
            bpy.ops.object.convert(target='MESH')
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='TOGGLE')
            bpy.ops.uv.project_from_view(camera_bounds=True,
                                         correct_aspect=False,
                                         scale_to_bounds=False)
            bpy.ops.object.editmode_toggle()
            bpy.ops.paint.texture_paint_toggle()  # toggle texpaint

        elif obj.type == 'CURVE' and obj.mode == 'OBJECT':
            bpy.ops.object.convert(target='MESH')
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='TOGGLE')
            bpy.ops.uv.project_from_view(camera_bounds=True,
                                         correct_aspect=False,
                                         scale_to_bounds=False)
            bpy.ops.object.editmode_toggle()
            bpy.ops.paint.texture_paint_toggle()  # toggle texpaint

        elif obj.type == 'MESH' and obj.mode == 'OBJECT':

            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='TOGGLE')
            bpy.ops.uv.project_from_view(camera_bounds=True,
                                         correct_aspect=False,
                                         scale_to_bounds=False)
            bpy.ops.object.editmode_toggle()
            bpy.ops.paint.texture_paint_toggle()  # toggle texpaint

        elif obj.type == 'MESH' and obj.mode == 'TEXTURE_PAINT':

            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='TOGGLE')
            bpy.ops.uv.project_from_view(camera_bounds=True,
                                         correct_aspect=False,
                                         scale_to_bounds=False)

            bpy.ops.object.editmode_toggle()
            bpy.ops.paint.texture_paint_toggle()  # toggle texpaint

        return {'FINISHED'}


############## alignment of masks selected
class D2P_OT_AlignLeft(bpy.types.Operator):
    """Left Align"""
    bl_idname = "d2p.align_left"
    bl_label = "Align Objects Left"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = obj.type == 'MESH' or 'CURVE'
            B = context.mode == 'OBJECT'
            return A and B

    def execute(self, context):
        scene = context.scene

        bpy.ops.object.align(align_mode='OPT_1', \
                             relative_to='OPT_4', align_axis={'X'})
        return {'FINISHED'}


class D2P_OT_AlignCenter(bpy.types.Operator):
    """Center Align"""
    bl_idname = "d2p.align_center"
    bl_label = "Align Objects Center"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = obj.type == 'MESH' or 'CURVE'
            B = context.mode == 'OBJECT'
            return A and B

    def execute(self, context):
        scene = context.scene

        bpy.ops.object.align(align_mode='OPT_2', \
                             relative_to='OPT_4', align_axis={'X'})
        scene.mask_V_align = True
        return {'FINISHED'}


class D2P_OT_AlignRight(bpy.types.Operator):
    """Center Align"""
    bl_idname = "d2p.align_right"
    bl_label = "Align Objects Right"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = obj.type == 'MESH' or 'CURVE'
            B = context.mode == 'OBJECT'
            return A and B

    def execute(self, context):
        scene = context.scene

        bpy.ops.object.align(align_mode='OPT_3', \
                             relative_to='OPT_4', align_axis={'X'})
        return {'FINISHED'}


class D2P_OT_AlignTop(bpy.types.Operator):
    """Top Align"""
    bl_idname = "d2p.align_top"
    bl_label = "Align Objects Top"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = obj.type == 'MESH' or 'CURVE'
            B = context.mode == 'OBJECT'
            return A and B

    def execute(self, context):
        scene = context.scene

        bpy.ops.object.align(align_mode='OPT_3', \
                             relative_to='OPT_4', align_axis={'Y'})
        return {'FINISHED'}


class D2P_OT_AlignHcenter(bpy.types.Operator):
    """Horizontal Center Align"""
    bl_idname = "d2p.align_hcenter"
    bl_label = "Align Objects Horizontal Center"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = obj.type == 'MESH' or 'CURVE'
            B = context.mode == 'OBJECT'
            return A and B

    def execute(self, context):
        scene = context.scene

        bpy.ops.object.align(align_mode='OPT_2', \
                             relative_to='OPT_4', align_axis={'Y'})
        scene.mask_V_align = False
        return {'FINISHED'}


class D2P_OT_CenterAlignReset(bpy.types.Operator):
    """Center Alignment Reset"""
    bl_idname = "d2p.center_align_reset"
    bl_label = "Reset center alignment"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = obj.type == 'MESH' or 'CURVE'
            B = context.mode == 'OBJECT'
            return A and B

    def execute(self, context):
        scene = context.scene
        mva = scene.mask_V_align

        scene.mask_V_align = False if mva else True
        return {'FINISHED'}


class D2P_OT_AlignBottom(bpy.types.Operator):
    """Horizontal Bottom Align"""
    bl_idname = "d2p.align_bottom"
    bl_label = "Align Objects Horizontal Bottom"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = obj.type == 'MESH' or 'CURVE'
            B = context.mode == 'OBJECT'
            return A and B

    def execute(self, context):
        scene = context.scene

        bpy.ops.object.align(align_mode='OPT_1', \
                             relative_to='OPT_4', align_axis={'Y'})
        return {'FINISHED'}


###########new curve primitives for drawing masks

class D2P_OT_my_enum_shapes(bpy.types.Operator):
    bl_label = "Add Mask Object"
    bl_idname = "d2p.my_enum_shapes"

    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool

        if mytool.my_enum == 'OP1':
            # operators guts from draw curve
            # def execute(self, context):
            scene = context.scene
            ######### add a new curve at 0.15 Z
            bpy.ops.curve.primitive_bezier_curve_add(radius=1,
                                                     enter_editmode=False, 
                                                     align='WORLD', 
                                                     location=(0, 0, 0.15),
                                                     scale=(1, 1, 1))
            # add constraint to follow canvas rotation
            bpy.ops.object.constraint_add(type='CHILD_OF')
            bpy.context.object.constraints["Child Of"].target = \
                bpy.data.objects["canvas"]
            bpy.ops.object.editmode_toggle()
            bpy.ops.curve.delete(type='VERT')
            # need to add a material to the object and make it a holdout shader
            bpy.ops.material.new()

            bpy.ops.curve.cyclic_toggle()

            bpy.context.object.data.dimensions = '2D'
            bpy.context.object.data.fill_mode = 'BOTH'

            bpy.ops.wm.tool_set_by_id(name="builtin.draw")

        if mytool.my_enum == 'OP2':
            # operators guts from draw vector
            bpy.ops.curve.primitive_bezier_curve_add(enter_editmode=True,
                                                     align='WORLD', 
                                                     location=(0, 0, 0.15),
                                                     scale=(1, 1, 1))
            # add constraint to follow canvas rotation
            bpy.ops.object.constraint_add(type='CHILD_OF')
            bpy.context.object.constraints["Child Of"].target = \
                bpy.data.objects["canvas"]

            bpy.ops.curve.handle_type_set(type='VECTOR')
            bpy.context.object.data.dimensions = '2D'
            bpy.context.object.data.fill_mode = 'BOTH'

            bpy.ops.transform.resize(value=(0.1, 0.1, 0.1))
            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

        if mytool.my_enum == 'OP3':
            # operators guts from draw square
            bpy.ops.curve.primitive_bezier_circle_add(radius=0.25,
                                                      enter_editmode=False, 
                                                      align='WORLD', 
                                                      location=(0, 0, 0.15),
                                                      scale=(1, 1, 1))
            # add constraint to follow canvas rotation
            bpy.ops.object.constraint_add(type='CHILD_OF')
            bpy.context.object.constraints["Child Of"].target = \
                bpy.data.objects["canvas"]
            bpy.context.object.data.dimensions = '2D'
            bpy.context.object.data.fill_mode = 'BOTH'
            bpy.ops.object.editmode_toggle()
            bpy.ops.curve.handle_type_set(type='VECTOR')
            bpy.ops.transform.rotate(value=0.785398, orient_axis='Z')
            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

        if mytool.my_enum == 'OP4':
            # operators guts from draw circle
            bpy.ops.curve.primitive_bezier_circle_add(radius=0.25,
                                                      enter_editmode=False, 
                                                      align='WORLD', 
                                                      location=(0, 0, 0.15),
                                                      scale=(1, 1, 1))
            # add constraint to follow canvas rotation
            bpy.ops.object.constraint_add(type='CHILD_OF')
            bpy.context.object.constraints["Child Of"].target = \
                bpy.data.objects["canvas"]
            bpy.context.object.data.dimensions = '2D'
            bpy.context.object.data.fill_mode = 'BOTH'
            bpy.ops.object.editmode_toggle()
            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

        return {'FINISHED'}


####################### boolean masks work
class D2P_OT_RemoveMods(bpy.types.Operator):
    """Remove Modifiers"""
    bl_idname = "d2p.remove_modifiers"
    bl_label = "Remove modifiers"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = obj.type == 'MESH'
            B = context.mode == 'OBJECT'
            return A and B

    def execute(self, context):
        scene = context.scene
        # init
        obj = context.object

        bpy.ops.object.convert(target='MESH')

        '''old_mesh = obj.data  # get a reference to the current obj.data

        apply_modifiers = False  # settings for to_mesh
        new_mesh = obj.to_mesh(preserve_all_data_layers=True, depsgraph=None)
        obj.modifiers.clear()  # object will still have modifiers, remove them
        obj.data = new_mesh  # assign the new mesh to obj.data
        bpy.data.meshes.remove(old_mesh)  # remove the old mesh from the .blend
        context.object.draw_type = 'TEXTURED'''

        return {'FINISHED'}


class D2P_OT_SolidifyDifference(bpy.types.Operator):
    """Solidify and Difference Mask"""
    bl_idname = "d2p.solidify_difference"
    bl_label = "Add Solidify and Difference Bool"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = obj.type == 'MESH'
            B = context.mode == 'OBJECT'
            return A and B

    def execute(self, context):
        scene = context.scene
        context = bpy.context

        obj = context.active_object

        mod = obj.modifiers.new("Solidify", 'SOLIDIFY')
        # add a solidify modifier on active object

        mod.thickness = 0.01  # set modifier properties
        obj.location.z = 0

        for o in context.selected_objects:
            if o == obj:
                continue
            # see if there is already a modifier named  \
            # "SelectedSolidify" and use it
            mod = o.modifiers.get("SelectedSolidify")
            if mod is None:
                # otherwise add a modifier to selected object
                mod = o.modifiers.new("SelectedSolidify", 'SOLIDIFY')
                mod.thickness = 0.3
                o.location.z += 0.1
            # add a boolean mod
            # obj = context.active_object
            o.display_type = 'WIRE'

            boolmod = obj.modifiers.new("Bool", 'BOOLEAN')
            boolmod.object = o
            boolmod.solver = 'FAST'
            boolmod.operation = 'DIFFERENCE'

            return {'FINISHED'}


class D2P_OT_SolidifyUnion(bpy.types.Operator):
    """Solidify and Union Mask"""
    bl_idname = "d2p.solidify_union"
    bl_label = "Add Solidify and Union Bool"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = obj.type == 'MESH'
            B = context.mode == 'OBJECT'
            return A and B

    def execute(self, context):
        scene = context.scene
        context = bpy.context

        obj = context.active_object

        mod = obj.modifiers.new("Solidify", 'SOLIDIFY')
        # add a solidify modifier on active object

        mod.thickness = 0.01  # set modifier properties
        obj.location.z = 0

        for o in context.selected_objects:
            if o == obj:
                continue
            # see if there is already a modifier named
            # "SelectedSolidify" and use it
            mod = o.modifiers.get("SelectedSolidify")
            if mod is None:
                # otherwise add a modifier to selected object
                mod = o.modifiers.new("SelectedSolidify", 'SOLIDIFY')
                mod.thickness = 0.01
                o.location.z = 0
            # add a boolean mod
            # obj = context.active_object
            # o.display_type = 'WIRE'

            boolmod = obj.modifiers.new("Bool", 'BOOLEAN')
            boolmod.object = o
            boolmod.solver = 'FAST'
            boolmod.operation = 'UNION'

            return {'FINISHED'}


############################## Vert Groups Forced into Ops
########################-------------------------vgroup force ops

class D2P_OT_SelectVertgroup(bpy.types.Operator):
    """Select Vertgroup"""
    bl_idname = "d2p.select_vgroup"

    bl_label = "Select VGroup"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.editmode_toggle()  # toggle editmode
        bpy.ops.object.vertex_group_select()  # select current active vgroup
        bpy.ops.object.editmode_toggle()  # toggle editmode
        bpy.ops.paint.texture_paint_toggle()  # Texpaint
        bpy.context.object.data.use_paint_mask = True
        # set face select masking on in case we forgot

        return {'FINISHED'}


class D2P_OT_DeselectVertgroup(bpy.types.Operator):
    """Deselect Vertgroup"""
    bl_idname = "d2p.deselect_vgroup"

    bl_label = "Deselect VGroup"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.editmode_toggle()  # toggle editmode
        bpy.ops.object.vertex_group_deselect()  # select current active vgroup
        bpy.ops.object.editmode_toggle()  # toggle editmode
        bpy.ops.paint.texture_paint_toggle()  # Texpaint
        bpy.context.object.data.use_paint_mask = True
        # set face select masking on in case we forgot

        return {'FINISHED'}


class D2P_OT_AssignVertgroup(bpy.types.Operator):
    """Assign Vertgroup"""
    bl_idname = "d2p.assign_vgroup"

    bl_label = "Assign VGroup"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.editmode_toggle()  # toggle editmode
        bpy.ops.object.vertex_group_assign()  # select current active vgroup
        bpy.ops.object.editmode_toggle()  # toggle editmode
        bpy.ops.paint.texture_paint_toggle()  # Texpaint
        bpy.context.object.data.use_paint_mask = True
        # set face select masking on in case we forgot

        return {'FINISHED'}


class D2P_OT_UnassignVertgroup(bpy.types.Operator):
    """Unassign Vertgroup"""
    bl_idname = "d2p.unassign_vgroup"

    bl_label = "Unassign VGroup"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.editmode_toggle()  # toggle editmode
        bpy.ops.object.vertex_group_remove_from()  # select current active vgroup
        bpy.ops.object.editmode_toggle()  # toggle editmode
        bpy.ops.paint.texture_paint_toggle()  # Texpaint
        bpy.context.object.data.use_paint_mask = True
        # set face select masking on in case we forgot

        return {'FINISHED'}


#############################Face Mask Groups FMG+
#############################  -------FMG

class D2P_OT_getFaceMaskGroups(bpy.types.Operator):
    """FMG+ _ Get Face Mask Groups from Linked Mesh Islands"""
    bl_idname = "d2p.getfacemaskgroups"
    bl_label = "Get Face Mask Groups"
    bl_options = {'REGISTER', 'UNDO'}

    ####answer from batFINGER
    @classmethod
    def poll(self, context):
        obj = context.active_object
        # fmg = obj.vertex_group

        if obj is not None:
            A = obj.type == 'MESH'
            B = context.mode == 'PAINT_TEXTURE' or 'OBJECT_MODE'
            return A and B

    def execute(self, context):
        scene = context.scene
        context = bpy.context

        def island_verts(mesh):
            #   import bmesh
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type='VERT')
            bpy.ops.mesh.select_all(action='DESELECT')

            bm = bmesh.from_edit_mesh(mesh)
            bm.verts.ensure_lookup_table()
            verts = [v.index for v in bm.verts]

            vgs = []
            while len(verts):
                bm.verts[verts[0]].select = True
                # bpy.ops.mesh.select_linked(delimit={'SEAM'})
                bpy.ops.mesh.select_linked()
                sv = [v.index for v in bm.verts if v.select]
                vgs.append(sv)
                for v in sv:
                    bm.verts[v].select = False
                    verts.remove(v)
            bm.free()  # prob not nec.
            bpy.ops.object.mode_set(mode='OBJECT')
            return vgs

            # test run

        obj = bpy.context.object
        mesh = obj.data
        vgs = island_verts(mesh)

        for vg in vgs:
            group = obj.vertex_groups.new()
            group.name = "FMG by Island"
            group.add(vg, 1.0, 'ADD')

        return {'FINISHED'}
    


######## Grease Pencil Blank Addition to Paint

class D2P_OT_NewGpencil(bpy.types.Operator):
    """Add Grease Pencil Object to Paint"""
    bl_idname = "d2p.grease_object"
    bl_label = "Must Render F12 to capture GPencil in Canvas Project"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = obj.type == 'MESH' or 'CURVE'
            B = context.mode == 'OBJECT' or 'PAINT_TEXTURE'
            return A and B

    def execute(self, context):
        scene = context.scene

        obj = context.active_object
        canvas = bpy.data.objects['canvas'].material_slots[0].material
        obj.data.materials.append(canvas)

        bpy.context.space_data.shading.type = 'MATERIAL'

        bpy.ops.paint.texture_paint_toggle()
        bpy.ops.object.gpencil_add(align='WORLD', location=(0, 0, 0),
                                   scale=(1, 1, 1), type='EMPTY')
        bpy.ops.gpencil.paintmode_toggle()
        bpy.context.object.data.layers["GP_Layer"].use_lights = False
        


        # parent
        bpy.context.object.data.layers["GP_Layer"].parent = \
            bpy.data.objects["canvas"]
            
        #make some setup shortuct
        bpy.context.scene.tool_settings.gpencil_stroke_placement_view3d = 'SURFACE'
        bpy.context.scene.tool_settings.gpencil_paint.color_mode = 'VERTEXCOLOR'

        return {'FINISHED'}


class D2P_OT_DisplayActivePaintSlot(bpy.types.Operator):
    '''Dispaly selected paint slot in new window'''
    bl_label = "Display active Slot"
    bl_idname = "d2p.display_active_slot"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(self, context):
        return context.object.active_material.texture_paint_images
    
    def execute(self, context):
        if context.object.active_material.texture_paint_images:
                # Get the Image
            mat = bpy.context.object.active_material
            image = mat.texture_paint_images[mat.paint_active_slot]
                # Call user prefs window
            bpy.ops.screen.userpref_show('INVOKE_DEFAULT')
                # Change area type
            area = context.window_manager.windows[-1].screen.areas[0]
            area.type = 'IMAGE_EDITOR'
                # Assign the Image
            context.area.spaces.active.image = image
            context.space_data.mode = 'PAINT'
        else:
            self.report({'INFO'}, "No active Slot")
        return {'FINISHED'}
    
########################################
## panel draw for Draw2Paint
class D2P_PT_ImageState(bpy.types.Panel):
    """Image State Tools"""
    bl_label = "Image State Tools"
    bl_idname = "D2P_PT_ImageState"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Draw2Paint"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        rd = context.scene.render

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Painting Starts Here")
        row = col.row(align=True)
        row.scale_x = 0.50
        row.scale_y = 1.25
        row.operator("d2p.new_image", text="New Image", icon='TEXTURE')
        row1 = row.split(align=True)
        row1.scale_x = 0.50
        row1.scale_y = 1.25
        row1.operator("d2p.create_d2p_scene", text="+Scene", icon='PREFERENCES')
        row = col.row(align=True)
        row1 = row.split(align=True)
        row1.scale_x = 0.50
        row1.scale_y = 1.25
        row1.operator("import_image.to_plane", text="Load Canvas",
                      icon='IMAGE_PLANE')
        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        row2.operator("d2p.cameraview_paint", text="Camera View Paint",
                      icon='CAMERA_STEREO')
        row3 = col.row(align=True)
        row3.scale_x=0.50
        row3.scale_y=1.25
        row3.operator("d2p.display_active_slot", icon = 'WINDOW')
        # row3.prop(view.region_3d, "lock_rotation", text="Lock Rotation")

        # d2p.lock_screen

        row = layout.row()
        row = col.row(align=True)
        row.scale_x = 0.50
        row.scale_y = 1.25
        row2 = row.split(align=True)
        row2.operator("d2p.reload_saved_state", text="Reload Image",
                      icon='IMAGE')
        row2.operator("d2p.save_current", text="Save Image",
                      icon='FILE_IMAGE')

        row = layout.row()
        row = col.row(align=True)
        row.scale_x = 0.50
        row.scale_y = 1.25
        row3 = row.split(align=True)
        row3.operator("d2p.save_increm", text="Save Increment",
                      icon='FILE_IMAGE')


################################## GPencil Future Home of Shortcuts
class D2P_PT_GreasePencil(bpy.types.Panel):
    """Panel for D2P GPencil"""
    bl_label = "Grease Pencil Shorts"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Draw2Paint"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        box = layout.box()  # MACRO
        col = box.column(align=True)
        col.label(text="GPencil for D2P Session")
        row = col.row(align=True)

        row.operator("d2p.grease_object", text="New GPencil",
                     icon='OUTLINER_DATA_GP_LAYER')


################################ 3D to 2D Experimental Workflow Items

############# Scene Extras
class D2P_PT_2D_to_3D_Experimental(bpy.types.Panel):
    """2D and 3D Workflow Experimental Operations"""
    bl_label = "Mad Scientist Painter Ops"
    bl_idname = "D2P_PT_2dto3d_experiment"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Draw2Paint"
    bl_parent_id = 'D2P_PT_ImageState'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Experimental-Use at YOUR OWN RISK")
        col.label(text="coll: canvas view-object view")
        row = col.row(align=True)

        row1 = row.split(align=True)
        row1.scale_x = 0.50
        row1.scale_y = 1.25
        row1.operator("d2p.swapcollview3d",
                      text='3D View',
                      icon='MESH_UVSPHERE')
        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        row2.operator("d2p.swapcollview2d",
                      text='2D View',
                      icon='MESH_CIRCLE')

        row = layout.row()
        row = col.row(align=True)
        row.scale_x = 0.50
        row.scale_y = 1.25
        row2 = row.split(align=True)
        row2.operator("d2p.getuvlayout",
                      text="Get UV Overlay",
                      icon='GROUP_UVS')
        row2.operator("d2p.loadbgcam",
                      text="UV to Camera",
                      icon='SCREEN_BACK')
        row = layout.row()
        row = col.row(align=True)
        row.scale_x = 0.50
        row.scale_y = 1.25
        row4 = row.split(align=True)
        row4.operator("d2p.frontof_paint",
                      text="Align to Face",
                      icon='FILE_TICK')


class D2P_PT_ImageCrop(bpy.types.Panel):
    """Image Crop Tools - PRBA"""
    bl_label = "Crop PRBA"
    bl_idname = "D2P_PT_imagecrop"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Draw2Paint"
    bl_parent_id = 'D2P_PT_ImageState'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        rd = context.scene.render

        ##################### render.use_crop_to_border
        # box = layout.box()
        # col = box.column(align=True)
        # col.label(text="Crop Tools PRBA")
        sub = layout.box()
        sub.prop(rd, "use_crop_to_border")
        if not scene.render.use_border:
            sub = layout.split(factor=0.7)
            sub.label(icon="ERROR", text="Border Render not activated:")
            sub.prop(scene.render, "use_border")

        row = sub.row()
        row.label(text="")
        row.prop(scene.render, "border_max_y", text="Max", slider=True)
        row.label(text="")
        row = sub.row(align=True)
        row.prop(scene.render, "border_min_x", text="Min", slider=True)
        row.prop(scene.render, "border_max_x", text="Max", slider=True)
        row = sub.row()
        row.label(text="")
        row.prop(scene.render, "border_min_y", text="Min", slider=True)
        row.label(text="")

        row = layout.row()
        row.label(text="Convert values to pixels:")
        row.operator("d2p.bordertopixels", text="Border -> Pixels")

        layout.label(text="Pixels position X:")
        row = layout.row(align=True)
        row.prop(scene, "x_min_pixels", text="Min")
        row.prop(scene, "x_max_pixels", text="Max")
        layout.label(text="Pixels position Y:")
        row = layout.row(align=True)
        row.prop(scene, "y_min_pixels", text="Min")
        row.prop(scene, "y_max_pixels", text="Max")

        layout.label(icon="INFO", text="Don't forget to apply pixels values")
        row = layout.row()
        row.operator("d2p.pixelstoborder", text="Pixels -> Border")


class D2P_PT_FlipRotate(bpy.types.Panel):
    """Flip and Rotate the Canvas"""
    bl_label = "Canvas Controls"
    bl_idname = "D2P_PT_FlipRotate"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Draw2Paint"
    bl_parent_id = 'D2P_PT_ImageState'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mytool = scene.my_tool

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Rotate and Flip Axis for Painting")
        row = col.row(align=True)

        row1 = row.split(align=True)
        row1.scale_x = 0.50
        row1.scale_y = 1.25
        row1.operator("d2p.canvas_horizontal", text="Flip X", icon='TRIA_RIGHT')
        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        row2.operator("d2p.canvas_vertical", text="Flip Y", icon='TRIA_UP')

        row = layout.row()
        row = col.row(align=True)
        row.scale_x = 0.50
        row.scale_y = 1.25
        row2 = row.split(align=True)
        row2.operator("d2p.rotate_ccw_90", text="90 CCW", icon='TRIA_LEFT_BAR')
        row2.operator("d2p.rotate_ccw_15", text="15 CCW", icon='TRIA_LEFT')
        row2.operator("d2p.rotate_cw_15", text="15 CW", icon='TRIA_RIGHT')
        row2.operator("d2p.rotate_cw_90", text="90 CW", icon='TRIA_RIGHT_BAR')
    
        row = layout.row()
        row.operator("d2p.canvas_resetrot", text="Reset Rotation",
                     icon='RECOVER_LAST')


class D2P_PT_GuideControls(bpy.types.Panel):
    """A custom panel in the viewport toolbar"""
    bl_label = "Guide Controls"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Draw2Paint"
    bl_parent_id = 'D2P_PT_ImageState'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        box = layout.box()  # MACRO
        col = box.column(align=True)
        col.label(text="Use for Setting Up Symmetry Guide")
        row = col.row(align=True)

        row.operator("d2p.empty_guides", text="Guide",
                     icon='ORIENTATION_CURSOR')
        row.operator("d2p.center_object", text="Recenter Guide",
                     icon='ORIENTATION_CURSOR')

        tool_settings = context.tool_settings
        ipaint = tool_settings.image_paint

        split = layout.split()

        col = split.column()
        col.alignment = 'RIGHT'
        col.label(text="Paint Symmetry")

        col = split.column()

        row = col.row(align=True)
        row.prop(context.object, "use_mesh_mirror_x", text="X", toggle=True)
        row.prop(context.object, "use_mesh_mirror_y", text="Y", toggle=True)
        row.prop(context.object, "use_mesh_mirror_z", text="Z", toggle=True)


############### align
class D2P_PT_MaskControl(bpy.types.Panel):
    """Align selected Objects in Camera View"""
    bl_label = "Mask Controls"
    bl_idname = "D2P_PT_AlignMask"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Draw2Paint"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mytool = scene.my_tool

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Align Selected Mask Objects")
        row = col.row(align=True)

        row1 = row.split(align=True)
        row1.scale_x = 0.50
        row1.scale_y = 1.25
        row1.operator("d2p.align_left", text='', icon='ANCHOR_LEFT')

        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        row2.operator("d2p.align_top", text='', icon='ANCHOR_TOP')

        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        row2.operator("d2p.align_hcenter", text='', icon='ANCHOR_CENTER')

        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        row2.operator("d2p.align_center", text='', icon='ALIGN_CENTER')

        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        row2.operator("d2p.align_bottom", text='', icon='ANCHOR_BOTTOM')

        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        row2.operator("d2p.align_right", text='', icon='ANCHOR_RIGHT')

        layout = self.layout
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Map and Apply Material to Mask")
        row = col.row(align=True)

        row1 = row.split(align=True)
        row1.scale_x = 0.50
        row1.scale_y = 1.25
        row1.operator("d2p.reproject_mask", text='(Re)Project',
                      icon='FULLSCREEN_EXIT')

        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        row1.operator("d2p.canvas_material", text='Copy Canvas',
                      icon='OUTLINER_OB_IMAGE')
        # row2.operator("d2p.solidify_difference", text='Subtract Masks',
        # icon='SELECT_SUBTRACT')
        row3 = row.split(align=True)
        row3.scale_x = 0.50
        row3.scale_y = 1.25
        row2.operator("d2p.add_holdout", text='Holdout', icon='GHOST_ENABLED')
        # row3.operator("d2p.solidify_union", text='Join Masks',
        # icon='SELECT_EXTEND')

        layout = self.layout
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Draw and Modify Masks")
        row = col.row(align=True)

        row1 = row.split(align=True)
        row1.scale_x = 0.50
        row1.scale_y = 1.25
        # row1.operator("d2p.draw_curve", text='Draw Curve',
        # icon='CURVE_BEZCURVE')
        row1.prop(mytool, "my_enum")
        row1.operator("d2p.my_enum_shapes")

        row = col.row(align=True)
        row1 = row.split(align=True)
        row1.scale_x = 0.50
        row1.scale_y = 1.25
        row1.operator("d2p.solidify_difference", text='Subtract Masks',
                      icon='SELECT_SUBTRACT')

        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        row2.operator("d2p.solidify_union", text='Join Masks',
                      icon='SELECT_EXTEND')
        # ("d2p.remove_modifiers", text='Remove Mods', icon='UNLINKED')
        row = col.row(align=True)
        row = row.split(align=True)
        row.scale_x = 0.50
        row.scale_y = 1.25
        row.operator("d2p.remove_modifiers", text='Remove Mods',
                     icon='UNLINKED')

        layout = self.layout

        row = layout.row()

        row.label(text="Face Mask Groups")
        box = layout.box()  # HORIZONTAL ALIGN
        col = box.column(align=True)
        row = col.row(align=True)
        row1 = row.split(align=True)
        # row = layout.row()
        row1.label(text="Generate FMG from Islands")
        row1.operator("d2p.getfacemaskgroups", text="FMG+", icon='SHADERFX')

        # def draw(self, context):
        layout = self.layout

        ob = context.object
        group = ob.vertex_groups.active

        rows = 2
        if group:
            rows = 4

        row = layout.row()
        row.template_list("MESH_UL_vgroups", "", ob, "vertex_groups",
                          ob.vertex_groups, "active_index", rows=rows)

        col = row.column(align=True)
        col.operator("object.vertex_group_add", icon='ADD', text="")
        col.operator("object.vertex_group_remove", icon='REMOVE',
                     text="").all = False
        col.menu("MESH_MT_vertex_group_context_menu",
                 icon='DOWNARROW_HLT', text="")
        if group:
            col.separator()
            col.operator("object.vertex_group_move",
                         icon='TRIA_UP', text="").direction = 'UP'
            col.operator("object.vertex_group_move",
                         icon='TRIA_DOWN', text="").direction = 'DOWN'

        box = layout.box()
        col = box.column(align=True)
        row = col.row(align=True)
        row1 = row.split(align=True)
        # row = layout.row()
        row1.operator("d2p.select_vgroup", text="Sel", icon='RADIOBUT_ON')
        # row1 = layout.row()
        row1.operator("d2p.deselect_vgroup", text="Desel", icon='RADIOBUT_OFF')
        # row = layout.row()
        row1.operator("d2p.assign_vgroup", text="Set", icon='ADD')
        # row = layout.row()
        row1.operator("d2p.unassign_vgroup", text="Unset", icon='REMOVE')


############# liquid sculpt
class D2P_PT_Sculpt2D(bpy.types.Panel):
    """Liquid Sculpt on a Copy of the Canvas"""
    bl_label = "Sculpt 2D Controls"
    bl_idname = "D2P_PT_Sculpt2D"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Draw2Paint"
    bl_parent_id = 'D2P_PT_ImageState'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Copy, Erase and Liquid Sculpt")
        row = col.row(align=True)

        row1 = row.split(align=True)
        row1.scale_x = 0.50
        row1.scale_y = 1.25
        row1.operator("d2p.sculpt_duplicate", text='Copy and Erase',
                      icon='NODE_TEXTURE')

        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        row2.operator("d2p.sculpt_liquid", text='Liquid Sculpt',
                      icon='MOD_FLUIDSIM')


############# Scene Extras
class D2P_PT_SceneExtras(bpy.types.Panel):
    """Creation and Use of new Scenes for Brush and Sculpt Extras"""
    bl_label = "Scene and Sculpt Extras"
    bl_idname = "D2P_PT_SceneExtras"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Draw2Paint"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Create Scenes for Brush/Sculpt Extras")
        row = col.row(align=True)

        row1 = row.split(align=True)
        row1.scale_x = 0.50
        row1.scale_y = 1.25
        row1.operator("d2p.create_brush", text='Create Brush/Mask',
                      icon='BRUSHES_ALL')

        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        row2.operator("d2p.create_reference_scene", text='Sculpt Ref',
                      icon='SCULPTMODE_HLT')

        row3 = row.split(align=True)
        row3.scale_x = 0.50
        row3.scale_y = 1.25
        row3.operator("d2p.sculpt_camera", text='Sculpt Camera',
                      icon='VIEW_CAMERA')

        row4 = row.split(align=True)
        row4.scale_x = 0.50
        row4.scale_y = 1.25
        row4.operator("d2p.slow_play", text='Slow Play',
                      icon='RENDER_ANIMATION')


classes = (

    MyProperties,
    D2P_OT_MacroCreateBrush,
    D2P_OT_CanvasHoriz,
    D2P_OT_CanvasVertical,
    D2P_OT_RotateCanvasCCW15,
    D2P_OT_RotateCanvasCW15,
    D2P_OT_RotateCanvasCCW,
    D2P_OT_RotateCanvasCW,
    D2P_OT_ImageReload,
    D2P_OT_CanvasResetrot,
    D2P_OT_SaveImage,
    D2P_OT_CameraviewPaint,
    D2P_OT_getuvlayout,
    D2P_OT_loadbgcam,
    D2P_OT_isolate_2d,
    D2P_OT_isolate_3d,
    D2P_OT_EmptyGuides,
    # D2P_OT_CamGuides,
    D2P_OT_PixelsToBorder,
    D2P_OT_BorderToPixels,
    D2P_OT_BorderCrop,
    D2P_OT_BorderUnCrop,
    D2P_OT_SculptDuplicate,
    D2P_OT_SculptLiquid,
    D2P_OT_ReprojectMask,
    D2P_OT_CanvasMaterial,
    D2P_OT_SolidifyDifference,
    D2P_OT_SolidifyUnion,
    D2P_OT_RemoveMods,
    D2P_OT_BorderCropToggle,
    D2P_OT_FrontOfPaint,
    # D2P_OT_DrawCurveloop,
    # D2P_OT_VectorCurve,
    # D2P_OT_SquareCurve,
    # D2P_OT_CircleCurve,
    D2P_OT_getFaceMaskGroups,
    D2P_OT_UnassignVertgroup,
    D2P_OT_AssignVertgroup,
    D2P_OT_DeselectVertgroup,
    D2P_OT_SelectVertgroup,
    D2P_OT_holdout_shader,
    D2P_PT_ImageState,
    D2P_PT_GreasePencil,
    D2P_PT_FlipRotate,
    D2P_PT_ImageCrop,
    D2P_PT_2D_to_3D_Experimental,
    D2P_PT_GuideControls,
    D2P_PT_MaskControl,
    D2P_PT_Sculpt2D,
    D2P_PT_SceneExtras,
    D2P_OT_SaveIncrem,
    D2P_OT_center_object,
    D2P_OT_AlignLeft,
    D2P_OT_AlignCenter,
    D2P_OT_AlignRight,
    D2P_OT_AlignTop,
    D2P_OT_AlignHcenter,
    D2P_OT_CenterAlignReset,
    D2P_OT_AlignBottom,
    # D2P_OT_ToggleLock,
    D2P_OT_CustomFps,
    D2P_OT_RefMakerScene,
    D2P_OT_SculptView,
    D2P_OT_my_enum_shapes,
    #D2P_OT_cvp_influence,
    D2P_OT_NewGpencil,
    D2P_OT_NewImage,
    D2P_OT_D2PaintScene,
    D2P_OT_DisplayActivePaintSlot

)


def register():
    # init_temp_props()
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.my_tool = bpy.props.PointerProperty(type=MyProperties)


def unregister():
    # remove_temp_props()
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    del bpy.types.Scene.my_tool


if __name__ == '__main__':
    register()

