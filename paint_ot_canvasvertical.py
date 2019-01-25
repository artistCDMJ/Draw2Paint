import bpy
from bpy.types import Operator

#--------------------------------flip vertical macro

class PAINT_OT_CanvasVertical(bpy.types.Operator):
    """Canvas Flip Vertical Macro"""
    bl_idname = "image.canvas_vertical"
    bl_label = "Canvas Vertical"
    bl_options = { 'REGISTER', 'UNDO' }

    def execute(self, context):

        scene = context.scene

        #toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()

        #flip canvas horizontal
        bpy.ops.transform.resize(value=(1, -1, 1),
            constraint_axis=(False, True, False),
            constraint_orientation='GLOBAL',
            mirror=False, proportional='DISABLED',
            proportional_edit_falloff='SMOOTH',
            proportional_size=1)

        #toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()

        return {'FINISHED'}
