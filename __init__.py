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
    "name": "2D Painter",
    "author": "CDMJ",
    "version": (3, 0, 0),
    "blender": (2, 80, 0),
    "location": "UI > 2D Painter",
    "description": "Art Macros.",
    "warning": "",
    "category": "Paint",
}






import bpy


'''class PAINT_OT_MirrorCanvas(bpy.types.Operator):
    """Mirror Canvas from Image as Plane Setup Macro"""
    bl_idname = "image.mirror_canvas" # must match a operator context, like
                                     # view3d, object or image and cannot have
                                     # more then one '.', if you need something
                                     # that is global use wm.create_brush
                                     # and uncomment from line 24-29
    bl_label = "Setup Mirror Canvas"
    bl_options = { 'REGISTER', 'UNDO' }



    def execute(self, context):

        scene = context.scene

        #get current context
        #bpy.context.active_object

        #make textured viewport
        bpy.context.space_data.viewport_shade = 'TEXTURED'


        #make shadeless for avoiding highlights and shadows while painting
        bpy.context.object.active_material.use_shadeless = True

        #set variable as current X dimension of image plane
        MoveX = bpy.context.object.dimensions.x

        #switch to top view
        bpy.ops.view3d.viewnumpad(type='TOP')

        #enter edit mode to move the mesh
        bpy.ops.object.editmode_toggle()

        #add mirror modifier
        bpy.ops.object.modifier_add(type='MIRROR')


        #move the mesh constrained to X at half of the mesh dimension in X
        bpy.ops.transform.translate(value=(MoveX/2, 0, 0), constraint_axis=(True, False, False), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1, release_confirm=True)

        #exit edit mode
        bpy.ops.object.editmode_toggle()





        #apply the mirror modifier to paint on both sides
        bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Mirror")

        #texture paint
        bpy.ops.paint.texture_paint_toggle()

        #toggle the tool bar
        #bpy.ops.view3d.toolshelf()

        #center to selected in view
        bpy.ops.view3d.view_selected()


        #change to camera view

        #commented out-  not needed for this script-cdmj
        #for area in bpy.context.screen.areas:
            #if area.type == 'VIEW_3D':
                #override = bpy.context.copy()
                #override['area'] = area
                #bpy.ops.view3d.viewnumpad(override, type = 'CAMERA')
                #break # this will break the loop after it is first ran

        return {'FINISHED'} # this is importent, as it tells blender that the
                            # operator is finished.'''

class PAINT_OT_MacroCreateBrush(bpy.types.Operator):
    """Image Brush Scene Setup Macro"""
    bl_idname = "image.create_brush" # must match a operator context, like
                                     # view3d, object or image and cannot have
                                     # more then one '.', if you need something
                                     # that is global use wm.create_brush
                                     # and uncomment from line 24-29
    bl_label = "Setup Scene for Image Brush Maker"
    bl_options = { 'REGISTER', 'UNDO' }

    # @classmethod
    # def poll(self, cls):
    #   '''
    #     A function that controls wether the operator can be accessed
    #   '''
    #   return context.area.type in {'VIEW3D'. 'IMAGE'}

    def execute(self, context):

        scene = context.scene


        #add new scene and name it 'Brush'

        bpy.ops.scene.new(type='NEW')
        bpy.context.scene.name = "Brush"


        #add lamp and move up 4 units in z
        bpy.ops.object.light_add( # you can sort elements like this if the code
                                 # is gettings long
          type = 'POINT',
          radius = 1,
          view_align = False,
          location = (0, 0, 4)
        )

        #add camera to center and move up 4 units in Z
        #rename selected camera

        bpy.ops.object.camera_add(
          view_align=False,
          enter_editmode=False,
          location=(0, 0, 4),
          rotation=(0, 0, 0)
        )

        bpy.context.object.name="Tex Camera"





        #change scene size to 1K

        bpy.context.scene.render.resolution_x=1024
        bpy.context.scene.render.resolution_y=1024
        bpy.context.scene.render.resolution_percentage = 100



        #save scene size as preset

        bpy.ops.render.preset_add(name = "1K Texture")

        #change to camera view


        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                override = bpy.context.copy()
                override['area'] = area
                bpy.ops.view3d.viewnumpad(override, type = 'CAMERA')
                break # this will break the loop after it is first ran

        return {'FINISHED'} # this is importent, as it tells blender that the
                            # operator is finished.


'''class PAINT_OT_CanvasShadeless(bpy.types.Operator):
    """Canvas made shadeless Macro"""
    bl_idname = "image.canvas_shadeless" # must match a operator context, like
                                     # view3d, object or image and cannot have
                                     # more then one '.', if you need something
                                     # that is global use wm.create_brush
                                     # and uncomment from line 24-29
    bl_label = "Canvas Shadeless"
    bl_options = { 'REGISTER', 'UNDO' }


    def execute(self, context):

        scene = context.scene

        #texture draw mode
        bpy.context.space_data.viewport_shade = 'TEXTURED'

        #shadeless material
        bpy.context.object.active_material.use_shadeless = True

        #change to local view and centerview
        bpy.ops.view3d.localview()

        #change to Texture Paint
        bpy.ops.paint.texture_paint_toggle()


        return {'FINISHED'} # this is importent, as it tells blender that the
                            # operator is finished.'''



#flip horizontal macro
class PAINT_OT_CanvasHoriz(bpy.types.Operator):
    """Canvas Flip Horizontal Macro"""
    bl_idname = "image.canvas_horizontal" # must match a operator context, like
                                     # view3d, object or image and cannot have
                                     # more then one '.', if you need something
                                     # that is global use wm.create_brush
                                     # and uncomment from line 24-29
    bl_label = "Canvas Horizontal"
    bl_options = { 'REGISTER', 'UNDO' }


    def execute(self, context):

        scene = context.scene

        #toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()


        #flip canvas horizontal
        bpy.ops.transform.resize(value=(-1, 1, 1), constraint_axis=(True, False, False), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1)

        #toggle object to texture
        bpy.ops.paint.texture_paint_toggle()





        return {'FINISHED'} # this is importent, as it tells blender that the
                            # operator is finished.


#--------------------------------flip vertical macro

class PAINT_OT_CanvasVertical(bpy.types.Operator):
    """Canvas Flip Vertical Macro"""
    bl_idname = "image.canvas_vertical" # must match a operator context, like
                                     # view3d, object or image and cannot have
                                     # more then one '.', if you need something
                                     # that is global use wm.create_brush
                                     # and uncomment from line 24-29
    bl_label = "Canvas Vertical"
    bl_options = { 'REGISTER', 'UNDO' }


    def execute(self, context):

        scene = context.scene

        #toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()

        #flip canvas horizontal
        bpy.ops.transform.resize(value=(1, -1, 1), constraint_axis=(False, True, False), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1)

        #toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()




        return {'FINISHED'} # this is importent, as it tells blender that the
                            # operator is finished.



#--------------------------ccw15

class PAINT_OT_RotateCanvasCCW15(bpy.types.Operator):
    """Image Rotate CounterClockwise 15 Macro"""
    bl_idname = "image.rotate_ccw_15" # must match a operator context, like
                                     # view3d, object or image and cannot have
                                     # more then one '.', if you need something
                                     # that is global use wm.create_brush
                                     # and uncomment from line 24-29
    bl_label = "Canvas Rotate CounterClockwise 15"
    bl_options = { 'REGISTER', 'UNDO' }


    def execute(self, context):

        scene = context.scene

        #toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()

        #rotate canvas 15 degrees left
        bpy.ops.transform.rotate(value=0.261799, axis=(0, 0, 1), constraint_axis=(False, False, True), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1)

        #toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()




        return {'FINISHED'} # this is important, as it tells blender that the
                            # operator is finished.

#--------------------------cw15

class PAINT_OT_RotateCanvasCW15(bpy.types.Operator):
    """Image Rotate Clockwise 15 Macro"""
    bl_idname = "image.rotate_cw_15" # must match a operator context, like
                                     # view3d, object or image and cannot have
                                     # more then one '.', if you need something
                                     # that is global use wm.create_brush
                                     # and uncomment from line 24-29
    bl_label = "Canvas Rotate Clockwise 15"
    bl_options = { 'REGISTER', 'UNDO' }


    def execute(self, context):

        scene = context.scene

        #toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()

        #rotate canvas 15 degrees left
        bpy.ops.transform.rotate(value=-0.261799, axis=(0, 0, 1), constraint_axis=(False, False, True), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1)

        #toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()




        return {'FINISHED'} # this is important, as it tells blender that the
                            # operator is finished.

#---------------------------ccw 90


class PAINT_OT_RotateCanvasCCW(bpy.types.Operator):
    """Image Rotate CounterClockwise 90 Macro"""
    bl_idname = "image.rotate_ccw_90" # must match a operator context, like
                                     # view3d, object or image and cannot have
                                     # more then one '.', if you need something
                                     # that is global use wm.create_brush
                                     # and uncomment from line 24-29
    bl_label = "Canvas Rotate CounterClockwise 90"
    bl_options = { 'REGISTER', 'UNDO' }


    def execute(self, context):

        scene = context.scene

        #toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()

        #rotate canvas 90 degrees left
        bpy.ops.transform.rotate(value=1.5708, axis=(0, 0, 1), constraint_axis=(False, False, True), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1)

        #toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()




        return {'FINISHED'} # this is important, as it tells blender that the
                            # operator is finished.



#-----------------------------------cw 90

class PAINT_OT_RotateCanvasCW(bpy.types.Operator):
    """Image Rotate Clockwise 90 Macro"""
    bl_idname = "image.rotate_cw_90" # must match a operator context, like
                                     # view3d, object or image and cannot have
                                     # more then one '.', if you need something
                                     # that is global use wm.create_brush
                                     # and uncomment from line 24-29
    bl_label = "Canvas Rotate Clockwise 90"
    bl_options = { 'REGISTER', 'UNDO' }


    def execute(self, context):

        scene = context.scene

        #toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()

        #rotate canvas 90 degrees left
        bpy.ops.transform.rotate(value=-1.5708, axis=(0, 0, 1), constraint_axis=(False, False, True), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1)

        #toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()




        return {'FINISHED'} # this is important, as it tells blender that the
                            # operator is finished.





#-----------------------------------reload image


class PAINT_OT_ImageReload(bpy.types.Operator):
    """Reload Image Last Saved State"""
    bl_idname = "image.reload_saved_state"
    bl_label = "Reload Image Save Point"
    bl_options = { 'REGISTER', 'UNDO' }


    def execute(self, context):

        scene = context.scene
        original_type = bpy.context.area.type
        bpy.context.area.type = 'IMAGE_EDITOR'

        #return image to last saved state
        bpy.ops.image.reload()

        bpy.context.area.type = original_type







        return {'FINISHED'}  #operator finished



#--------------------------------image rotation reset

class PAINT_OT_CanvasResetrot(bpy.types.Operator):
    """Canvas Rotation Reset Macro"""
    bl_idname = "image.canvas_resetrot" # must match a operator context, like
                                     # view3d, object or image and cannot have
                                     # more then one '.', if you need something
                                     # that is global use wm.create_brush
                                     # and uncomment from line 24-29
    bl_label = "Canvas Reset Rotation"
    bl_options = { 'REGISTER', 'UNDO' }


    def execute(self, context):

        scene = context.scene

        #reset canvas rotation
        bpy.ops.object.rotation_clear()




        return {'FINISHED'} # this is importent, as it tells blender that the
                            # operator is finished.


#-----------------------------cameraview paint

class PAINT_OT_CameraviewPaint(bpy.types.Operator):

    bl_idname = "image.cameraview_paint" # must match a operator context, like
                                     # view3d, object or image and cannot have
                                     # more then one '.', if you need something
                                     # that is global use wm.create_brush
                                     # and uncomment from line 24-29
    bl_label = "Cameraview Paint"
    bl_options = { 'REGISTER', 'UNDO' }



    def execute(self, context):

        scene = context.scene

        #toggle on/off textpaint

        obj = context.active_object

        if obj:
            mode = obj.mode
            # aslkjdaslkdjasdas
            if mode == 'TEXTURE_PAINT':
                bpy.ops.paint.texture_paint_toggle()

        #save selected plane by rename
        bpy.context.object.name = "canvas"


        #variable to get image texture dimensions - thanks to Mutant Bob http://blender.stackexchange.com/users/660/mutant-bob
        #select_mat = bpy.context.active_object.data.materials[0].texture_slots[0].texture.image.size[:]
        
        #select_mat = []

        for ob in bpy.context.scene.objects:
            for s in ob.material_slots:
                if s.material and s.material.use_nodes:
                    for n in s.material.node_tree.nodes:
                        if n.type == 'TEX_IMAGE':
                            select_mat = n.image.size[:]
                            #print(obj.name,'uses',n.image.name,'saved at',n.image.filepath)

        #add camera
        bpy.ops.object.camera_add(view_align=False, enter_editmode=False, location=(0, 0, 0), rotation=(0, 0, 0))
        #ratio full
        bpy.context.scene.render.resolution_percentage = 100

        #name it
        bpy.context.object.name = "Canvas View Paint"


        #switch to camera view
        bpy.ops.view3d.object_as_camera()

        #ortho view on current camera
        bpy.context.object.data.type = 'ORTHO'
        #move cam up in Z by 1 unit
        bpy.ops.transform.translate(value=(0, 0, 1), constraint_axis=(False, False, True), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1)


        #switch on composition guides for use in cameraview paint
        '''bpy.context.object.data.show_guide = {'CENTER', 'CENTER_DIAGONAL', 'THIRDS', 'GOLDEN', 'GOLDEN_TRIANGLE_A', 'GOLDEN_TRIANGLE_B', 'HARMONY_TRIANGLE_A', 'HARMONY_TRIANGLE_B'}'''


        #found on net Atom wrote this simple script

        #image_index = 0

        rnd = bpy.data.scenes[0].render
        rnd.resolution_x, rnd.resolution_y = select_mat
        #bpy.context.object.data.ortho_scale = orthoscale

        rndx = rnd.resolution_x
        rndy = rnd.resolution_y
        #orthoscale = ((rndx - rndy)/rndy)+1


        if rndx >= rndy:
            orthoscale = ((rndx - rndy)/rndy)+1

        elif rndx < rndy:
            orthoscale = 1






        bpy.context.object.data.ortho_scale = orthoscale



        bpy.context.selectable_objects

        #deselect camera
        bpy.ops.object.select_all(action='TOGGLE')
       # bpy.ops.object.select_all(action='TOGGLE')



        #select plane
        bpy.ops.object.select_all(action='DESELECT')
        ob = bpy.data.objects["canvas"]
        bpy.context.view_layer.objects.active = ob
        #bpy.context.scene.objects.active = ob


        #selection to texpaint toggle
        bpy.ops.paint.texture_paint_toggle()







        return {'FINISHED'} # this is importent, as it tells blender that the
                            # operator is finished.



#-----------------------------image save

class PAINT_OT_SaveImage(bpy.types.Operator):
    """Save Image"""
    bl_idname = "image.save_current"
    bl_label = "Save Image Current"
    bl_options = { 'REGISTER', 'UNDO' }


    def execute(self, context):

        scene = context.scene
        original_type = bpy.context.area.type
        bpy.context.area.type = 'IMAGE_EDITOR'

        #return image to last saved state
        bpy.ops.image.save()

        bpy.context.area.type = original_type







        return {'FINISHED'}  #operator finished




########################################
## panel


class PAINT_OT_ArtistPanel(bpy.types.Panel):
    """A custom panel in the viewport toolbar"""
    bl_label = "2D Painter"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Artist Macros"

    def draw(self, context):
        layout = self.layout

        row = layout.row()

        row.label(text="Image State")

        row = layout.row()
        #bpy.ops.import_image.to_plane()
        row.operator("import_image.to_plane", text = "Image to plane", icon = 'IMAGE_PLANE')

        row = layout.row()
        row.operator("image.reload_saved_state", text = "Reload Image", icon = 'IMAGE')

        row = layout.row()
        row.operator("image.save_current", text = "Save Image", icon = 'FILE_IMAGE')


        row = layout.row()

        row.label(text="Flip")

        row = layout.row()
        row.operator("image.canvas_horizontal", text = "Canvas Flip Horizontal", icon = 'TRIA_RIGHT')

        row = layout.row()
        row.operator("image.canvas_vertical", text = "Canvas Flip Vertical", icon = 'TRIA_UP')


        row = layout.row()

        row.label(text="Special Macros")



        '''row = layout.row()
        row.operator("image.canvas_shadeless", text = "Shadeless Canvas", icon = 'EMPTY_SINGLE_ARROW')'''

        row = layout.row()
        row.operator("image.cameraview_paint", text = "Camera View Paint", icon = 'OUTLINER_OB_CAMERA')

        row = layout.row()
        row.operator("image.create_brush", text = "Brush Maker Scene", icon = 'GPBRUSH_INK')

        '''row = layout.row()
        row.operator("image.mirror_canvas", text = "Mirror Canvas Paint", icon = 'EMPTY_SINGLE_ARROW')'''

        row = layout.row()

        row.label(text="Rotation")


        row = layout.row()
        row.operator("image.rotate_ccw_15", text = "Rotate 15 CCW", icon = 'TRIA_LEFT')

        row = layout.row()
        row.operator("image.rotate_cw_15", text = "Rotate 15 CW", icon = 'TRIA_RIGHT')

        row = layout.row()
        row.operator("image.rotate_ccw_90", text = "Rotate 90 CCW", icon = 'TRIA_LEFT_BAR')

        row = layout.row()
        row.operator("image.rotate_cw_90", text = "Rotate 90 CW", icon = 'TRIA_RIGHT_BAR')

        row = layout.row()
        row.operator("image.canvas_resetrot", text = "Reset Rotation", icon = 'RECOVER_LAST')

classes = (
            PAINT_OT_ArtistPanel,
            PAINT_OT_MacroCreateBrush,
            PAINT_OT_CanvasHoriz,
            PAINT_OT_CanvasVertical,
            PAINT_OT_RotateCanvasCCW15,
            PAINT_OT_RotateCanvasCW15,
            PAINT_OT_RotateCanvasCCW,
            PAINT_OT_RotateCanvasCW,
            PAINT_OT_ImageReload,
            PAINT_OT_CanvasResetrot,
            PAINT_OT_SaveImage,
            PAINT_OT_CameraviewPaint,
)

register, unregister = bpy.utils.register_classes_factory(classes)

if __name__ == '__main__':
    register()
