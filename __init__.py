################################ 3D to 2D Experimental Workflow Items

############# Scene Extras
class DRAW2PAINT_PT_2D_to_3D_Experimental(bpy.types.Panel):
    """2D and 3D Workflow Experimental Operations"""
    bl_label = "MaD ScIeNtIsT Painter Ops"
    bl_idname = "DRAW2PAINT_PT_2dto3d_experiment"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Draw2Paint"
    bl_parent_id = 'DRAW2PAINT_PT_ImageState'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Experimental-Use at YOUR OWN RISK")
        col.label(text="coll: canvas view-object view")
        row = col.row(align=True)

        row1 = row.split(align=True)
        row1.scale_x = 0.50
        row1.scale_y = 1.25
        row1.operator("draw2paint.swapcollview3d", 
                    text='3D View', 
                    icon='MESH_UVSPHERE')
        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        row2.operator("draw2paint.swapcollview2d", 
                    text='2D View', 
                    icon='MESH_CIRCLE')

        row = layout.row()
        row = col.row(align=True)
        row.scale_x = 0.50
        row.scale_y = 1.25
        row2 = row.split(align=True)
        row2.operator("draw2paint.getuvlayout", 
                    text="Get UV Overlay", 
                    icon='GROUP_UVS')
        row2.operator("draw2paint.loadbgcam",
                    text="UV to Camera", 
                    icon='SCREEN_BACK')
        row=layout.row()
        row = col.row(align=True)
        row.scale_x = 0.50
        row.scale_y = 1.25
        row4 = row.split(align=True)
        row4.operator("draw2paint.frontof_paint",
                    text="Align to Face", 
                    icon='FILE_TICK')

