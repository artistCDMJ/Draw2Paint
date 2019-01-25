import bpy
from bpy.types import Operator

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
