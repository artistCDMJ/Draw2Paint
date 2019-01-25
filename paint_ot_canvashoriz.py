import bpy
from bpy.types import Operator

#flip horizontal macro
class PAINT_OT_CanvasHoriz(bpy.types.Operator):
    """Canvas Flip Horizontal Macro"""
    bl_idname = "image.canvas_horizontal"
    bl_label = "Canvas Horizontal"
    bl_options = { 'REGISTER', 'UNDO' }

    def execute(self, context):

        scene = context.scene
        #toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()

        #flip canvas horizontal
        bpy.ops.transform.resize(value=(-1, 1, 1),
           constraint_axis=(True, False, False),
           constraint_orientation='GLOBAL',
           mirror=False, proportional='DISABLED',
           proportional_edit_falloff='SMOOTH',
           proportional_size=1)

        #toggle object to texture
        bpy.ops.paint.texture_paint_toggle()

        return {'FINISHED'} # this is importent, as it tells blender that the
                            # operator is finished.
