import bpy

from bpy.types import Operator, Menu, Panel, UIList
from bpy_extras.io_utils import ImportHelper

class D2P_PT_ImageState(bpy.types.Panel):
    """Image State Tools"""
    bl_label = "Image State Tools"
    bl_idname = "D2P_PT_ImageState"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Draw2Paint"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        rd = context.scene.render

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Painting Starts Here")
        row = col.row(align=True)
        row.scale_x = 0.50
        row.scale_y = 1.25
        row.operator("d2p.new_image", text="New Image", icon='TEXTURE')
        row1 = row.split(align=True)
        row1.scale_x = 0.50
        row1.scale_y = 1.25
        row1.operator("d2p.create_d2p_scene", text="+Scene", icon='PREFERENCES')
        row = col.row(align=True)
        row1 = row.split(align=True)
        row1.scale_x = 0.50
        row1.scale_y = 1.25
        row1.operator("object.canvas_and_camera", text="Canvas and Camera",
                      icon='IMAGE_PLANE')
        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        row2.operator("object.create_camera_from_selected_image_plane", text="Camera From Canvas",
                      icon='RENDER_RESULT')
        row3 = col.row(align=True)
        row3.scale_x=0.50
        row3.scale_y=1.25
        row3.operator("d2p.display_active_slot", icon = 'WINDOW')

        row = layout.row()
        row = col.row(align=True)
        row.scale_x = 0.50
        row.scale_y = 1.25
        row2 = row.split(align=True)
        row2.operator("d2p.reload_saved_state", text="Reload",
                      icon='IMAGE')
        row2.operator("d2p.save_current", text="Save",
                      icon='FILE_IMAGE')
        row2.operator("d2p.save_increm", text="Save +1",
                      icon='FILE_IMAGE')
        row = layout.row()
        row.operator("d2p.save_dirty", text="Save All Pack All", icon='BORDERMOVE')


################################## GPencil Future Home of Shortcuts
class D2P_PT_GreasePencil(bpy.types.Panel):
    """Panel for D2P GPencil"""
    bl_label = "Grease Pencil Shorts"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Draw2Paint"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        box = layout.box()  # MACRO
        col = box.column(align=True)
        col.label(text="GPencil for D2P Session")
        row = col.row(align=True)

        row.operator("d2p.grease_object", text="New GPencil",
                     icon='OUTLINER_DATA_GP_LAYER')

############# Scene Extras
class D2P_PT_2D_to_3D_Experimental(bpy.types.Panel):
    """3D-2D Image Editor"""
    bl_label = "3d Image Editor Work"
    bl_idname = "D2P_PT_2dto3d_experiment"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Draw2Paint"
    bl_parent_id = 'D2P_PT_ImageState'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Collections:")
        col.label(text="3d: subject view 2D:canvas view")
        row = col.row(align=True)

        row1 = row.split(align=True)
        row1.scale_x = 0.50
        row1.scale_y = 1.25
        
        row1.operator("object.canvas_and_camera_from_selected_object",
                      text='Subject to Canvas',
                      icon='MESH_MONKEY')
        
        row = layout.row()
        row = col.row(align=True)
        
        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        subject_view = bpy.data.collections.get("subject_view")
        canvas_view = bpy.data.collections.get("canvas_view")
        
        if subject_view and canvas_view:
            if subject_view.hide_viewport:
                row2.operator("object.toggle_collection_visibility", 
                            text="Show Subject", 
                            icon='MESH_UVSPHERE')
            else:
                row2.operator("object.toggle_collection_visibility", 
                            text="Show Canvas", 
                            icon='MESH_CIRCLE')
        else:
            row2 = layout.row()
            row2.label(text="Collections not found")

        row = layout.row()
        row = col.row(align=True)
        row.scale_x = 0.50
        row.scale_y = 1.25
        row = row.split(align=True)
        row.operator("object.toggle_uv_image_visibility",
                      text="Toggle UV in Camera",
                      icon='IMAGE_PLANE')
        row = layout.row()
        row = col.row(align=True)
        row.scale_x = 0.50
        row.scale_y = 1.25
        
        row.operator("d2p.frontof_paint",
                      text="Align to Face",
                      icon='IMPORT')


class D2P_PT_ImageCrop(bpy.types.Panel):
    """Image Crop Tools - PRBA"""
    bl_label = "Crop PRBA"
    bl_idname = "D2P_PT_imagecrop"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Draw2Paint"
    bl_parent_id = 'D2P_PT_ImageState'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        rd = context.scene.render

        sub = layout.box()
        sub.prop(rd, "use_crop_to_border")
        if not scene.render.use_border:
            sub = layout.split(factor=0.7)
            sub.label(icon="ERROR", text="Border Render not activated:")
            sub.prop(scene.render, "use_border")

        row = sub.row()
        row.label(text="")
        row.prop(scene.render, "border_max_y", text="Max", slider=True)
        row.label(text="")
        row = sub.row(align=True)
        row.prop(scene.render, "border_min_x", text="Min", slider=True)
        row.prop(scene.render, "border_max_x", text="Max", slider=True)
        row = sub.row()
        row.label(text="")
        row.prop(scene.render, "border_min_y", text="Min", slider=True)
        row.label(text="")

        row = layout.row()
        row.label(text="Convert values to pixels:")
        row.operator("d2p.bordertopixels", text="Border -> Pixels")

        layout.label(text="Pixels position X:")
        row = layout.row(align=True)
        row.prop(scene, "x_min_pixels", text="Min")
        row.prop(scene, "x_max_pixels", text="Max")
        layout.label(text="Pixels position Y:")
        row = layout.row(align=True)
        row.prop(scene, "y_min_pixels", text="Min")
        row.prop(scene, "y_max_pixels", text="Max")

        layout.label(icon="INFO", text="Don't forget to apply pixels values")
        row = layout.row()
        row.operator("d2p.pixelstoborder", text="Pixels -> Border")

class D2P_PT_FlipRotate(bpy.types.Panel):
    """Flip and Rotate the Canvas"""
    bl_label = "Canvas Controls"
    bl_idname = "D2P_PT_FlipRotate"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Draw2Paint"
    bl_parent_id = 'D2P_PT_ImageState'
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = obj.type == 'MESH'
            B = context.mode == 'PAINT_TEXTURE'
            return A and B

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Rotate and Flip Axis for Painting")
        row = col.row(align=True)

        row1 = row.split(align=True)
        row1.scale_x = 0.50
        row1.scale_y = 1.25
        row1.operator("d2p.canvas_horizontal", text="Flip X", icon='TRIA_RIGHT')
        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        row2.operator("d2p.canvas_vertical", text="Flip Y", icon='TRIA_UP')

        layout = self.layout
        obj = context.object

        if obj and obj.type == 'MESH':
            #layout.label(text="Rotate Canvas")
            row = layout.row()
            row.prop(obj, "rotation_euler", index=2, text="Rotate Canvas")
            row.operator("d2p.canvas_resetrot", text="",
                         icon='RECOVER_LAST')

class D2P_PT_GuideControls(bpy.types.Panel):
    """A custom panel in the viewport toolbar"""
    bl_label = "Guide Controls"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Draw2Paint"
    bl_parent_id = 'D2P_PT_ImageState'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        box = layout.box()  # MACRO
        col = box.column(align=True)
        col.label(text="Use for Setting Up Symmetry Guide")
        row = col.row(align=True)

        row.operator("d2p.empty_guides", text="Guide",
                     icon='ORIENTATION_CURSOR')
        row.operator("d2p.center_object", text="Recenter Guide",
                     icon='ORIENTATION_CURSOR')

############### masking
class D2P_PT_MaskControl(bpy.types.Panel):
    """Align selected Objects in Camera View"""
    bl_label = "Mask Controls"
    bl_idname = "D2P_PT_AlignMask"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Draw2Paint"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mytool = scene.my_tool

        layout = self.layout
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Draw and Modify Masks")
        row = col.row(align=True)

        row1 = row.split(align=True)
        row1.scale_x = 0.50
        row1.scale_y = 1.25
        # row1.operator("d2p.draw_curve", text='Draw Curve',
        # icon='CURVE_BEZCURVE')
        row1.prop(mytool, "my_enum")
        row1.operator("d2p.my_enum_shapes")

        row = col.row(align=True)
        row1 = row.split(align=True)
        row1.scale_x = 0.50
        row1.scale_y = 1.25
        row1.operator("d2p.solidify_difference", text='Subtract Masks',
                      icon='SELECT_SUBTRACT')

        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        row2.operator("d2p.solidify_union", text='Join Masks',
                      icon='SELECT_EXTEND')

        row = col.row(align=True)
        row = row.split(align=True)
        row.scale_x = 0.50
        row.scale_y = 1.25
        row.operator("d2p.remove_modifiers", text='Remove Mods',
                     icon='UNLINKED')
        row = layout.row()
        row.operator("object.uv_mask_from_selected_object", text='Create UV Mask', icon='MESH_MONKEY')

        layout = self.layout
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Map and Apply Material to Mask")
        row = col.row(align=True)

        row1 = row.split(align=True)
        row1.scale_x = 0.50
        row1.scale_y = 1.25
        row1.operator("d2p.reproject_mask", text='(Re)Project',
                      icon='FULLSCREEN_EXIT')

        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        row1.operator("d2p.canvas_material", text='Copy Canvas',
                      icon='OUTLINER_OB_IMAGE')
        row3 = row.split(align=True)
        row3.scale_x = 0.50
        row3.scale_y = 1.25
        row2.operator("d2p.add_holdout", text='Holdout', icon='GHOST_ENABLED')

        layout = self.layout
        row = layout.row()
        row.label(text="Face Mask Groups")
        box = layout.box()  # HORIZONTAL ALIGN
        col = box.column(align=True)
        row = col.row(align=True)
        row1 = row.split(align=True)
        row1.label(text="Generate FMG from Islands")
        row1.operator("d2p.getfacemaskgroups", text="FMG+", icon='SHADERFX')

        # def draw(self, context):
        layout = self.layout
        ob = context.object
        group = ob.vertex_groups.active
        rows = 2
        if group:
            rows = 4

        row = layout.row()
        row.template_list("MESH_UL_vgroups", "", ob, "vertex_groups",
                          ob.vertex_groups, "active_index", rows=rows)

        col = row.column(align=True)
        col.operator("object.vertex_group_add", icon='ADD', text="")
        col.operator("object.vertex_group_remove", icon='REMOVE',
                     text="").all = False
        col.menu("MESH_MT_vertex_group_context_menu",
                 icon='DOWNARROW_HLT', text="")
        if group:
            col.separator()
            col.operator("object.vertex_group_move",
                         icon='TRIA_UP', text="").direction = 'UP'
            col.operator("object.vertex_group_move",
                         icon='TRIA_DOWN', text="").direction = 'DOWN'

        box = layout.box()
        col = box.column(align=True)
        row = col.row(align=True)
        row1 = row.split(align=True)
        row1.operator("d2p.select_vgroup", text="Sel", icon='RADIOBUT_ON')

        row1.operator("d2p.deselect_vgroup", text="Desel", icon='RADIOBUT_OFF')

        row1.operator("d2p.assign_vgroup", text="Set", icon='ADD')

        row1.operator("d2p.unassign_vgroup", text="Unset", icon='REMOVE')


############# liquid sculpt
class D2P_PT_Sculpt2D(bpy.types.Panel):
    """Liquid Sculpt on a Copy of the Canvas"""
    bl_label = "Sculpt 2D Controls"
    bl_idname = "D2P_PT_Sculpt2D"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Draw2Paint"
    bl_parent_id = 'D2P_PT_ImageState'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Copy, Erase and Liquid Sculpt")
        row = col.row(align=True)

        row1 = row.split(align=True)
        row1.scale_x = 0.50
        row1.scale_y = 1.25
        row1.operator("d2p.sculpt_duplicate", text='Copy and Erase',
                      icon='NODE_TEXTURE')

        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        row2.operator("d2p.sculpt_liquid", text='Liquid Sculpt',
                      icon='MOD_FLUIDSIM')
                      
                      
############################### IMAGE EDITOR PANEL OPTION
class D2P_PT_ImagePlanePanel(bpy.types.Panel):
    bl_label = "Image Plane and Camera"
    bl_idname = "D2P_PT_image_plane_panel"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Create'

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator("image.canvas_and_camera", text="Create Canvas and Camera")
