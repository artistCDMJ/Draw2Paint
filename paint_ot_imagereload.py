import bpy
from bpy.types import Operator

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
