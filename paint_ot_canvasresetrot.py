import bpy
from bpy.types import Operator

#--------------------------------image rotation reset

class PAINT_OT_CanvasResetrot(bpy.types.Operator):
    """Canvas Rotation Reset Macro"""
    bl_idname = "image.canvas_resetrot"
    bl_label = "Canvas Reset Rotation"
    bl_options = { 'REGISTER', 'UNDO' }


    def execute(self, context):

        scene = context.scene

        #reset canvas rotation
        bpy.ops.object.rotation_clear()


        return {'FINISHED'}
