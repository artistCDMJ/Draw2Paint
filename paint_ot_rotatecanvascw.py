import bpy
from bpy.types import Operator

#-----------------------------------cw 90

class PAINT_OT_RotateCanvasCW(bpy.types.Operator):
    """Image Rotate Clockwise 90 Macro"""
    bl_idname = "image.rotate_cw_90"
    bl_label = "Canvas Rotate Clockwise 90"
    bl_options = { 'REGISTER', 'UNDO' }


    def execute(self, context):

        scene = context.scene

        #toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()

        #rotate canvas 90 degrees left
        bpy.ops.transform.rotate(value=-1.5708, axis=(0, 0, 1),
            constraint_axis=(False, False, True),
            constraint_orientation='GLOBAL',
            mirror=False,
            proportional='DISABLED',
            proportional_edit_falloff='SMOOTH',
            proportional_size=1)

        #toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()

        return {'FINISHED'}
