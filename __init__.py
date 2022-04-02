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
    "author": "CDMJ",
    "version": (3, 5, 0),
    "blender": (3, 0, 0),
    "location": "UI > Draw2Paint",
    "description": "2D Paint in 3D View, Mask Manipulation",
    "warning": "",
    "category": "Paint",
}

import bpy
import bmesh

##### main operators grouped
########### props
class MyProperties(bpy.types.PropertyGroup):
    
    my_string : bpy.props.StringProperty(name= "Enter Text")
    
    #my_float_vector : bpy.props.FloatVectorProperty(name= "Scale", soft_min= 0, soft_max= 1000, default= (1,1,1))
    
    my_enum : bpy.props.EnumProperty(
        name= "",
        description= "Choose Curve To Draw",
        items= [('OP1',"Draw Curve", ""),
                ('OP2', "Draw Vector", ""),
                ('OP3', "Draw Square", ""),
                ('OP4', "Draw Circle", "")
        ]
    )


####brush scenes and sculpt scenes

class DRAW2PAINT_OT_MacroCreateBrush(bpy.types.Operator):
    """Image Brush Scene Setup Macro"""
    bl_idname = "draw2paint.create_brush"
    bl_label = "Setup Scene for Image Brush Maker"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        scene = context.scene
        # add new scene and name it 'Brush'
        bpy.ops.scene.new(type='LINK_COPY')
        bpy.context.scene.name = "Brush"

        bpy.context.scene.render.engine = 'CYCLES'
        bpy.data.worlds[0]

        # add lamp and move up 4 units in z
        # bpy.ops.object.light_add(  # you can sort elements like this if the code
        #     # is gettings long
        #     type='POINT',
        #     radius=1,
        #     align='VIEW',
        #     location=(0, 0, 4)
        # )
        # add camera to center and move up 4 units in Z
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
class DRAW2PAINT_OT_CustomFps(bpy.types.Operator):
    """Slow Play FPS"""
    bl_idname = "draw2paint.slow_play"
    bl_label = "Slow Play FPS Toggle"
    bl_options = {'REGISTER', 'UNDO'}

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
class DRAW2PAINT_OT_RefMakerScene(bpy.types.Operator):
    """Create Reference Scene"""
    bl_description = "Create Scene for Composing Reference Slides"
    bl_idname = "draw2paint.create_reference_scene"
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


# sculpt the new duplicated canvas
class DRAW2PAINT_OT_SculptView(bpy.types.Operator):
    """Sculpt View Reference Camera"""
    bl_idname = "draw2paint.sculpt_camera"
    bl_label = "Sculpt Camera"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene

        bpy.ops.object.camera_add(view_align=False,
                                  enter_editmode=False,
                                  location=(0, -4, 0),
                                  rotation=(1.5708, 0, 0)
                                  )
        context.object.name = "Reference Cam"  # add camera to front view
        context.object.data.show_passepartout = False
        context.object.data.lens = 80

        # change to camera view
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                override = bpy.context.copy()
                override['area'] = area
                bpy.ops.view3d.viewnumpad(override, type='CAMERA')
                break
        scene.render.resolution_x = 1920
        scene.render.resolution_y = 1080

        return {'FINISHED'}


#################### shader applications
###############test material holdout generator
class DRAW2PAINT_OT_holdout_shader(bpy.types.Operator):
    bl_label = "Mask Holdout Shader"
    bl_idname = "draw2paint.add_holdout"

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
        material_output = bpy.context.active_object.active_material.node_tree.nodes.get('Material Output')

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


class DRAW2PAINT_OT_CanvasMaterial(bpy.types.Operator):
    """Adopt Canvas Material"""
    bl_idname = "draw2paint.canvas_material"
    bl_label = "Set the Material to the same as Main Canvas"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene

        obj = context.active_object
        canvas = bpy.data.objects['canvas'].material_slots[0].material
        obj.data.materials.append(canvas)

        return {'FINISHED'}

######################## sculpt to liquid
class DRAW2PAINT_OT_SculptDuplicate(bpy.types.Operator):
    """Duplicate Selected Image Plane, Single User for Eraser Paint"""
    bl_idname = "draw2paint.sculpt_duplicate"
    bl_label = "Sculpt Liquid Duplicate"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene

        bpy.ops.paint.texture_paint_toggle()
        bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked": False, "mode": 'TRANSLATION'},
                                      TRANSFORM_OT_translate={"value": (0, 0, 0), "orient_axis_ortho": 'X',
                                                              "orient_type": 'GLOBAL',
                                                              "orient_matrix": ((0, 0, 0), (0, 0, 0), (0, 0, 0)),
                                                              "orient_matrix_type": 'GLOBAL',
                                                              "constraint_axis": (False, False, False), "mirror": False,
                                                              "use_proportional_edit": False,
                                                              "proportional_edit_falloff": 'SMOOTH',
                                                              "proportional_size": 1,
                                                              "use_proportional_connected": False,
                                                              "use_proportional_projected": False, "snap": False,
                                                              "snap_target": 'CLOSEST', "snap_point": (0, 0, 0),
                                                              "snap_align": False, "snap_normal": (0, 0, 0),
                                                              "gpencil_strokes": False, "cursor_transform": False,
                                                              "texture_space": False, "remove_on_cancel": False,
                                                              "view2d_edge_pan": False, "release_confirm": False,
                                                              "use_accurate": False, "use_automerge_and_split": False})
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
            # context.scene.tool_settings.unified_paint_settings.use_pressure_size = False
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


class DRAW2PAINT_OT_SculptLiquid(bpy.types.Operator):
    """Convert to Subdivided Plane & Sculpt Liquid"""
    bl_idname = "draw2paint.sculpt_liquid"
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
class DRAW2PAINT_OT_CanvasHoriz(bpy.types.Operator):
    """Flip the Canvas Left/Right"""
    bl_idname = "draw2paint.canvas_horizontal"
    bl_label = "Canvas Horizontal"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj =  context.active_object
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
                                 orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
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

class DRAW2PAINT_OT_CanvasVertical(bpy.types.Operator):
    """Flip the Canvas Top/Bottom"""
    bl_idname = "draw2paint.canvas_vertical"
    bl_label = "Canvas Vertical"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj =  context.active_object
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
                                 orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
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

class DRAW2PAINT_OT_RotateCanvasCCW15(bpy.types.Operator):
    """Rotate Image CounterClockwise 15 degrees"""
    bl_idname = "draw2paint.rotate_ccw_15"
    bl_label = "Canvas Rotate CounterClockwise 15"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj =  context.active_object
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
                                 orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
                                 orient_matrix_type='GLOBAL',
                                 constraint_axis=(False, False, True), mirror=True,
                                 use_proportional_edit=False,
                                 proportional_edit_falloff='SMOOTH', proportional_size=1,
                                 use_proportional_connected=False,
                                 use_proportional_projected=False)

        # toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()

        return {'FINISHED'}


# --------------------------cw15

class DRAW2PAINT_OT_RotateCanvasCW15(bpy.types.Operator):
    """Rotate Image Clockwise 15 degrees"""
    bl_idname = "draw2paint.rotate_cw_15"
    bl_label = "Canvas Rotate Clockwise 15"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj =  context.active_object
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
                                 orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
                                 orient_matrix_type='GLOBAL',
                                 constraint_axis=(False, False, True), mirror=True,
                                 use_proportional_edit=False,
                                 proportional_edit_falloff='SMOOTH', proportional_size=1,
                                 use_proportional_connected=False,
                                 use_proportional_projected=False)

        # toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()

        return {'FINISHED'}


# ---------------------------ccw 90

class DRAW2PAINT_OT_RotateCanvasCCW(bpy.types.Operator):
    """Rotate Image CounterClockwise 90 degrees"""
    bl_idname = "draw2paint.rotate_ccw_90"
    bl_label = "Canvas Rotate CounterClockwise 90"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj =  context.active_object
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
                                 orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
                                 orient_matrix_type='GLOBAL',
                                 constraint_axis=(False, False, True), mirror=True,
                                 use_proportional_edit=False,
                                 proportional_edit_falloff='SMOOTH', proportional_size=1,
                                 use_proportional_connected=False,
                                 use_proportional_projected=False)

        # toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()

        return {'FINISHED'}


# -----------------------------------cw 90

class DRAW2PAINT_OT_RotateCanvasCW(bpy.types.Operator):
    """Rotate Image Clockwise 90 degrees"""
    bl_idname = "draw2paint.rotate_cw_90"
    bl_label = "Canvas Rotate Clockwise 90"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj =  context.active_object
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
                                 orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
                                 orient_matrix_type='GLOBAL',
                                 constraint_axis=(False, False, True), mirror=True,
                                 use_proportional_edit=False,
                                 proportional_edit_falloff='SMOOTH', proportional_size=1,
                                 use_proportional_connected=False,
                                 use_proportional_projected=False)

        # toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()

        return {'FINISHED'}
# --------------------------------image rotation reset

class DRAW2PAINT_OT_CanvasResetrot(bpy.types.Operator):
    """Reset Canvas Rotation"""
    bl_idname = "draw2paint.canvas_resetrot"
    bl_label = "Canvas Reset Rotation"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj =  context.active_object
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
######################### image ops to camera

# -----------------------------cameraview paint

class DRAW2PAINT_OT_CameraviewPaint(bpy.types.Operator):
    """Set up Camera to match and follow Canvas"""
    bl_idname = "draw2paint.cameraview_paint"
    bl_label = "Cameraview Paint"
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

        # toggle on/off textpaint

        obj = context.active_object

        if obj:
            mode = obj.mode
            # aslkjdaslkdjasdas
            if mode == 'TEXTURE_PAINT':
                bpy.ops.paint.texture_paint_toggle()

        # save selected plane by rename
        bpy.context.object.name = "canvas"

        # variable to get image texture dimensions - thanks to Mutant Bob http://blender.stackexchange.com/users/660/mutant-bob
        # select_mat = bpy.context.active_object.data.materials[0].texture_slots[0].texture.image.size[:]

        # select_mat = []

        for ob in bpy.context.scene.objects:
            for s in ob.material_slots:
                if s.material and s.material.use_nodes:
                    for n in s.material.node_tree.nodes:
                        if n.type == 'TEX_IMAGE':
                            select_mat = n.image.size[:]
                            # print(obj.name,'uses',n.image.name,'saved at',n.image.filepath)

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
                                    orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
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
        # try to constrain cam to canvas here
        bpy.ops.object.constraint_add(type='COPY_ROTATION')
        bpy.context.object.constraints["Copy Rotation"].target = bpy.data.objects["canvas"]

        bpy.context.object.data.show_name = True
        bpy.context.object.data.passepartout_alpha = 0.65

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

        # selection to texpaint toggle
        bpy.ops.paint.texture_paint_toggle()
        # set to Flat Shading Solid and Textured
        bpy.context.space_data.shading.type = 'MATERIAL'

        # set to standard color
        bpy.context.scene.view_settings.view_transform = 'Standard'
        bpy.context.scene.render.film_transparent = True

        return {'FINISHED'}
# -----------------------------image save

class DRAW2PAINT_OT_SaveImage(bpy.types.Operator):
    """Save Image"""
    bl_idname = "draw2paint.save_current"
    bl_label = "Save Image Current"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj =  context.active_object
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
class DRAW2PAINT_OT_SaveIncrem(bpy.types.Operator):
    """Save Incremential Images - MUST SAVE SESSION FILE FIRST"""
    bl_description = ""
    bl_idname = "draw2paint.save_increm"
    bl_label = "Save incremential Image Current"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj =  context.active_object
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

class DRAW2PAINT_OT_ImageReload(bpy.types.Operator):
    """Reload Image Last Saved State"""
    bl_idname = "draw2paint.reload_saved_state"
    bl_label = "Reload Image Save Point"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj =  context.active_object
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
class DRAW2PAINT_OT_EmptyGuides(bpy.types.Operator):
    """experimental- create new empty guide or selected guide relocates origin"""
    bl_idname = "draw2paint.empty_guides"
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
                                             radius=0.01)  # add empty for reference and movement of origin

                    # rename new empty to Symmetry Guide
                    bpy.context.object.name = "Symmetry Guide"

                    bpy.ops.transform.resize(value=(10, 10, 10))  # scale up past the normal range of image plane
                    # add constraint to follow canvas rotation
                    bpy.ops.object.constraint_add(type='COPY_ROTATION')
                    bpy.context.object.constraints["Copy Rotation"].target = bpy.data.objects["canvas"]
                    # snap cursor to empty
                    bpy.ops.view3d.snap_cursor_to_selected()

                    bpy.ops.object.select_all(action='DESELECT')
                    bpy.data.objects['Symmetry Guide'].select_set(False)
                    bpy.data.objects['canvas'].select_set(True)
                    bpy.context.view_layer.objects.active = bpy.data.objects['canvas']

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
class DRAW2PAINT_OT_center_object(bpy.types.Operator):
    """Snaps cursor and Selected Object to World Center"""
    bl_idname = "draw2paint.center_object"
    bl_label = "Center Object to World"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        # cursor to world origin
        bpy.ops.view3d.snap_cursor_to_center()
        # selected object origin to geometry
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
        bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)

        return {'FINISHED'}
################ legacy

############################################################
# -------------------LEGACY FOR ADDITION TO PANEL OPERATORS
############################################################
# -----------------------------------------------------------------FRONT OF PAINT
class DRAW2PAINT_OT_FrontOfPaint(bpy.types.Operator):
    """fast front of face view paint"""
    bl_description = ""
    bl_idname = "draw2paint.frontof_paint"
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

        context.space_data.viewport_shade = 'TEXTURED'  # texture draw
        paint.texture_paint_toggle()
        object.editmode_toggle()
        bpy.ops.view3d.viewnumpad(type='TOP', align_active=True)
        object.editmode_toggle()
        paint.texture_paint_toggle()
        contextObj.data.use_paint_mask = True
        return {'FINISHED'}


# -------------------------------------------------------------BORDER CROP TOGGLE
class DRAW2PAINT_OT_BorderCropToggle(bpy.types.Operator):
    """Set Border Crop in Render Settings"""
    bl_description = "Border Crop On/Off TOGGLE"
    bl_idname = "draw2paint.border_toggle"
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

class DRAW2PAINT_OT_ReprojectMask(bpy.types.Operator):
    """Reproject Mask"""
    bl_idname = "draw2paint.reproject_mask"
    bl_label = "Reproject Mask to UV from Camera View"
    bl_options = {'REGISTER', 'UNDO'}

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
class DRAW2PAINT_OT_AlignLeft(bpy.types.Operator):
    """Left Align"""
    bl_idname = "draw2paint.align_left"
    bl_label = "Align Objects Left"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene

        bpy.ops.object.align(align_mode='OPT_1', \
                             relative_to='OPT_4', align_axis={'X'})
        return {'FINISHED'}


class DRAW2PAINT_OT_AlignCenter(bpy.types.Operator):
    """Center Align"""
    bl_idname = "draw2paint.align_center"
    bl_label = "Align Objects Center"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene

        bpy.ops.object.align(align_mode='OPT_2', \
                             relative_to='OPT_4', align_axis={'X'})
        scene.mask_V_align = True
        return {'FINISHED'}


class DRAW2PAINT_OT_AlignRight(bpy.types.Operator):
    """Center Align"""
    bl_idname = "draw2paint.align_right"
    bl_label = "Align Objects Right"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene

        bpy.ops.object.align(align_mode='OPT_3', \
                             relative_to='OPT_4', align_axis={'X'})
        return {'FINISHED'}


class DRAW2PAINT_OT_AlignTop(bpy.types.Operator):
    """Top Align"""
    bl_idname = "draw2paint.align_top"
    bl_label = "Align Objects Top"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene

        bpy.ops.object.align(align_mode='OPT_3', \
                             relative_to='OPT_4', align_axis={'Y'})
        return {'FINISHED'}


class DRAW2PAINT_OT_AlignHcenter(bpy.types.Operator):
    """Horizontal Center Align"""
    bl_idname = "draw2paint.align_hcenter"
    bl_label = "Align Objects Horizontal Center"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene

        bpy.ops.object.align(align_mode='OPT_2', \
                             relative_to='OPT_4', align_axis={'Y'})
        scene.mask_V_align = False
        return {'FINISHED'}


class DRAW2PAINT_OT_CenterAlignReset(bpy.types.Operator):
    """Center Alignment Reset"""
    bl_idname = "draw2paint.center_align_reset"
    bl_label = "Reset center alignment"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        mva = scene.mask_V_align

        scene.mask_V_align = False if mva else True
        return {'FINISHED'}


class DRAW2PAINT_OT_AlignBottom(bpy.types.Operator):
    """Horizontal Bottom Align"""
    bl_idname = "draw2paint.align_bottom"
    bl_label = "Align Objects Horizontal Bottom"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene

        bpy.ops.object.align(align_mode='OPT_1', \
                             relative_to='OPT_4', align_axis={'Y'})
        return {'FINISHED'}


###########new curve primitives for drawing masks

class DRAW2PAINT_OT_my_enum_shapes(bpy.types.Operator):
    bl_label = "Add Mask Object"
    bl_idname = "draw2paint.my_enum_shapes"
    
    
    
    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool
        
        if mytool.my_enum == 'OP1':
            #operators guts from draw curve
            #def execute(self, context):
            scene = context.scene
            ######### add a new curve at 0.15 Z
            bpy.ops.curve.primitive_bezier_curve_add(radius=1, enter_editmode=False, align='WORLD', location=(0, 0, 0.15),
                                                     scale=(1, 1, 1))
            bpy.ops.object.editmode_toggle()
            bpy.ops.curve.delete(type='VERT')
            ########### need to add a material to the object and make it a holdout shader
            bpy.ops.material.new()

            bpy.ops.curve.cyclic_toggle()

            bpy.context.object.data.dimensions = '2D'
            bpy.context.object.data.fill_mode = 'BOTH'

            bpy.ops.wm.tool_set_by_id(name="builtin.draw")


            
            
        if mytool.my_enum == 'OP2':
            #operators guts from draw vector
            bpy.ops.curve.primitive_bezier_curve_add(enter_editmode=True, align='WORLD', location=(0, 0, 0.0125),
                                                 scale=(1, 1, 1))

            bpy.ops.curve.handle_type_set(type='VECTOR')
            bpy.context.object.data.dimensions = '2D'
            bpy.context.object.data.fill_mode = 'BOTH'

            bpy.ops.transform.resize(value=(0.1, 0.1, 0.1))
            
        
        
        
        if mytool.my_enum == 'OP3':
            #operators guts from draw square
            bpy.ops.curve.primitive_bezier_circle_add(radius=0.25, enter_editmode=False, align='WORLD', location=(0, 0, 0),
                                                      scale=(1, 1, 1))
            bpy.context.object.data.dimensions = '2D'
            bpy.context.object.data.fill_mode = 'BOTH'
            bpy.ops.object.editmode_toggle()
            bpy.ops.curve.handle_type_set(type='VECTOR')
            bpy.ops.transform.rotate(value=0.785398, orient_axis='Z')
        
        
        if mytool.my_enum == 'OP4':
            #operators guts from draw circle
            bpy.ops.curve.primitive_bezier_circle_add(radius=0.25, enter_editmode=False, align='WORLD', location=(0, 0, 0),
                                                      scale=(1, 1, 1))
            bpy.context.object.data.dimensions = '2D'
            bpy.context.object.data.fill_mode = 'BOTH'
            bpy.ops.object.editmode_toggle()            
        
        
            
        
        
        return {'FINISHED'}




'''class DRAW2PAINT_OT_SquareCurve(bpy.types.Operator):
    """Square Curve primitive for Mask"""
    bl_idname = "draw2paint.square_curve"
    bl_label = "Add Square Curve Primitive for Masking"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene

        # square curve primitive
        bpy.ops.curve.primitive_bezier_circle_add(radius=0.25, enter_editmode=False, align='WORLD', location=(0, 0, 0),
                                                  scale=(1, 1, 1))
        bpy.context.object.data.dimensions = '2D'
        bpy.context.object.data.fill_mode = 'BOTH'
        bpy.ops.object.editmode_toggle()
        bpy.ops.curve.handle_type_set(type='VECTOR')
        bpy.ops.transform.rotate(value=0.785398, orient_axis='Z')

        return {'FINISHED'}


class DRAW2PAINT_OT_CircleCurve(bpy.types.Operator):
    """Circle Curve primitive for Mask"""
    bl_idname = "draw2paint.circle_curve"
    bl_label = "Add Circle Curve Primitive for Masking"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene

        # square curve primitive
        bpy.ops.curve.primitive_bezier_circle_add(radius=0.25, enter_editmode=False, align='WORLD', location=(0, 0, 0),
                                                  scale=(1, 1, 1))
        bpy.context.object.data.dimensions = '2D'
        bpy.context.object.data.fill_mode = 'BOTH'
        bpy.ops.object.editmode_toggle()

        return {'FINISHED'}


class DRAW2PAINT_OT_VectorCurve(bpy.types.Operator):
    """Vector Curve primitive for Mask"""
    bl_idname = "draw2paint.vector_curve"
    bl_label = "Add Vector Curve Primitive for Precise Masking"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene

        bpy.ops.curve.primitive_bezier_curve_add(enter_editmode=True, align='WORLD', location=(0, 0, 0.0125),
                                                 scale=(1, 1, 1))

        bpy.ops.curve.handle_type_set(type='VECTOR')
        bpy.context.object.data.dimensions = '2D'
        bpy.context.object.data.fill_mode = 'BOTH'

        bpy.ops.transform.resize(value=(0.1, 0.1, 0.1))

        return {'FINISHED'}


class DRAW2PAINT_OT_DrawCurveloop(bpy.types.Operator):
    """Add New Curve Drawing"""
    bl_idname = "draw2paint.draw_curve"

    bl_label = "draw curve"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        ######### add a new curve at 0.15 Z
        bpy.ops.curve.primitive_bezier_curve_add(radius=1, enter_editmode=False, align='WORLD', location=(0, 0, 0.15),
                                                 scale=(1, 1, 1))
        bpy.ops.object.editmode_toggle()
        bpy.ops.curve.delete(type='VERT')
        ########### need to add a material to the object and make it a holdout shader
        bpy.ops.material.new()

        bpy.ops.curve.cyclic_toggle()

        bpy.context.object.data.dimensions = '2D'
        bpy.context.object.data.fill_mode = 'BOTH'

        bpy.ops.wm.tool_set_by_id(name="builtin.draw")

        return {'FINISHED'}'''

####################### boolean masks work
class DRAW2PAINT_OT_RemoveMods(bpy.types.Operator):
    """Remove Modifiers"""
    bl_idname = "draw2paint.remove_modifiers"
    bl_label = "Remove modifiers"
    bl_options = {'REGISTER', 'UNDO'}

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


class DRAW2PAINT_OT_SolidifyDifference(bpy.types.Operator):
    """Solidify and Difference Mask"""
    bl_idname = "draw2paint.solidify_difference"
    bl_label = "Add Solidify and Difference Bool"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        context = bpy.context

        obj = context.active_object

        mod = obj.modifiers.new("Solidify", 'SOLIDIFY')  # add a solidify modifier on active object

        mod.thickness = 0.01  # set modifier properties
        obj.location.z = 0

        for o in context.selected_objects:
            if o == obj:
                continue
            # see if there is already a modifier named "SelectedSolidify" and use it
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


class DRAW2PAINT_OT_SolidifyUnion(bpy.types.Operator):
    """Solidify and Union Mask"""
    bl_idname = "draw2paint.solidify_union"
    bl_label = "Add Solidify and Union Bool"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        context = bpy.context

        obj = context.active_object

        mod = obj.modifiers.new("Solidify", 'SOLIDIFY')  # add a solidify modifier on active object

        mod.thickness = 0.01  # set modifier properties
        obj.location.z = 0

        for o in context.selected_objects:
            if o == obj:
                continue
            # see if there is already a modifier named "SelectedSolidify" and use it
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

class DRAW2PAINT_OT_SelectVertgroup(bpy.types.Operator):
    """Select Vertgroup"""
    bl_idname = "draw2paint.select_vgroup"

    bl_label = "Select VGroup"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.editmode_toggle()  # toggle editmode
        bpy.ops.object.vertex_group_select()  # select current active vgroup
        bpy.ops.object.editmode_toggle()  # toggle editmode
        bpy.ops.paint.texture_paint_toggle()  # Texpaint
        bpy.context.object.data.use_paint_mask = True  # set face select masking on in case we forgot

        return {'FINISHED'}


class DRAW2PAINT_OT_DeselectVertgroup(bpy.types.Operator):
    """Deselect Vertgroup"""
    bl_idname = "draw2paint.deselect_vgroup"

    bl_label = "Deselect VGroup"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.editmode_toggle()  # toggle editmode
        bpy.ops.object.vertex_group_deselect()  # select current active vgroup
        bpy.ops.object.editmode_toggle()  # toggle editmode
        bpy.ops.paint.texture_paint_toggle()  # Texpaint
        bpy.context.object.data.use_paint_mask = True  # set face select masking on in case we forgot

        return {'FINISHED'}


class DRAW2PAINT_OT_AssignVertgroup(bpy.types.Operator):
    """Deselect Vertgroup"""
    bl_idname = "draw2paint.assign_vgroup"

    bl_label = "Deselect VGroup"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.editmode_toggle()  # toggle editmode
        bpy.ops.object.vertex_group_assign()  # select current active vgroup
        bpy.ops.object.editmode_toggle()  # toggle editmode
        bpy.ops.paint.texture_paint_toggle()  # Texpaint
        bpy.context.object.data.use_paint_mask = True  # set face select masking on in case we forgot

        return {'FINISHED'}


class DRAW2PAINT_OT_UnassignVertgroup(bpy.types.Operator):
    """Deselect Vertgroup"""
    bl_idname = "draw2paint.unassign_vgroup"

    bl_label = "Deselect VGroup"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.editmode_toggle()  # toggle editmode
        bpy.ops.object.vertex_group_remove_from()  # select current active vgroup
        bpy.ops.object.editmode_toggle()  # toggle editmode
        bpy.ops.paint.texture_paint_toggle()  # Texpaint
        bpy.context.object.data.use_paint_mask = True  # set face select masking on in case we forgot

        return {'FINISHED'}

#############################Face Mask Groups FMG+
#############################  -------FMG

class DRAW2PAINT_OT_getFaceMaskGroups(bpy.types.Operator):
    """Test your addon operator here first"""
    bl_idname = "draw2paint.getfacemaskgroups"
    bl_label = "Generic Operator Shell"
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


########################################
## panel draw for Draw2Paint
class DRAW2PAINT_PT_ImageState(bpy.types.Panel):
    """Image State Tools"""
    bl_label = "Image State Tools"
    bl_idname = "DRAW2PAINT_PT_ImageState"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Draw2Paint"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Painting Starts Here")
        row = col.row(align=True)

        row1 = row.split(align=True)
        row1.scale_x = 0.50
        row1.scale_y = 1.25
        row1.operator("import_image.to_plane", text="Load Canvas", icon='IMAGE_PLANE')
        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        row2.operator("draw2paint.cameraview_paint", text="Camera View Paint", icon='CAMERA_STEREO')
        # row3 = row.split(align=True)
        # row3.scale_x=0.50
        # row3.scale_y=1.25
        # row3.operator("draw2paint.lock_screen", icon = 'DECORATE_LOCKED')
        # row3.prop(view.region_3d, "lock_rotation", text="Lock Rotation")

        # draw2paint.lock_screen

        row = layout.row()
        row = col.row(align=True)
        row.scale_x = 0.50
        row.scale_y = 1.25
        row2 = row.split(align=True)
        row2.operator("draw2paint.reload_saved_state", text="Reload Image", icon='IMAGE')
        row2.operator("draw2paint.save_current", text="Save Image", icon='FILE_IMAGE')

        row = layout.row()
        row = col.row(align=True)
        row.scale_x = 0.50
        row.scale_y = 1.25
        row3 = row.split(align=True)
        row3.operator("draw2paint.save_increm", text="Save Increment", icon='FILE_IMAGE')


class DRAW2PAINT_PT_FlipRotate(bpy.types.Panel):
    """Flip and Rotate the Canvas"""
    bl_label = "Canvas Controls"
    bl_idname = "DRAW2PAINT_PT_FlipRotate"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Draw2Paint"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Rotate and Flip Axis for Painting")
        row = col.row(align=True)

        row1 = row.split(align=True)
        row1.scale_x = 0.50
        row1.scale_y = 1.25
        row1.operator("draw2paint.canvas_horizontal", text="Flip X", icon='TRIA_RIGHT')
        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        row2.operator("draw2paint.canvas_vertical", text="Flip Y", icon='TRIA_UP')

        row = layout.row()
        row = col.row(align=True)
        row.scale_x = 0.50
        row.scale_y = 1.25
        row2 = row.split(align=True)
        row2.operator("draw2paint.rotate_ccw_90", text="90 CCW", icon='TRIA_LEFT_BAR')
        row2.operator("draw2paint.rotate_ccw_15", text="15 CCW", icon='TRIA_LEFT')
        row2.operator("draw2paint.rotate_cw_15", text="15 CW", icon='TRIA_RIGHT')
        row2.operator("draw2paint.rotate_cw_90", text="90 CW", icon='TRIA_RIGHT_BAR')

        row = layout.row()
        row.operator("draw2paint.canvas_resetrot", text="Reset Rotation", icon='RECOVER_LAST')


class DRAW2PAINT_PT_GuideControls(bpy.types.Panel):
    """A custom panel in the viewport toolbar"""
    bl_label = "Guide Controls"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Draw2Paint"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        box = layout.box()  # MACRO
        col = box.column(align=True)
        col.label(text="Use for Setting Up Symmetry Guide")
        row = col.row(align=True)

        row.operator("draw2paint.empty_guides", text="Guide", icon='ORIENTATION_CURSOR')
        row.operator("draw2paint.center_object", text="Recenter Guide", icon='ORIENTATION_CURSOR')

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
        # row.prop(context.object, "use_mesh_mirror_z", text="Z", toggle=True)


############### align
class DRAW2PAINT_PT_MaskControl(bpy.types.Panel):
    """Align selected Objects in Camera View"""
    bl_label = "Mask Controls"
    bl_idname = "DRAW2PAINT_PT_AlignMask"
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
        row1.operator("draw2paint.align_left", text='', icon='ANCHOR_LEFT')

        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        row2.operator("draw2paint.align_top", text='', icon='ANCHOR_TOP')

        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        row2.operator("draw2paint.align_hcenter", text='', icon='ANCHOR_CENTER')

        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        row2.operator("draw2paint.align_center", text='', icon='ALIGN_CENTER')

        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        row2.operator("draw2paint.align_bottom", text='', icon='ANCHOR_BOTTOM')

        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        row2.operator("draw2paint.align_right", text='', icon='ANCHOR_RIGHT')

        layout = self.layout
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Map and Apply Material to Mask")
        row = col.row(align=True)

        row1 = row.split(align=True)
        row1.scale_x = 0.50
        row1.scale_y = 1.25
        row1.operator("draw2paint.reproject_mask", text='(Re)Project', icon='FULLSCREEN_EXIT')

        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        row1.operator("draw2paint.canvas_material", text='Copy Canvas', icon='OUTLINER_OB_IMAGE')
        # row2.operator("draw2paint.solidify_difference", text='Subtract Masks', icon='SELECT_SUBTRACT')
        row3 = row.split(align=True)
        row3.scale_x = 0.50
        row3.scale_y = 1.25
        row2.operator("draw2paint.add_holdout", text='Holdout', icon='GHOST_ENABLED')
        # row3.operator("draw2paint.solidify_union", text='Join Masks', icon='SELECT_EXTEND')

        layout = self.layout
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Draw and Modify Masks")
        row = col.row(align=True)

        row1 = row.split(align=True)
        row1.scale_x = 0.50
        row1.scale_y = 1.25
        #row1.operator("draw2paint.draw_curve", text='Draw Curve', icon='CURVE_BEZCURVE')
        row1.prop(mytool, "my_enum")
        row1.operator("draw2paint.my_enum_shapes")
        

        row = col.row(align=True)
        row1 = row.split(align=True)
        row1.scale_x = 0.50
        row1.scale_y = 1.25
        row1.operator("draw2paint.solidify_difference", text='Subtract Masks', icon='SELECT_SUBTRACT')

        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        row2.operator("draw2paint.solidify_union", text='Join Masks', icon='SELECT_EXTEND')
        # ("draw2paint.remove_modifiers", text='Remove Mods', icon='UNLINKED')
        row = col.row(align=True)
        row = row.split(align=True)
        row.scale_x = 0.50
        row.scale_y = 1.25
        row.operator("draw2paint.remove_modifiers", text='Remove Mods', icon='UNLINKED')

        layout = self.layout

        row = layout.row()

        row.label(text="Face Mask Groups")
        box = layout.box()  # HORIZONTAL ALIGN
        col = box.column(align=True)
        row = col.row(align=True)
        row1 = row.split(align=True)
        # row = layout.row()
        row1.label(text="Generate FMG from Islands")
        row1.operator("draw2paint.getfacemaskgroups", text="FMG+", icon='SHADERFX')

        # def draw(self, context):
        layout = self.layout

        ob = context.object
        group = ob.vertex_groups.active

        rows = 2
        if group:
            rows = 4

        row = layout.row()
        row.template_list("MESH_UL_vgroups", "", ob, "vertex_groups", ob.vertex_groups, "active_index", rows=rows)

        col = row.column(align=True)
        col.operator("object.vertex_group_add", icon='ADD', text="")
        col.operator("object.vertex_group_remove", icon='REMOVE', text="").all = False
        col.menu("MESH_MT_vertex_group_context_menu", icon='DOWNARROW_HLT', text="")
        if group:
            col.separator()
            col.operator("object.vertex_group_move", icon='TRIA_UP', text="").direction = 'UP'
            col.operator("object.vertex_group_move", icon='TRIA_DOWN', text="").direction = 'DOWN'

        box = layout.box()
        col = box.column(align=True)
        row = col.row(align=True)
        row1 = row.split(align=True)
        # row = layout.row()
        row1.operator("draw2paint.select_vgroup", text="Sel", icon='RADIOBUT_ON')
        # row1 = layout.row()
        row1.operator("draw2paint.deselect_vgroup", text="Desel", icon='RADIOBUT_OFF')
        # row = layout.row()
        row1.operator("draw2paint.assign_vgroup", text="Set", icon='ADD')
        # row = layout.row()
        row1.operator("draw2paint.unassign_vgroup", text="Unset", icon='REMOVE')


############# liquid sculpt
class DRAW2PAINT_PT_Sculpt2D(bpy.types.Panel):
    """Liquid Sculpt on a Copy of the Canvas"""
    bl_label = "Sculpt 2D Controls"
    bl_idname = "DRAW2PAINT_PT_Sculpt2D"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Draw2Paint"
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
        row1.operator("draw2paint.sculpt_duplicate", text='Copy and Erase', icon='NODE_TEXTURE')

        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        row2.operator("draw2paint.sculpt_liquid", text='Liquid Sculpt', icon='MOD_FLUIDSIM')


############# Scene Extras
class DRAW2PAINT_PT_SceneExtras(bpy.types.Panel):
    """Creation and Use of new Scenes for Brush and Sculpt Extras"""
    bl_label = "Scene and Sculpt Extras"
    bl_idname = "DRAW2PAINT_PT_SceneExtras"
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
        row1.operator("draw2paint.create_brush", text='Create Brush/Mask', icon='BRUSHES_ALL')

        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        row2.operator("draw2paint.create_reference_scene", text='Sculpt Ref', icon='SCULPTMODE_HLT')

        row3 = row.split(align=True)
        row3.scale_x = 0.50
        row3.scale_y = 1.25
        row3.operator("draw2paint.sculpt_camera", text='Sculpt Camera', icon='VIEW_CAMERA')

        row4 = row.split(align=True)
        row4.scale_x = 0.50
        row4.scale_y = 1.25
        row4.operator("draw2paint.slow_play", text='Slow Play', icon='RENDER_ANIMATION')

        col = box.column(align=True)
        col.label(text="Extras for 3D Paint")
        row = col.row(align=True)

        row1 = row.split(align=True)
        row1.scale_x = 0.50
        row1.scale_y = 1.25
        row1.operator("draw2paint.frontof_paint", text='Align to Face', icon='TRACKER')

classes = (
    
    MyProperties,
    DRAW2PAINT_OT_MacroCreateBrush,
    DRAW2PAINT_OT_CanvasHoriz,
    DRAW2PAINT_OT_CanvasVertical,
    DRAW2PAINT_OT_RotateCanvasCCW15,#
    DRAW2PAINT_OT_RotateCanvasCW15,
    DRAW2PAINT_OT_RotateCanvasCCW,
    DRAW2PAINT_OT_RotateCanvasCW,
    DRAW2PAINT_OT_ImageReload,
    DRAW2PAINT_OT_CanvasResetrot,
    DRAW2PAINT_OT_SaveImage,
    DRAW2PAINT_OT_CameraviewPaint,
    DRAW2PAINT_OT_EmptyGuides,
    # DRAW2PAINT_OT_CamGuides,
    DRAW2PAINT_OT_SculptDuplicate,
    DRAW2PAINT_OT_SculptLiquid,
    DRAW2PAINT_OT_ReprojectMask,
    DRAW2PAINT_OT_CanvasMaterial,
    DRAW2PAINT_OT_SolidifyDifference,
    DRAW2PAINT_OT_SolidifyUnion,
    DRAW2PAINT_OT_RemoveMods,
    DRAW2PAINT_OT_BorderCropToggle,
    DRAW2PAINT_OT_FrontOfPaint,
    #DRAW2PAINT_OT_DrawCurveloop,
    #DRAW2PAINT_OT_VectorCurve,
    #DRAW2PAINT_OT_SquareCurve,
    #DRAW2PAINT_OT_CircleCurve,
    DRAW2PAINT_OT_getFaceMaskGroups,
    DRAW2PAINT_OT_UnassignVertgroup,
    DRAW2PAINT_OT_AssignVertgroup,
    DRAW2PAINT_OT_DeselectVertgroup,
    DRAW2PAINT_OT_SelectVertgroup,
    DRAW2PAINT_OT_holdout_shader,
    DRAW2PAINT_PT_ImageState,
    DRAW2PAINT_PT_FlipRotate,
    DRAW2PAINT_PT_GuideControls,
    DRAW2PAINT_PT_MaskControl,
    DRAW2PAINT_PT_Sculpt2D,
    DRAW2PAINT_PT_SceneExtras,
    DRAW2PAINT_OT_SaveIncrem,
    DRAW2PAINT_OT_center_object,
    DRAW2PAINT_OT_AlignLeft,
    DRAW2PAINT_OT_AlignCenter,
    DRAW2PAINT_OT_AlignRight,
    DRAW2PAINT_OT_AlignTop,
    DRAW2PAINT_OT_AlignHcenter,
    DRAW2PAINT_OT_CenterAlignReset,
    DRAW2PAINT_OT_AlignBottom,
    # DRAW2PAINT_OT_ToggleLock,
    DRAW2PAINT_OT_CustomFps,
    DRAW2PAINT_OT_RefMakerScene,
    DRAW2PAINT_OT_SculptView,
    DRAW2PAINT_OT_my_enum_shapes

)

#register, unregister = bpy.utils.register_classes_factory(classes)


def register():
    #init_temp_props()
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.my_tool = bpy.props.PointerProperty(type=MyProperties)

def unregister():
    remove_temp_props()
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
        
    del bpy.types.Scene.my_tool

    

    # Remove module




    
if __name__ == '__main__':
    register()









