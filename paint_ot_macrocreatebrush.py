import bpy
from bpy.types import Operator

class PAINT_OT_MacroCreateBrush(bpy.types.Operator):
    """Image Brush Scene Setup Macro"""
    bl_idname = "image.create_brush"
    bl_label = "Setup Scene for Image Brush Maker"
    bl_options = { 'REGISTER', 'UNDO' }

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
        bpy.ops.object.camera_add(
          view_align=False,
          enter_editmode=False,
          location=(0, 0, 4),
          rotation=(0, 0, 0)
        )
        #rename selected camera
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
                bpy.ops.view3d.view_camera( )#view3d.view_axis
                break # this will break the loop after it is first ran

        return {'FINISHED'}
