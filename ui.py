import bpy

from bpy.types import Operator, Menu, Panel, UIList
from bpy_extras.io_utils import ImportHelper
from .operators import (
    IMAGE_RESIZE_OT_getcurrentsize,
    IMAGE_RESIZE_OT_width_div2,
    IMAGE_RESIZE_OT_width_mul2,
    IMAGE_RESIZE_OT_height_div2,
    IMAGE_RESIZE_OT_height_mul2,
    IMAGE_RESIZE_OT_scale_percentage,
    IMAGE_RESIZE_OT_main,
    D2P_OT_SetColorFamilies
)
from .utils import (
    is_canvas_mesh,
    is_subject_mesh
)

class D2P_PT_ImageCreation(bpy.types.Panel):
    """Image State Tools"""
    bl_label = "Image Creation"
    bl_idname = "D2P_PT_ImageCreation"
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
        col.label(text="Image2Paint")

        row = layout.row()
        row = col.row(align=True)
        row.scale_x = 0.50
        row.scale_y = 1.25
        row = row.split(align=True)
        row.operator("d2p.new_image", text="Image2Scene", icon='TEXTURE')

        row = col.row(align=True)
        row.scale_x = 0.50
        row.scale_y = 1.25
        if scene.view_mode == 'SINGLE':
            row.operator("view3d.set_multi_texture_paint_view", text="Set Multi Layer View")
        else:
            row.operator("view3d.set_single_texture_paint_view", text="Set Single Texture View")


        row3 = col.row(align=True)
        row3.scale_x=0.50
        row3.scale_y=1.25
        row3.operator("d2p.display_active_slot", text= "Slot2Display", icon = 'WINDOW')

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
        row = col.row(align=True)
        row.scale_x = 0.50
        row.scale_y = 1.25
        row.operator("d2p.reload_all", text= "Reload ALL", icon='FILE_REFRESH')
        row.operator("d2p.save_dirty", text="Save/Pack All", icon='BORDERMOVE')


class D2P_PT_PhotoStack(bpy.types.Panel):
    """Creation and Control of PhotoStack Group Node"""
    bl_label = "PhotoStack Tools"
    bl_idname = "D2P_PT_PhotoStack"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Draw2Paint"
    bl_parent_id = 'D2P_PT_ImageCreation'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and obj.active_material

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mat = context.active_object.active_material

        box = layout.box()
        col = box.column(align=True)
        col.label(text="PhotoStack")

        row = col.row(align=True)
        row.scale_x = 0.50
        row.scale_y = 1.25
        # Number of textures input
        row.prop(scene, "num_textures")

        row = col.row(align=True)
        row.scale_x = 0.50
        row.scale_y = 1.25

        # Add material button
        row.operator("object.add_photostack", text="Generate/Extend Photostack")

        row = col.row(align=True)
        row.scale_x = 0.50
        row.scale_y = 1.25
        # applicable even without using PhotoStack, okay to draw
        if mat and mat.use_nodes:
            layout.label(text="Select Two Textures to Swap:")
            self.draw_texture_nodes(layout, mat.node_tree)

            layout.operator("image.swap_selected_textures", text="Swap Selected Textures")

    def draw_texture_nodes(self, layout, node_tree, prefix=""):
        """Recursively draw texture nodes with checkboxes, showing image names."""
        for node in node_tree.nodes:
            if node.type == 'TEX_IMAGE' and node.image:
                row = layout.row()
                # Display image name with checkbox
                image_name = node.image.name
                row.prop(node.texture_swap_props, "swap_select", text=prefix + image_name)

            elif node.type == 'GROUP' and node.node_tree:
                # Recurse into group nodes
                self.draw_texture_nodes(layout, node.node_tree, prefix=prefix + node.name + " > ")


################################## GPencil Future Home of Shortcuts
class D2P_PT_GreasePencil(bpy.types.Panel):
    """Panel for D2P GPencil for Sketching and Detailing"""
    bl_label = "GPencil2Paint"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Draw2Paint"
    bl_parent_id = 'D2P_PT_ImageCreation'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        box = layout.box()  # MACRO
        col = box.column(align=True)
        col.label(text="GPencil2Canvas")
        row = col.row(align=True)

        row.operator("d2p.grease_object", text="GPencil2Canvas",
                     icon='OUTLINER_DATA_GP_LAYER')

############# Scene Extras
class D2P_PT_3dImageEditor(bpy.types.Panel):
    """3D-2D Image Editor"""
    bl_label = "3DPaint-2-2DPaint"
    bl_idname = "D2P_PT_2dto3d_experiment"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Draw2Paint"
    #bl_parent_id = 'D2P_PT_ImageCreation'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        col = box.column(align=True)
        row = col.row(align=True)

        layout.operator("object.calculate_texel_density", icon='TEXTURE')
        if context.scene.get("texel_density_result"):
            layout.label(text=context.scene["texel_density_result"])

        row = layout.row()
        row1 = row.split(align=True)
        row1.scale_x = 0.50
        row1.scale_y = 1.25
        
        row1.operator("object.canvas_and_camera_from_selected_object",
                      text='Subject2Canvas',
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
                            text="Subject2View", 
                            icon='MESH_UVSPHERE')
            else:
                row2.operator("object.toggle_collection_visibility", 
                            text="Canvas2View", 
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
                      text="Toggle UV2Camera",
                      icon='IMAGE_PLANE')
        row = layout.row()
        row = col.row(align=True)
        row.scale_x = 0.50
        row.scale_y = 1.25
        obj = context.object
        if obj and obj.type == 'MESH':
            if '_subject' in obj.name:
                row.operator("d2p.frontof_paint",
                              text="Align2Face",
                              icon='IMPORT')


class D2P_PT_Crop2Camera(bpy.types.Panel):
    """Image Crop Tools - PRBA"""
    bl_label = "Crop2Camera"
    bl_idname = "D2P_PT_imagecrop"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Draw2Paint"
    bl_parent_id = 'D2P_PT_ImageCreation'
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
    bl_parent_id = 'D2P_PT_ImageCreation'
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        return is_canvas_mesh(context.object)
    def draw(self, context):
        layout = self.layout
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
            if '_canvas' in obj.name:
                row = layout.row()
                row.prop(obj, "rotation_euler", index=2, text="Rotate Canvas")
                row.operator("d2p.canvas_resetrot", text="",
                             icon='RECOVER_LAST')

class D2P_PT_Symmetry2Guide(bpy.types.Panel):
    """A custom panel in the viewport toolbar"""
    bl_label = "Symmetry2Guide"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Draw2Paint"
    bl_parent_id = 'D2P_PT_ImageCreation'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        box = layout.box()  # MACRO
        col = box.column(align=True)
        col.label(text="Use for Setting Up Symmetry Guide")
        row = col.row(align=True)

        row.operator("d2p.empty_guides", text="Guide2Canvas",
                     icon='ORIENTATION_CURSOR')
        row.operator("d2p.center_object", text="Recenter",
                     icon='ORIENTATION_CURSOR')

############### masking
class D2P_PT_MaskTools(bpy.types.Panel):
    """Create Mask Objects for Canvas Session"""
    bl_label = "Mask Creation"
    bl_idname = "D2P_PT_AlignMask"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Draw2Paint"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mymask = scene.my_mask

        layout = self.layout
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Curve2Mask")
        row = col.row(align=True)

        row1 = row.split(align=True)
        row1.scale_x = 0.50
        row1.scale_y = 1.25
        # row1.operator("d2p.draw_curve", text='Draw Curve',
        # icon='CURVE_BEZCURVE')
        row1.prop(mymask, "my_enum")
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

        row = col.row(align=True)
        row = row.split(align=True)
        row.scale_x = 0.50
        row.scale_y = 1.25

        row.operator("d2p.reproject_mask", text='(Re)Project', icon='FULLSCREEN_EXIT')
        row.operator("d2p.canvas_material", text='Copy Canvas', icon='OUTLINER_OB_IMAGE')
        row.operator("d2p.add_holdout", text='Holdout', icon='GHOST_ENABLED')

        layout = self.layout
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Special Mask Ops")
        row = col.row(align=True)

        row1 = row.split(align=True)
        row1.scale_x = 0.50
        row1.scale_y = 1.25
        row1.operator("object.uv_mask_from_selected_object", text='UV2Mask', icon='MESH_MONKEY')
        row1.operator("d2p.trace2curve", text='Trace2Curve', icon='OUTLINER_DATA_CURVE')

        obj = context.object
        if obj and obj.type == 'MESH':
            if '_subject' in obj.name:
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
    bl_label = "Sculpt2Canvas"
    bl_idname = "D2P_PT_Sculpt2D"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Draw2Paint"
    bl_parent_id = 'D2P_PT_ImageCreation'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return is_canvas_mesh(context.object)

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Sculpt to Modify Canvas")
        row = col.row(align=True)

        row1 = row.split(align=True)
        row1.scale_x = 0.50
        row1.scale_y = 1.25
        row1.operator("d2p.sculpt_duplicate", text='Copy2Eraser',
                      icon='NODE_TEXTURE')

        row2 = row.split(align=True)
        row2.scale_x = 0.50
        row2.scale_y = 1.25
        row2.operator("d2p.sculpt_liquid", text='Liquid Sculpt',
                      icon='MOD_FLUIDSIM')
                      
                      
############################### IMAGE EDITOR PANEL OPTION
class D2P_PT_Image2CanvasPlus(bpy.types.Panel):
    bl_label = "Image2Canvas+"
    bl_idname = "D2P_PT_image_plane_panel"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Image'

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator("image.canvas_and_camera", text="Create Canvas and Camera")

class IMAGE_RESIZE_PT_panel(bpy.types.Panel):
    bl_label = "Image Resize by todashuta"
    bl_space_type = "IMAGE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Image"

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        layout.operator(IMAGE_RESIZE_OT_getcurrentsize.bl_idname)
        split = layout.split(factor=0.6)
        split.prop(scene, "image_resize_addon_width")
        split.operator(IMAGE_RESIZE_OT_width_div2.bl_idname, text="/2")
        split.operator(IMAGE_RESIZE_OT_width_mul2.bl_idname, text="*2")
        split = layout.split(factor=0.6)
        split.prop(scene, "image_resize_addon_height")
        split.operator(IMAGE_RESIZE_OT_height_div2.bl_idname, text="/2")
        split.operator(IMAGE_RESIZE_OT_height_mul2.bl_idname, text="*2")
        layout.prop(scene, "image_resize_addon_percentage", text="Scale Percentage")
        layout.operator(IMAGE_RESIZE_OT_scale_percentage.bl_idname)
        layout.operator(IMAGE_RESIZE_OT_main.bl_idname)

def draw_node_editor_button(self, context):
    layout = self.layout
    layout.operator("node.new_texture_node", text="New Texture Node from Active Texture")

def draw_image_editor_button(self, context):
    layout = self.layout
    layout.operator("image.get_image_size", text="New Image from Active Image Size")

### Color Families Palette generation
def draw_func(self, context):
    layout = self.layout
    settings = None

    if context.mode == 'PAINT_TEXTURE':
        settings = context.tool_settings.image_paint
    elif context.mode == 'PAINT_VERTEX':
        settings = context.tool_settings.vertex_paint
    elif context.mode == 'PAINT_WEIGHT':
        settings = context.tool_settings.weight_paint

    if settings and settings.palette:
        layout.operator(D2P_OT_SetColorFamilies.bl_idname)

#### nodes selected to compositor and back
class D2P_PT_node_editor_panel(bpy.types.Panel):
    bl_label = "D2P Node Editor Panel"
    bl_idname = "D2P_PT_node_editor_panel"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        # swap editor button

        if context.space_data.tree_type != 'CompositorNodeTree':

            # shader editor buttons
            layout.operator("d2p.editor_swap", text="2Compositor", icon='AREA_SWAP')

            layout.label(text="Image Node Ops")
            layout.operator("viewer.shader2viewer", text="Image2Compositor", icon='OUTLINER_OB_IMAGE')
            layout.operator('node.copy_photostack_to_compositor', text="PhotoStack2Compositor", icon ='RENDERLAYERS')
        else:
            # compositor editor buttons
            layout.operator("d2p.editor_swap", text="2ShaderEditor", icon='AREA_SWAP')

            layout.label(text="Composite Node Ops")
            layout.operator("viewer.viewer2image", text="Compositor2Image", icon='RENDER_STILL')




# Define the Operator that is triggered by the button

#### easy to see UV access
class UV_WireColor(bpy.types.Panel):
    """Creates a Panel in the UV Editor to change the UV wire color"""
    bl_label = "UV Wire Color"
    bl_idname = "UV_PT_wire_color"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'View'

    def draw(self, context):
        layout = self.layout
        prefs = bpy.context.preferences
        theme = prefs.themes[0].image_editor

        if context.area.ui_type == 'UV':
            layout.prop(theme, "wire_edit", text="UV Wire in Edit")
        else:
            layout.prop(theme, "uv_shadow", text="UV Wire in Paint")


class VIEW3D_WireColor(bpy.types.Panel):
    """Creates a Panel in the 3D View to change the Edit Mode wire color"""
    bl_label = "3D View Wire Color"
    bl_idname = "VIEW3D_PT_wire_color"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'View'

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def draw(self, context):
        layout = self.layout
        prefs = bpy.context.preferences
        theme = prefs.themes[0].view_3d

        layout.prop(theme, "wire_edit", text="Wire in Edit")
        layout.prop(theme, "edge_width", text="Edge Width")


