import bpy
from bpy.types import Operator

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
        row.operator("import_image.to_plane",
       text = "Image to plane",
           icon = 'IMAGE_PLANE')

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
