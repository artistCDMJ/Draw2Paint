import os
import bpy
import colorsys

import bmesh

import bgl, blf, bpy, mathutils, time, copy, math, re

from .utils import next_power_of_2, previous_power_of_2

from bpy.props import *
import bpy
from bpy.types import Operator
from .utils import (find_brush, create_image_plane_from_image, create_matching_camera,\
                    switch_to_camera_view, get_image_from_selected_object, \
                    move_object_to_collection, export_uv_layout, \
                    set_camera_background_image, get_active_image_from_image_editor, \
                    save_incremental_copy,paint_view_color_management_settings, \
                    multi_texture_paint_view,single_texture_paint_view, get_active_image_size, \
                    get_active_texture_node_image_size,create_new_texture_node_with_size, \
                    rgb_to_hex, complementary_color, split_complementary_colors,\
                    triadic_colors, tetradic_colors, analogous_colors, create_palette, \
                    new_convert_curve_object,convert_gpencil_to_curve,move_trace_objects_to_collection, \
                    convert_image_plane_to_curve, is_canvas_mesh, create_compositor_node_tree,\
                    render_and_extract_image,calculate_texel_density, create_scene_based_on_active_image,\
                    select_object_by_suffix)

from bpy.types import Operator, Menu, Panel, UIList
from bpy_extras.io_utils import ImportHelper

#new Trace2Curve makes the leap from image plane to gpencil to curve
class D2P_OT_Trace2Curve(bpy.types.Operator):
    """Convert B&W Image Plane to Curve"""
    bl_idname = "d2p.trace2curve"
    bl_label = "Convert Image Plane to Curve"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_objects = context.selected_objects
        if selected_objects:
            convert_image_plane_to_curve(selected_objects[0])
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "No object selected.")
            return {'CANCELLED'}

# new image texture node sized to same as active
class D2P_OT_NewTextureNode(bpy.types.Operator):
    bl_idname = "node.new_texture_node"
    bl_label = "New Texture Node from Active Texture"

    def execute(self, context):
        width, height = get_active_texture_node_image_size()
        if width and height:
            create_new_texture_node_with_size(width, height)
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "No active texture node with an image found")
            return {'CANCELLED'}


# new image dialog autofilled with size from active image in image editor
class D2P_OT_GetImageSizeOperator(bpy.types.Operator):
    bl_idname = "image.get_image_size"
    bl_label = "New Image from Active Image Size"

    width: bpy.props.IntProperty()
    height: bpy.props.IntProperty()

    def invoke(self, context, event):
        width, height = get_active_image_size()
        if width and height:
            self.width = width
            self.height = height
            context.window_manager.invoke_props_dialog(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "No active image found")
            return {'CANCELLED'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "width")
        layout.prop(self, "height")

    def execute(self, context):
        bpy.ops.image.new(name="New Image", width=self.width, height=self.height)
        return {'FINISHED'}

# Operator to set single texture paint view
class D2P_OT_SetSingleTexturePaintView(bpy.types.Operator):
    bl_idname = "view3d.set_single_texture_paint_view"
    bl_label = "Set Single Texture Paint View"

    def execute(self, context):
        single_texture_paint_view()
        context.scene.view_mode = 'SINGLE'
        return {'FINISHED'}


# Operator to set multi texture paint view
class D2P_OT_SetMultiTexturePaintView(bpy.types.Operator):
    bl_idname = "view3d.set_multi_texture_paint_view"
    bl_label = "Set Multi Texture Paint View"

    def execute(self, context):
        multi_texture_paint_view()
        context.scene.view_mode = 'MULTI'
        return {'FINISHED'}


class D2P_OT_UV2Mask(bpy.types.Operator):
    """New Mask Object from UV Map of Subject"""
    bl_description = "New Mask Object from UV Map of Subject"
    bl_idname = "object.uv_mask_from_selected_object"
    bl_label = "Generate UV Mask Object from Selected Object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        selected_objects = context.selected_objects
        if not selected_objects:
            return False

        selected_object = selected_objects[0]

        # Check if 'subject_view' collection exists
        if 'subject_view' not in bpy.data.collections:
            return False

        # Check if the object with the same name and suffix '_UVObj' already exists in 'mask_objects' collection
        object_name_with_suffix = selected_object.name + '_UVObj'
        if 'mask_objects' in bpy.data.collections:
            mask_objects_collection = bpy.data.collections['mask_objects']
            if object_name_with_suffix in mask_objects_collection.objects:
                return False

        return True

    def execute(self, context):
        selected_objects = context.selected_objects
        if not selected_objects:
            self.report({'WARNING'}, "No selected objects found.")
            return {'CANCELLED'}

        selected_object = selected_objects[0]

        if not selected_object.data.uv_layers:
            self.report({'WARNING'}, "Please Create UV Layer")
            return {'CANCELLED'}

        C = bpy.context
        ob = selected_object  # Use the selected object
        size = 4.095675

        def create_mesh_from_data(name, verts, faces):
            # Create mesh and object
            me = bpy.data.meshes.new(name + 'Mesh')
            new_ob = bpy.data.objects.new(name, me)
            new_ob.show_name = True

            # Link object to scene and make active
            C.view_layer.active_layer_collection.collection.objects.link(new_ob)
            C.view_layer.objects.active = new_ob
            new_ob.select_set(True)

            # Create mesh from given verts, faces
            me.from_pydata(verts, [], faces)
            # Update mesh with new data
            me.update()
            return new_ob

        out_verts = []
        out_faces = []
        for face in ob.data.polygons:
            oface = []
            for vert, loop in zip(face.vertices, face.loop_indices):
                uv = ob.data.uv_layers.active.data[loop].uv
                out_verts.append((uv.x * size, uv.y * size, 0))
                oface.append(loop)
            out_faces.append(oface)

        new_obj = create_mesh_from_data(ob.name + '_UVObj', out_verts, out_faces)

        # Show wire on the new object
        new_obj.show_wire = True

        # Enter Edit Mode to remove duplicate vertices
        with bpy.context.temp_override(active_object=new_obj, selected_objects=[new_obj]):
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.remove_doubles()
            bpy.ops.object.mode_set(mode='OBJECT')

        # Deselect all objects
        bpy.ops.object.select_all(action='DESELECT')

        # Find the canvas object by suffix
        canvas_obj = None
        for obj in bpy.data.objects:
            if obj.name.endswith('_canvas'):
                canvas_obj = obj
                break

        if canvas_obj:
            # Select the canvas object
            canvas_obj.select_set(True)
            context.view_layer.objects.active = canvas_obj

            # Update the context to ensure the active object is set
            bpy.context.view_layer.update()

            # Use temp_override for mode switching
            with bpy.context.temp_override(active_object=canvas_obj, selected_objects=[canvas_obj]):
                # Enter Edit Mode for the canvas object
                bpy.ops.object.mode_set(mode='EDIT')

                # Get the active mesh
                bm = bmesh.from_edit_mesh(canvas_obj.data)

                # Ensure the lookup table is up to date
                bm.verts.ensure_lookup_table()

                # Identify the lower left vertex (default is Vertex 0)
                lower_left_vertex = bm.verts[0]

                # Switch to Object Mode temporarily
                bpy.ops.object.mode_set(mode='OBJECT')

                # Access the mesh vertices in Object Mode
                verts = canvas_obj.data.vertices

                # Get the coordinates of the lower left vertex (Vertex 0)
                lower_left_vertex_co = verts[0].co

                # Snap the cursor to this vertex
                bpy.context.scene.cursor.location = lower_left_vertex_co

                print(f"Cursor snapped to lower left vertex: {lower_left_vertex_co}")

            # Select the new UV mask object
            new_obj.select_set(True)
            context.view_layer.objects.active = new_obj

            # Move the new object to the cursor's location
            new_obj.location = bpy.context.scene.cursor.location
            new_obj.location.z += 0.25  # Move up Z by 0.25
            new_obj.parent = canvas_obj  # Make it a child of canvas object

            # Adopt the material of the selected object
            if selected_object.data.materials:
                new_obj.data.materials.append(selected_object.data.materials[0])  # Copy material from selected object

            # Ensure 'canvas_view' collection exists
            if 'canvas_view' not in bpy.data.collections:
                canvas_view_collection = bpy.data.collections.new('canvas_view')
                bpy.context.scene.collection.children.link(canvas_view_collection)
            else:
                canvas_view_collection = bpy.data.collections['canvas_view']

            # Ensure 'mask_objects' collection exists within 'canvas_view'
            if 'mask_objects' not in bpy.data.collections:
                mask_objects_collection = bpy.data.collections.new('mask_objects')
                canvas_view_collection.children.link(mask_objects_collection)
            else:
                mask_objects_collection = bpy.data.collections['mask_objects']

            # Add new object to 'mask_objects' collection
            if new_obj.name not in mask_objects_collection.objects:
                mask_objects_collection.objects.link(new_obj)
                bpy.context.view_layer.active_layer_collection.collection.objects.unlink(new_obj)

        else:
            self.report({'WARNING'}, "Canvas object with suffix '_canvas' not found.")
            return {'CANCELLED'}

        return {'FINISHED'}


class D2P_OT_Subject2Canvas(bpy.types.Operator):
    """New Canvas and Camera from Selected Subject"""
    bl_description = "New Canvas and Camera from Selected Subject"
    bl_idname = "object.canvas_and_camera_from_selected_object"
    bl_label = "Generate Image Plane and Camera from Selected Object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return 'subject_view' not in bpy.data.collections or 'canvas_view' not in bpy.data.collections

    def execute(self, context):
        selected_objects = context.selected_objects
        if not selected_objects:
            self.report({'WARNING'}, "No selected objects found.")
            return {'CANCELLED'}

        selected_object = selected_objects[0]

        if not selected_object.data.uv_layers:
            self.report({'WARNING'}, "Please Create UV Layer")
            return {'CANCELLED'}

        # Rename object with suffix _subject
        selected_object.name += '_subject'

        # Create new scene and ensure the object is linked
        create_scene_based_on_active_image(selected_object)

        # Ensure the object is active and selected in the new scene
        selected_object = bpy.context.scene.objects.get(selected_object.name)
        if selected_object is None:
            self.report({'ERROR'}, "Selected object could not be found in the new scene.")
            return {'CANCELLED'}


        # Ensure the object is active and selected
        bpy.context.view_layer.objects.active = selected_object
        selected_object.select_set(True)

        # Move object to 'subject_view' collection
        move_object_to_collection(selected_object, 'subject_view')

        # Export UV layout
        uv_filepath = os.path.join("C:/tmp", selected_object.name + ".png")
        export_uv_layout(selected_object, uv_filepath)

        # Try to link to original scene here
        bpy.ops.object.make_links_scene(scene='Scene')

        # Continue the rest of the process
        active_image = get_image_from_selected_object(selected_object)
        if not active_image:
            self.report({'WARNING'}, "Selected object has no image texture.")
            return {'CANCELLED'}

        image_plane_obj, width, height = create_image_plane_from_image(active_image)
        if not image_plane_obj:
            self.report({'WARNING'}, "Failed to create image plane.")
            return {'CANCELLED'}

        camera_obj = create_matching_camera(image_plane_obj, width, height)

        # Move camera and image plane to 'canvas_view' collection
        move_object_to_collection(image_plane_obj, 'canvas_view')
        move_object_to_collection(camera_obj, 'canvas_view')

        try:
            set_camera_background_image(camera_obj, uv_filepath)
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        switch_to_camera_view(camera_obj)

        # Switch to canvas_view collection on init
        bpy.ops.object.toggle_collection_visibility()

        return {'FINISHED'}


class D2P_OT_Image2CanvasPlus(bpy.types.Operator):
    """Create Canvas and Camera from Active Image In Image Editor"""
    bl_description = "Create Canvas and Camera from Active Image In Image Editor"
    bl_idname = "image.canvas_and_camera"
    bl_label = "Generate Image Plane and Matching Camera from Image Editor"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        active_image = None
        for area in bpy.context.screen.areas:
            if area.type == 'IMAGE_EDITOR':
                active_image = area.spaces.active.image
                break

        if not active_image:
            self.report({'WARNING'}, "No active image found.")
            return {'CANCELLED'}

        # Create new scene based on the image editor's active image (no object needed)
        create_scene_based_on_active_image()  # No selected object is passed here

        # Switch to 3D view
        bpy.context.area.ui_type = 'VIEW_3D'

        # Create image plane and matching camera
        image_plane_obj, width, height = create_image_plane_from_image(active_image)
        if not image_plane_obj:
            self.report({'WARNING'}, "Failed to create image plane.")
            return {'CANCELLED'}

        camera_obj = create_matching_camera(image_plane_obj, width, height)
        bpy.context.view_layer.objects.active = camera_obj
        camera_obj.data.show_name = True

        # Ensure the correct context is active before applying view settings
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                with bpy.context.temp_override(area=area):
                    area.spaces.active.shading.type = 'SOLID'
                    area.spaces.active.shading.light = 'FLAT'
                    area.spaces.active.shading.color_type = 'TEXTURE'

        # Move camera and image plane to 'canvas_view' collection
        move_object_to_collection(image_plane_obj, active_image.name + '_canvas_view')
        move_object_to_collection(camera_obj, active_image.name + '_canvas_view')

        # Switch to camera view (inside the 3D View context)
        switch_to_camera_view(camera_obj)

        # Switch back to Image Editor
        bpy.context.area.ui_type = 'IMAGE_EDITOR'

        return {'FINISHED'}


class D2P_OT_ToggleUV2Camera(bpy.types.Operator):
    """Toggle UV Image Visibility in Camera"""
    bl_description = "Toggle UV Image Visibility in Camera"
    bl_idname = "object.toggle_uv_image_visibility"
    bl_label = "Toggle UV Image Visibility in Camera"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll (clas, context):
        return is_canvas_mesh(context.object)
    def execute(self, context):
        cam = context.scene.camera
        if cam and cam.data.background_images:
            # Assume the first background image is the one we want to toggle
            bg = cam.data.background_images[0]
            bg.show_background_image = not bg.show_background_image
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "No background image found on the active camera.")
            return {'CANCELLED'}

class D2P_OT_ToggleCollectionView(bpy.types.Operator):
    """Toggle 3D or 2D Collection"""
    bl_description = "Toggle 3D or 2D Collection"
    bl_idname = "object.toggle_collection_visibility"
    bl_label = "Toggle Collection Visibility"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        subject_view = bpy.data.collections.get("subject_view")
        canvas_view = bpy.data.collections.get("canvas_view")

        if subject_view and canvas_view:
            if subject_view.hide_viewport:
                subject_view.hide_viewport = False
                subject_view.hide_render = False
                canvas_view.hide_viewport = True
                canvas_view.hide_render = True
                # Switch to front view
                bpy.ops.view3d.view_axis(type='FRONT', align_active=True)
                bpy.context.space_data.shading.type = 'MATERIAL'
                select_object_by_suffix('_subject')

            else:
                subject_view.hide_viewport = True
                subject_view.hide_render = True
                canvas_view.hide_viewport = False
                canvas_view.hide_render = False
                # Switch to camera view
                switch_to_camera_view(context.scene.camera)
                bpy.context.space_data.shading.type = 'SOLID'
                bpy.context.space_data.shading.light = 'FLAT'
                select_object_by_suffix('_canvas')

            
            # Update the view layer to reflect visibility changes
            bpy.context.view_layer.update()
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "One or both collections not found.")
            return {'CANCELLED'}


class D2P_OT_holdout_shader(bpy.types.Operator):
    bl_label = "Mask Holdout Shader"
    bl_idname = "d2p.add_holdout"

    @classmethod
    def poll(self, context):
        obj = context.active_object
        A = obj is not None
        if A:
            B = obj.type == 'CURVE' or 'MESH'
            return B

    def execute(self, context):
        mask = bpy.data.materials.new(name="Holdout Mask")
        mask.use_nodes = True

        bpy.context.object.active_material = mask

        mask = bpy.data.materials.new(name="Holdout Mask")

        mask.use_nodes = True

        bpy.context.object.active_material = mask

        ###output node new

        material_output = bpy.context.active_object.active_material.node_tree.\
                                                nodes.get('Material Output')

        # Principled Main Shader in Tree
        principled_node = mask.node_tree.nodes.get('Principled BSDF')
        mask.node_tree.nodes.remove(principled_node)

        ###Tex Coordinate Node
        hold = mask.node_tree.nodes.new('ShaderNodeHoldout')
        hold.location = (-100, 0)
        hold.label = ("Holdout Mask")


        #####LINKING
        link = mask.node_tree.links.new

        link(hold.outputs[0], material_output.inputs[0])

        return {'FINISHED'}

class D2P_OT_CanvasMaterial(bpy.types.Operator):
    """Adopt Canvas Material"""
    bl_idname = "d2p.canvas_material"
    bl_label = "Set the Material to the same as Main Canvas"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type in {'MESH', 'CURVE'} and context.mode in {'OBJECT', 'PAINT_TEXTURE'}

    def execute(self, context):
        scene = context.scene
        suffix = '_canvas'
        match_object_name = None

        # Find the object with the specified suffix
        for obj in scene.objects:
            if obj.name.endswith(suffix):
                match_object_name = obj.name
                break

        if match_object_name:
            print(f"Object with suffix '{suffix}' found: {match_object_name}")
            # Get the material from the matching object
            canvas_object = bpy.data.objects.get(match_object_name)
            if canvas_object and canvas_object.material_slots:
                canvas_material = canvas_object.material_slots[0].material

                # Assign the material to the active object if not already present
                active_obj = context.active_object
                material_names = [mat.name for mat in active_obj.data.materials]
                if canvas_material.name not in material_names:
                    active_obj.data.materials.append(canvas_material)
                    print(f"Material '{canvas_material.name}' added to the active object.")
                else:
                    print(f"Material '{canvas_material.name}' already assigned to the object.")
            else:
                self.report({'WARNING'}, f"Object '{match_object_name}' has no materials.")
        else:
            self.report({'WARNING'}, f"No object with suffix '{suffix}' found in the scene.")
        
        return {'FINISHED'}
    
class D2P_OT_Copy2Eraser(bpy.types.Operator):
    """Duplicate Selected Image Plane, Single User for Eraser Paint"""
    bl_idname = "d2p.sculpt_duplicate"
    bl_label = "Sculpt Liquid Duplicate"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return is_canvas_mesh(context.object)

    def execute(self, context):
        scene = context.scene

        bpy.ops.paint.texture_paint_toggle()
        bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked": False, "mode": 'TRANSLATION'},
                                      TRANSFORM_OT_translate={"value": (0, 0, 0),
                                                              "orient_type": 'GLOBAL',
                                                              "orient_matrix": ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
                                                              "orient_matrix_type": 'GLOBAL',
                                                              "constraint_axis": (False, False, False),
                                                              "mirror": False,
                                                              "use_proportional_edit": False,
                                                              "proportional_edit_falloff": 'SMOOTH',
                                                              "proportional_size": 1,
                                                              "use_proportional_connected": False,
                                                              "use_proportional_projected": False,
                                                              "snap": False,
                                                              "snap_target": 'CLOSEST',
                                                              "snap_point": (0, 0, 0),
                                                              "snap_align": False,
                                                              "snap_normal": (0, 0, 0),
                                                              "gpencil_strokes": False,
                                                              "cursor_transform": False,
                                                              "texture_space": False,
                                                              "remove_on_cancel": False,
                                                              "view2d_edge_pan": False,
                                                              "release_confirm": False,
                                                              "use_accurate": False,
                                                              "use_automerge_and_split": False})
        bpy.ops.transform.translate(value=(0, 0, 0.1))
        bpy.ops.view3d.localview()
        bpy.ops.paint.texture_paint_toggle()

        # make ERASER brush or use existing
        # might need fixing for 4.3 version
    
        try:
            context.tool_settings.image_paint.brush = bpy.data.brushes["Eraser"]
        except KeyError:
            context.tool_settings.image_paint.brush = bpy.data.brushes["TexDraw"]
            bpy.ops.brush.add()
            bpy.data.brushes["TexDraw.001"].name = "Eraser"
            bpy.data.brushes["Eraser"].use_pressure_strength = False
            bpy.data.brushes["Eraser"].blend = 'ERASE_ALPHA'

        # make individual of material AND of image reference inside
        sel = bpy.context.active_object
        mat = sel.material_slots[0].material
        sel.material_slots[0].material = mat.copy()

        material = sel.material_slots[0].material
        node = material.node_tree.nodes['Image Texture']
        new_image = node.image.copy()
        node.image = new_image

        return {'FINISHED'}

class D2P_OT_LiquidSculpt(bpy.types.Operator):
    """Convert to Subdivided Plane & Sculpt Liquid"""
    bl_idname = "d2p.sculpt_liquid"
    bl_label = "Sculpt like Liquid"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return is_canvas_mesh(context.object)

    def execute(self, context):
        scene = context.scene

        bpy.ops.paint.texture_paint_toggle()
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.subdivide(number_cuts=100, smoothness=0)
        bpy.ops.mesh.subdivide(number_cuts=2, smoothness=0)
        bpy.ops.sculpt.sculptmode_toggle()
        bpy.ops.paint.brush_select(sculpt_tool='GRAB', create_missing=False)
        scene.tool_settings.sculpt.use_symmetry_x = False
        bpy.ops.view3d.localview()

        return {'FINISHED'}

class D2P_OT_CanvasX(bpy.types.Operator):
    """Flip the Canvas Left/Right"""
    bl_idname = "d2p.canvas_horizontal"
    bl_label = "Canvas Horizontal"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return is_canvas_mesh(context.object)

    def execute(self, context):
        scene = context.scene
        layer = bpy.context.view_layer
        layer.update()

        # toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()

        scene = bpy.context.scene

        original_area = bpy.context.area.type

        # toggle edit mode
        bpy.ops.object.editmode_toggle()

        #####select all mesh
        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action='SELECT')

        ####change editor to UV Editor
        bpy.context.area.ui_type = 'UV'

        # + select the uvs
        bpy.ops.uv.select_all(action='SELECT')
        bpy.ops.uv.select_all(action='SELECT')

        ######scale -1 on axis
        bpy.ops.transform.resize(value=(-1, 1, 1),
                                 orient_type='GLOBAL',
                                 orient_matrix=((1, 0, 0), (0, 1, 0),
                                                (0, 0, 1)),
                                 orient_matrix_type='GLOBAL',
                                 constraint_axis=(True, False, False),
                                 mirror=True, use_proportional_edit=False,
                                 proportional_edit_falloff='SMOOTH',
                                 proportional_size=1,
                                 use_proportional_connected=False,
                                 use_proportional_projected=False)

        # back to Object mode
        bpy.ops.object.editmode_toggle()

        #####return to original window editor
        bpy.context.area.type = original_area

        bpy.ops.paint.texture_paint_toggle()

        return {'FINISHED'}

class D2P_OT_CanvasY(bpy.types.Operator):
    """Flip the Canvas Top/Bottom"""
    bl_idname = "d2p.canvas_vertical"
    bl_label = "Canvas Vertical"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return is_canvas_mesh(context.object)

    def execute(self, context):
        scene = context.scene
        layer = bpy.context.view_layer
        layer.update()

        # toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()

        scene = bpy.context.scene

        original_area = bpy.context.area.type

        # toggle edit mode
        bpy.ops.object.editmode_toggle()

        #####select all mesh
        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action='SELECT')

        ####change editor to UV Editor
        bpy.context.area.ui_type = 'UV'

        # + select the uvs
        bpy.ops.uv.select_all(action='SELECT')
        bpy.ops.uv.select_all(action='SELECT')

        ######scale -1 on axis
        bpy.ops.transform.resize(value=(1, -1, 1),
                                 orient_type='GLOBAL',
                                 orient_matrix=((1, 0, 0), (0, 1, 0),
                                                (0, 0, 1)),
                                 orient_matrix_type='GLOBAL',
                                 constraint_axis=(True, False, False),
                                 mirror=True, use_proportional_edit=False,
                                 proportional_edit_falloff='SMOOTH',
                                 proportional_size=1,
                                 use_proportional_connected=False,
                                 use_proportional_projected=False)

        # back to Object mode
        bpy.ops.object.editmode_toggle()

        #####return to original window editor
        bpy.context.area.type = original_area

        bpy.ops.paint.texture_paint_toggle()

        return {'FINISHED'}

class D2P_OT_CanvasReset(bpy.types.Operator):
    """Reset Canvas Rotation"""
    bl_idname = "d2p.canvas_resetrot"
    bl_label = "Canvas Reset Rotation"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = obj.type == 'MESH'
            B = context.mode == 'PAINT_TEXTURE'
            return A and B

    def execute(self, context):
        scene = context.scene
        layer = bpy.context.view_layer
        layer.update()

        # reset canvas rotation
        bpy.ops.object.rotation_clear()
        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS',
                                  center='MEDIAN')

        return {'FINISHED'}

class D2P_OT_PixelsToBorder(bpy.types.Operator):
    """ Convert the pixel value into the proportion needed
        by the Blender native property """
    bl_idname = "d2p.pixelstoborder"
    bl_label = "Convert Pixels to Border proportion"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        C = bpy.context

        X = C.scene.render.resolution_x
        Y = C.scene.render.resolution_y

        C.scene.render.border_min_x = C.scene.x_min_pixels / X
        C.scene.render.border_max_x = C.scene.x_max_pixels / X
        C.scene.render.border_min_y = C.scene.y_min_pixels / Y
        C.scene.render.border_max_y = C.scene.y_max_pixels / Y

        if C.scene.x_min_pixels > X:
            C.scene.x_min_pixels = X
        if C.scene.x_max_pixels > X:
            C.scene.x_max_pixels = X
        if C.scene.y_min_pixels > Y:
            C.scene.y_min_pixels = Y
        if C.scene.y_max_pixels > Y:
            C.scene.y_max_pixels = Y

        return {'FINISHED'}

class D2P_OT_BorderToPixels(bpy.types.Operator):
    """ Convert the Blender native property value to pixels"""
    bl_idname = "d2p.bordertopixels"
    bl_label = "Convert border values to pixels"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        C = bpy.context

        X = C.scene.render.resolution_x
        Y = C.scene.render.resolution_y

        C.scene.x_min_pixels = int(C.scene.render.border_min_x * X)
        C.scene.x_max_pixels = int(C.scene.render.border_max_x * X)
        C.scene.y_min_pixels = int(C.scene.render.border_min_y * Y)
        C.scene.y_max_pixels = int(C.scene.render.border_max_y * Y)

        return {'FINISHED'}

class D2P_OT_BorderCrop(bpy.types.Operator):
    """Turn on Border Crop in Render Settings"""
    bl_description = "Border Crop ON"
    bl_idname = "d2p.border_crop"
    bl_label = ""
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        rs = context.scene.render
        rs.use_border = True
        rs.use_crop_to_border = True
        return {'FINISHED'}


class D2P_OT_BorderUnCrop(bpy.types.Operator):
    """Turn off Border Crop in Render Settings"""
    bl_description = "Border Crop OFF"
    bl_idname = "d2p.border_uncrop"
    bl_label = ""
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        rs = context.scene.render
        rs.use_border = False
        rs.use_crop_to_border = False
        return {'FINISHED'}

class D2P_OT_BorderCropToggle(bpy.types.Operator):
    """Set Border Crop in Render Settings"""
    bl_description = "Border Crop On/Off TOGGLE"
    bl_idname = "d2p.border_toggle"
    bl_label = ""
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        return poll_apt(self, context)

    def execute(self, context):
        scene = context.scene
        rs = context.scene.render

        if not (scene.prefs_are_locked):
            if rs.use_border and rs.use_crop_to_border:
                bpy.ops.d2p.border_uncrop()
                scene.bordercrop_is_activated = False
            else:
                bpy.ops.d2p.border_crop()
                scene.bordercrop_is_activated = True
        return {'FINISHED'}

class D2P_OT_Image2Scene(bpy.types.Operator):
    """IMAGE EDITOR FOR CREATING NEW BLANK CANVAS IMAGE"""
    bl_idname = "d2p.new_image"
    bl_label = "New Image"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        layer = bpy.context.view_layer
        layer.update()
        
        # Call user prefs window
        bpy.ops.screen.userpref_show('INVOKE_DEFAULT')
        #bpy.ops.wm.window_new()
        
        # Change area type
        area = context.window_manager.windows[-1].screen.areas[0]
        area.type = 'IMAGE_EDITOR'
                
        return {'FINISHED'}

class D2P_OT_SaveImage(bpy.types.Operator): # works IF image is already in Slot2Display prior
    """Save Image"""
    bl_idname = "d2p.save_current"
    bl_label = "Save Image Current"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = obj.type == 'MESH'
            B = context.mode == 'PAINT_TEXTURE'
            return A and B

    def execute(self, context):
        scene = context.scene
        layer = bpy.context.view_layer
        layer.update()
        original_type = bpy.context.area.type
        bpy.context.area.type = 'IMAGE_EDITOR'

        # SAVE CHANGES MADE TO IMAGE
        bpy.ops.image.save()

        bpy.context.area.type = original_type

        return {'FINISHED'}

class D2P_OT_SaveIncrem(bpy.types.Operator): #works already with Material and Image IF image is opened in Editor prior
    """Save Incremential Images - MUST SAVE SESSION FILE FIRST"""
    bl_description = ""
    bl_idname = "d2p.save_increm"
    bl_label = "Save incremential Image Current"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = obj.type == 'MESH'
            B = context.mode == 'PAINT_TEXTURE'
            return A and B
    ####new code
    def execute(self, context):
        try:
            image = get_active_image_from_image_editor()
            save_incremental_copy(image)
            self.report({'INFO'}, "Incremental copy saved.")
        except ValueError as e:
            self.report({'ERROR'}, str(e))
        return {'FINISHED'}

class D2P_OT_SaveDirty(bpy.types.Operator):  #Already Good for Image and Material
    """Save All Modified Images or Pack if Unsaved"""
    bl_description = "Save all modified images or pack them if unsaved"
    bl_idname = "d2p.save_dirty"
    bl_label = "Save All Modified Images or Pack if Unsaved"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if obj is not None:
            A = obj.type == 'MESH'
            B = context.mode == 'PAINT_TEXTURE'
            return A and B
        return False

    def execute(self, context):
        # Save or pack all modified images
        for image in bpy.data.images:  #already packs all in Image and Material modes
            if image.is_dirty:
                if image.filepath:
                    try:
                        image.save()
                        self.report({'INFO'}, f"Saved image: {image.name}")
                    except Exception as e:
                        self.report({'ERROR'}, f"Failed to save image {image.name}: {str(e)}")
                else:
                    image.pack()
                    self.report({'INFO'}, f"Packed image: {image.name}")

        return {'FINISHED'}
class D2P_OT_ReloadAll(bpy.types.Operator):  #Already Good for Image and Material
    '''Reload ALL IMAGES to last Saved State'''
    bl_idname = "d2p.reload_all"
    bl_label = "Reload ALL IMAGES"
    bl_options = {'REGISTER','UNDO'}


    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = obj.type == 'MESH'
            B = context.mode == 'PAINT_TEXTURE'
            return A and B
    def execute(self, context):
        for image in bpy.data.images:## already affects Image mode as well as Material mode images
            image.reload()
        return {'FINISHED'}


class D2P_OT_ImageReload(bpy.types.Operator):  #Fixed for Material and Image mode
    """Reload Image Last Saved State"""
    bl_idname = "d2p.reload_saved_state"
    bl_label = "Reload Image Save Point"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = obj.type == 'MESH'
            B = context.mode == 'PAINT_TEXTURE'
            return A and B

    def execute(self, context):
        # Store the current UI type to switch back after
        original_type = context.area.ui_type

        image = None

        # Detect the current paint mode
        paint_mode = context.scene.tool_settings.image_paint.mode

        if paint_mode == 'MATERIAL':
            # Handle MATERIAL mode: get the image from the material's texture paint slot
            mat = context.object.active_material
            if mat and mat.texture_paint_images:
                image = mat.texture_paint_images[mat.paint_active_slot]
            else:
                self.report({'INFO'}, "No active material slot to reload.")
                return {'CANCELLED'}

        elif paint_mode == 'IMAGE':
            # Handle IMAGE mode: get the active image from the image paint canvas
            image = context.scene.tool_settings.image_paint.canvas
            if not image:
                self.report({'INFO'}, "No active image to reload.")
                return {'CANCELLED'}

        # If an image was found, reload it
        if image:
            # Switch to Image Editor to reload the image
            context.area.ui_type = 'IMAGE_EDITOR'
            context.space_data.image = image
            bpy.ops.image.reload()  # Reload the image to its last saved state
        else:
            self.report({'WARNING'}, "No image found to reload.")
            return {'CANCELLED'}

        # Restore the original UI type
        context.area.ui_type = original_type

        return {'FINISHED'}

class D2P_OT_Guide2Canvas(bpy.types.Operator):
    """Create new empty guide or selected guide relocate origin"""
    bl_idname = "d2p.empty_guides"
    bl_label = "Empty Guides Constrained"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and (obj.type == 'MESH' or obj.type == 'EMPTY')

    def execute(self, context):
        scene = context.scene
        layer = bpy.context.view_layer
        layer.update()

        # Toggle texpaint and deselect
        obj = context.active_object

        # Find the '_canvas' object
        canvas_object = None
        for ob in bpy.data.objects:
            if ob.name.endswith('_canvas'):
                canvas_object = ob
                break

        if not canvas_object:
            self.report({'ERROR'}, "No '_canvas' object found.")
            return {'CANCELLED'}

        if obj == canvas_object:
            bpy.ops.paint.texture_paint_toggle()
            bpy.ops.object.select_all(action='DESELECT')

            # Check for existing 'Symmetry Guide'
            symmetry_guide = None
            for ob in bpy.data.objects:
                if ob.type == 'EMPTY' and ob.name == 'Symmetry Guide':
                    symmetry_guide = ob
                    break

            if symmetry_guide:
                bpy.ops.object.select_all(action='DESELECT')
                symmetry_guide.select_set(True)
                bpy.context.view_layer.objects.active = symmetry_guide
                bpy.ops.view3d.snap_cursor_to_selected()
                bpy.ops.object.select_all(action='DESELECT')
                symmetry_guide.select_set(False)
                canvas_object.select_set(True)
                bpy.context.view_layer.objects.active = canvas_object
            else:
                bpy.ops.object.empty_add(type='SPHERE', location=(0, 0, 0), radius=0.01)
                new_empty = context.object
                new_empty.name = "Symmetry Guide"
                bpy.ops.transform.resize(value=(10, 10, 10))
                new_empty.parent = canvas_object
                bpy.ops.view3d.snap_cursor_to_selected()
                bpy.ops.object.select_all(action='DESELECT')
                canvas_object.select_set(True)
                bpy.context.view_layer.objects.active = canvas_object

            bpy.ops.paint.texture_paint_toggle()
            return {'FINISHED'}

        elif obj.name == 'Symmetry Guide':
            bpy.ops.view3d.snap_cursor_to_selected()

            # Set the canvas object as active and in object mode before running the operator
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            canvas_object.select_set(True)
            bpy.context.view_layer.objects.active = canvas_object

            # Set the origin of the canvas object to the cursor
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

            # Deselect all and reselect the Symmetry Guide
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj

            # Switch canvas object back to texture paint mode
            bpy.ops.object.select_all(action='DESELECT')
            canvas_object.select_set(True)
            bpy.context.view_layer.objects.active = canvas_object

            return {'FINISHED'}

        return {'CANCELLED'}


class D2P_OT_Recenter(bpy.types.Operator):
    """Snaps cursor and Selected Object to World Center"""
    bl_idname = "d2p.center_object"
    bl_label = "Center Object to World"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        # cursor to world origin
        bpy.ops.view3d.snap_cursor_to_center()
        # selected object origin to geometry - SYMMETRY GUIDE
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
        bpy.ops.view3d.snap_selected_to_cursor(use_offset=True)
        
        return {'FINISHED'}

class D2P_OT_Align2Face(bpy.types.Operator):
    """fast front of face view paint"""
    bl_description = ""
    bl_idname = "d2p.frontof_paint"
    bl_label = "Front Of Paint"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = context.mode == 'PAINT_TEXTURE'
            B = obj.type == 'MESH'
            return A and B

    def execute(self, context):
        # init
        paint = bpy.ops.paint
        object = bpy.ops.object
        contextObj = context.object

        #context.space_data.viewport_shade = 'TEXTURED'  # texture draw
        paint.texture_paint_toggle()
        object.editmode_toggle()
        #previous was view3d.numpad()
        bpy.ops.view3d.view_axis(type='TOP', align_active=True)
        object.editmode_toggle()
        paint.texture_paint_toggle()
        contextObj.data.use_paint_mask = True
        return {'FINISHED'}

class D2P_OT_BorderCropToggle(bpy.types.Operator):
    """Set Border Crop in Render Settings"""
    bl_description = "Border Crop On/Off TOGGLE"
    bl_idname = "d2p.border_toggle"
    bl_label = ""
    bl_options = {'REGISTER', 'UNDO'}

    # @classmethod
    # def poll(self, context):
    # return poll_apt(self, context)

    def execute(self, context):
        scene = context.scene
        rs = context.scene.render

        if not (scene.prefs_are_locked):
            if rs.use_border and rs.use_crop_to_border:
                bpy.ops.ez_draw.border_uncrop()
                scene.bordercrop_is_activated = False
            else:
                bpy.ops.ez_draw.border_crop()
                scene.bordercrop_is_activated = True
        return {'FINISHED'}


class D2P_OT_ReprojectMask(bpy.types.Operator):
    """Reproject Mask"""
    bl_idname = "d2p.reproject_mask"
    bl_label = "Reproject Mask to UV from Camera View"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        A = obj is not None
        if A:
            B = obj.type == 'CURVE' or 'MESH'
            return B

    def execute(self, context):
        scene = context.scene

        obj = context.active_object

        if obj.type == 'CURVE' and obj.mode == 'EDIT':

            bpy.ops.object.editmode_toggle()
            bpy.ops.object.convert(target='MESH')
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='TOGGLE')
            bpy.ops.uv.project_from_view(camera_bounds=True,
                                         correct_aspect=False,
                                         scale_to_bounds=False)
            bpy.ops.mesh.normals_make_consistent(inside=False)
            bpy.ops.object.editmode_toggle()
                      
            bpy.ops.paint.texture_paint_toggle()  # toggle texpaint

        elif obj.type == 'CURVE' and obj.mode == 'OBJECT':
            bpy.ops.object.convert(target='MESH')
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='TOGGLE')
            bpy.ops.uv.project_from_view(camera_bounds=True,
                                         correct_aspect=False,
                                         scale_to_bounds=False)
            bpy.ops.mesh.normals_make_consistent(inside=False)
            bpy.ops.object.editmode_toggle()
            
            bpy.ops.paint.texture_paint_toggle()  # toggle texpaint

        elif obj.type == 'MESH' and obj.mode == 'OBJECT':

            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='TOGGLE')
            bpy.ops.uv.project_from_view(camera_bounds=True,
                                         correct_aspect=False,
                                         scale_to_bounds=False)
            bpy.ops.mesh.normals_make_consistent(inside=False)
            bpy.ops.object.editmode_toggle()
            
            bpy.ops.paint.texture_paint_toggle()  # toggle texpaint

        elif obj.type == 'MESH' and obj.mode == 'TEXTURE_PAINT':

            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='TOGGLE')
            bpy.ops.uv.project_from_view(camera_bounds=True,
                                         correct_aspect=False,
                                         scale_to_bounds=False)
            bpy.ops.mesh.normals_make_consistent(inside=False)

            bpy.ops.object.editmode_toggle()
            
            bpy.ops.paint.texture_paint_toggle()  # toggle texpaint

        return {'FINISHED'}


class D2P_OT_my_enum_shapes(bpy.types.Operator):
    bl_label = "Add Mask Object"
    bl_idname = "d2p.my_enum_shapes"

    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool
        
        # Find the parent object with suffix '_canvas'
        suffix = '_canvas'
        parent_object = None
        for obj in scene.objects:
            if obj.name.endswith(suffix):
                parent_object = obj
                break
        
        if not parent_object:
            self.report({'WARNING'}, f"No object with suffix '{suffix}' found in the scene.")
            return {'CANCELLED'}
        
        def add_child_constraint(obj):
            bpy.ops.object.constraint_add(type='CHILD_OF')
            obj.constraints["Child Of"].target = parent_object

        def copy_material_to_new_object(new_obj):
            if parent_object.material_slots:
                parent_material = parent_object.material_slots[0].material
                new_obj.data.materials.append(parent_material)
            else:
                self.report({'WARNING'}, f"Parent object '{parent_object.name}' has no materials.")
        
        if mytool.my_enum == 'OP1':
            # Add a new bezier curve
            bpy.ops.curve.primitive_bezier_curve_add(radius=1, enter_editmode=False, align='WORLD', location=(0, 0, 0.15), scale=(1, 1, 1))
            new_obj = bpy.context.object
            # Move new_obj to 'canvas_view' collection
            move_object_to_collection(new_obj, 'canvas_view')
            add_child_constraint(new_obj)
            bpy.ops.object.editmode_toggle()
            bpy.ops.curve.delete(type='VERT')
            bpy.ops.object.editmode_toggle()
            copy_material_to_new_object(new_obj)
            new_obj.data.dimensions = '2D'
            new_obj.data.fill_mode = 'BOTH'
            bpy.ops.object.editmode_toggle()
            bpy.ops.wm.tool_set_by_id(name="builtin.draw")

        elif mytool.my_enum == 'OP2':
            # Add a new bezier curve and set handle type to VECTOR
            bpy.ops.curve.primitive_bezier_curve_add(enter_editmode=True, align='WORLD', location=(0, 0, 0.15), scale=(1, 1, 1))
            new_obj = bpy.context.object
            # Move new_obj to 'canvas_view' collection
            move_object_to_collection(new_obj, 'canvas_view')
            add_child_constraint(new_obj)
            bpy.ops.curve.handle_type_set(type='VECTOR')
            bpy.ops.object.editmode_toggle()
            copy_material_to_new_object(new_obj)
            new_obj.data.dimensions = '2D'
            new_obj.data.fill_mode = 'BOTH'
            bpy.ops.transform.resize(value=(0.1, 0.1, 0.1))
            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

        elif mytool.my_enum == 'OP3':
            # Add a new bezier circle
            bpy.ops.curve.primitive_bezier_circle_add(radius=0.25, enter_editmode=False, align='WORLD', location=(0, 0, 0.15), scale=(1, 1, 1))
            new_obj = bpy.context.object
            # Move new_obj to 'canvas_view' collection
            move_object_to_collection(new_obj, 'canvas_view')
            add_child_constraint(new_obj)
            copy_material_to_new_object(new_obj)
            new_obj.data.dimensions = '2D'
            new_obj.data.fill_mode = 'BOTH'
            bpy.ops.object.editmode_toggle()
            bpy.ops.curve.handle_type_set(type='VECTOR')
            bpy.ops.transform.rotate(value=0.785398, orient_axis='Z')
            bpy.ops.object.editmode_toggle()
            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

        elif mytool.my_enum == 'OP4':
            # Add a new bezier circle
            bpy.ops.curve.primitive_bezier_circle_add(radius=0.25, enter_editmode=False, align='WORLD', location=(0, 0, 0.15), scale=(1, 1, 1))
            new_obj = bpy.context.object
            # Move new_obj to 'canvas_view' collection
            move_object_to_collection(new_obj, 'canvas_view')
            add_child_constraint(new_obj)
            copy_material_to_new_object(new_obj)
            new_obj.data.dimensions = '2D'
            new_obj.data.fill_mode = 'BOTH'
            bpy.ops.object.editmode_toggle()
            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

        return {'FINISHED'}


class D2P_OT_RemoveMods(bpy.types.Operator):
    """Remove Modifiers"""
    bl_idname = "d2p.remove_modifiers"
    bl_label = "Remove modifiers"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = obj.type == 'MESH'
            B = context.mode == 'OBJECT'
            return A and B

    def execute(self, context):
        scene = context.scene
        # init
        obj = context.object

        bpy.ops.object.convert(target='MESH')

        return {'FINISHED'}


class D2P_OT_SolidifyDifference(bpy.types.Operator):
    """Solidify and Difference Mask"""
    bl_idname = "d2p.solidify_difference"
    bl_label = "Add Solidify and Difference Bool"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = obj.type == 'MESH'
            B = context.mode == 'OBJECT'
            return A and B

    def execute(self, context):
        scene = context.scene
        context = bpy.context

        obj = context.active_object

        mod = obj.modifiers.new("Solidify", 'SOLIDIFY')
        # add a solidify modifier on active object

        mod.thickness = 0.01  # set modifier properties
        obj.location.z = 0

        for o in context.selected_objects:
            if o == obj:
                continue
            # see if there is already a modifier named  \
            # "SelectedSolidify" and use it
            mod = o.modifiers.get("SelectedSolidify")
            if mod is None:
                # otherwise add a modifier to selected object
                mod = o.modifiers.new("SelectedSolidify", 'SOLIDIFY')
                mod.thickness = 0.3
                o.location.z += 0.1
            # add a boolean mod
            # obj = context.active_object
            o.display_type = 'WIRE'

            boolmod = obj.modifiers.new("Bool", 'BOOLEAN')
            boolmod.object = o
            boolmod.solver = 'FAST'
            boolmod.operation = 'DIFFERENCE'

            return {'FINISHED'}

class D2P_OT_SolidifyUnion(bpy.types.Operator):
    """Solidify and Union Mask"""
    bl_idname = "d2p.solidify_union"
    bl_label = "Add Solidify and Union Bool"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = obj.type == 'MESH'
            B = context.mode == 'OBJECT'
            return A and B

    def execute(self, context):
        scene = context.scene
        context = bpy.context

        obj = context.active_object

        mod = obj.modifiers.new("Solidify", 'SOLIDIFY')
        # add a solidify modifier on active object

        mod.thickness = 0.01  # set modifier properties
        obj.location.z = 0

        for o in context.selected_objects:
            if o == obj:
                continue
            # see if there is already a modifier named
            # "SelectedSolidify" and use it
            mod = o.modifiers.get("SelectedSolidify")
            if mod is None:
                # otherwise add a modifier to selected object
                mod = o.modifiers.new("SelectedSolidify", 'SOLIDIFY')
                mod.thickness = 0.01
                o.location.z = 0
            # add a boolean mod
            # obj = context.active_object
            # o.display_type = 'WIRE'

            boolmod = obj.modifiers.new("Bool", 'BOOLEAN')
            boolmod.object = o
            boolmod.solver = 'FAST'
            boolmod.operation = 'UNION'

            return {'FINISHED'}

class D2P_OT_SelectVertgroup(bpy.types.Operator):
    """Select Vertgroup"""
    bl_idname = "d2p.select_vgroup"

    bl_label = "Select VGroup"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.editmode_toggle()  # toggle editmode
        bpy.ops.object.vertex_group_select()  # select current active vgroup
        bpy.ops.object.editmode_toggle()  # toggle editmode
        bpy.ops.paint.texture_paint_toggle()  # Texpaint
        bpy.context.object.data.use_paint_mask = True
        # set face select masking on in case we forgot

        return {'FINISHED'}


class D2P_OT_DeselectVertgroup(bpy.types.Operator):
    """Deselect Vertgroup"""
    bl_idname = "d2p.deselect_vgroup"

    bl_label = "Deselect VGroup"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.editmode_toggle()  # toggle editmode
        bpy.ops.object.vertex_group_deselect()  # select current active vgroup
        bpy.ops.object.editmode_toggle()  # toggle editmode
        bpy.ops.paint.texture_paint_toggle()  # Texpaint
        bpy.context.object.data.use_paint_mask = True
        # set face select masking on in case we forgot

        return {'FINISHED'}


class D2P_OT_AssignVertgroup(bpy.types.Operator):
    """Assign Vertgroup"""
    bl_idname = "d2p.assign_vgroup"

    bl_label = "Assign VGroup"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.editmode_toggle()  # toggle editmode
        bpy.ops.object.vertex_group_assign()  # select current active vgroup
        bpy.ops.object.editmode_toggle()  # toggle editmode
        bpy.ops.paint.texture_paint_toggle()  # Texpaint
        bpy.context.object.data.use_paint_mask = True
        # set face select masking on in case we forgot

        return {'FINISHED'}


class D2P_OT_UnassignVertgroup(bpy.types.Operator):
    """Unassign Vertgroup"""
    bl_idname = "d2p.unassign_vgroup"

    bl_label = "Unassign VGroup"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.editmode_toggle()  # toggle editmode
        bpy.ops.object.vertex_group_remove_from()  # select current active vgroup
        bpy.ops.object.editmode_toggle()  # toggle editmode
        bpy.ops.paint.texture_paint_toggle()  # Texpaint
        bpy.context.object.data.use_paint_mask = True
        # set face select masking on in case we forgot

        return {'FINISHED'}

class D2P_OT_getFaceMaskGroups(bpy.types.Operator):
    """FMG+ _ Get Face Mask Groups from Linked Mesh Islands"""
    bl_idname = "d2p.getfacemaskgroups"
    bl_label = "Get Face Mask Groups"
    bl_options = {'REGISTER', 'UNDO'}

    ####answer from batFINGER
    @classmethod
    def poll(self, context):
        obj = context.active_object
        # fmg = obj.vertex_group

        if obj is not None:
            A = obj.type == 'MESH'
            B = context.mode == 'PAINT_TEXTURE' or 'OBJECT_MODE'
            return A and B

    def execute(self, context):
        scene = context.scene
        context = bpy.context

        def island_verts(mesh):
            #   import bmesh
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type='VERT')
            bpy.ops.mesh.select_all(action='DESELECT')

            bm = bmesh.from_edit_mesh(mesh)
            bm.verts.ensure_lookup_table()
            verts = [v.index for v in bm.verts]

            vgs = []
            while len(verts):
                bm.verts[verts[0]].select = True
                bpy.ops.mesh.select_linked()
                sv = [v.index for v in bm.verts if v.select]
                vgs.append(sv)
                for v in sv:
                    bm.verts[v].select = False
                    verts.remove(v)
            bm.free()  # prob not nec.
            bpy.ops.object.mode_set(mode='OBJECT')
            return vgs

            # test run

        obj = bpy.context.object
        mesh = obj.data
        vgs = island_verts(mesh)

        for vg in vgs:
            group = obj.vertex_groups.new()
            group.name = "FMG by Island"
            group.add(vg, 1.0, 'ADD')

        return {'FINISHED'}

class D2P_OT_GPencil2Canvas(bpy.types.Operator):
    """Add Grease Pencil Object to Paint"""
    bl_idname = "d2p.grease_object"
    bl_label = "Must Render F12 to capture GPencil in Canvas Project"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if obj is not None:
            is_mesh_or_curve = obj.type in {'MESH', 'CURVE'}
            in_object_or_paint_texture_mode = context.mode in {'OBJECT', 'PAINT_TEXTURE'}
            return is_mesh_or_curve and in_object_or_paint_texture_mode
        return False

    def execute(self, context):
        scene = context.scene
        active_obj = context.active_object

        bpy.context.space_data.shading.type = 'SOLID'
        bpy.ops.paint.texture_paint_toggle()

        # Create Grease Pencil Object
        bpy.ops.object.gpencil_add(align='WORLD', location=(0, 0, 0.0125), scale=(1, 1, 1), type='EMPTY')
        gpencil_obj = context.object

        # Find the parent object with suffix '_canvas'
        suffix = '_canvas'
        parent_object = next((obj for obj in scene.objects if obj.name.endswith(suffix)), None)

        if not parent_object:
            self.report({'WARNING'}, f"No object with suffix '{suffix}' found in the scene.")
            return {'CANCELLED'}

        # Parent the Grease Pencil Object directly
        gpencil_obj.parent = parent_object
        gpencil_obj.matrix_parent_inverse.identity()  # Clear parent inverse matrix

        # Additional Setup
        bpy.ops.gpencil.paintmode_toggle()
        gpencil_obj.data.layers["GP_Layer"].use_lights = False

        # Make some setup shortcuts
        scene.tool_settings.gpencil_stroke_placement_view3d = 'SURFACE'
        scene.tool_settings.gpencil_paint.color_mode = 'VERTEXCOLOR'

        return {'FINISHED'}


class D2P_OT_Slot2Display(bpy.types.Operator): #Fixed for Material and Image modes
    '''Display selected paint slot or image in new window'''
    bl_label = "Display Active Slot or Image"
    bl_idname = "d2p.display_active_slot"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # Ensure the object has an active material and/or image for painting
        paint_mode = context.scene.tool_settings.image_paint.mode
        obj = context.object
        if obj is None:
            return False

        if paint_mode == 'MATERIAL':
            return obj.active_material and obj.active_material.texture_paint_images
        elif paint_mode == 'IMAGE':
            return bool(context.scene.tool_settings.image_paint.canvas)
        return False

    def execute(self, context):
        # Detect the current paint mode
        paint_mode = context.scene.tool_settings.image_paint.mode

        if paint_mode == 'MATERIAL':
            # Handle MATERIAL mode: Display the texture paint slot from the material
            mat = context.object.active_material
            if mat and mat.texture_paint_images:
                image = mat.texture_paint_images[mat.paint_active_slot]
            else:
                self.report({'INFO'}, "No active material slot")
                return {'CANCELLED'}

        elif paint_mode == 'IMAGE':
            # Handle IMAGE mode: Display the active image from the image paint canvas
            image = context.scene.tool_settings.image_paint.canvas
            if not image:
                self.report({'INFO'}, "No active image")
                return {'CANCELLED'}

        # Open a new window and set the area to IMAGE_EDITOR
        bpy.ops.wm.window_new()
        new_window = context.window_manager.windows[-1]
        area = new_window.screen.areas[0]
        area.type = 'IMAGE_EDITOR'

        # Set the image in the newly created image editor space
        space = area.spaces.active
        space.image = image
        space.mode = 'PAINT'

        self.report({'INFO'}, f"Displaying {paint_mode.lower()} image")
        return {'FINISHED'}

########################################
#EZPaint Adopted Testing   needs work
########################################

class D2P_OT_BrushPopup(bpy.types.Operator):
    """Brush popup"""
    bl_idname = "view3d.brush_popup"
    bl_label = "Brush Settings"
    COMPAT_ENGINES = {'BLENDER_EEVEE_NEXT', 'CYCLES'}
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        if context.active_object:
            A = context.active_object.type == 'MESH'
            B = context.mode in {'PAINT_TEXTURE', 'PAINT_VERTEX', 'PAINT_WEIGHT'}
            return A and B

    @staticmethod
    def check(self, context):
        return True

    @staticmethod
    def paint_settings(context):
        toolsettings = context.tool_settings

        if context.vertex_paint_object:
            return toolsettings.vertex_paint
        elif context.weight_paint_object:
            return toolsettings.weight_paint
        elif context.image_paint_object:
            if (toolsettings.image_paint and toolsettings.image_paint.detect_data()):
                return toolsettings.image_paint

            return None
        return None

    @staticmethod
    def unified_paint_settings(parent, context):
        ups = context.tool_settings.unified_paint_settings
        parent.label(text="Unified Settings:")
        row = parent.row()
        row.prop(ups, "use_unified_size", text="Size")
        row.prop(ups, "use_unified_strength", text="Strength")
        if context.weight_paint_object:
            parent.prop(ups, "use_unified_weight", text="Weight")
        elif context.vertex_paint_object or context.image_paint_object:
            parent.prop(ups, "use_unified_color", text="Color")
        else:
            parent.prop(ups, "use_unified_color", text="Color")

    @staticmethod
    def prop_unified_size(parent, context, brush, prop_name, icon='NONE', text="", slider=False):
        ups = context.tool_settings.unified_paint_settings
        ptr = ups if ups.use_unified_size else brush
        parent.prop(ptr, prop_name, icon=icon, text=text, slider=slider)

    @staticmethod
    def prop_unified_strength(parent, context, brush, prop_name, icon='NONE', text="", slider=False):
        ups = context.tool_settings.unified_paint_settings
        ptr = ups if ups.use_unified_strength else brush
        parent.prop(ptr, prop_name, icon=icon, text=text, slider=slider)

    @staticmethod
    def prop_unified_weight(parent, context, brush, prop_name, icon='NONE', text="", slider=False):
        ups = context.tool_settings.unified_paint_settings
        ptr = ups if ups.use_unified_weight else brush
        parent.prop(ptr, prop_name, icon=icon, text=text, slider=slider)

    @staticmethod
    def prop_unified_color(parent, context, brush, prop_name, text=""):
        ups = context.tool_settings.unified_paint_settings
        ptr = ups if ups.use_unified_color else brush
        parent.prop(ptr, prop_name, text=text)

    @staticmethod
    def prop_unified_color_picker(parent, context, brush, prop_name, value_slider=True):
        ups = context.tool_settings.unified_paint_settings
        ptr = ups if ups.use_unified_color else brush
        parent.template_color_picker(ptr, prop_name, value_slider=value_slider)

    def brush_texpaint_common(self, layout, context, brush, settings, projpaint=False):
        capabilities = brush.image_paint_capabilities
        col = layout.column()
        row = col.row(align=True)
        row.use_property_split = False
        row.prop(brush, "color_type", expand=True)

        if brush.image_tool in {'DRAW', 'FILL'}:
            if brush.blend not in {'ERASE_ALPHA', 'ADD_ALPHA'}:
                # If the color type is not 'GRADIENT', show the color picker
                if brush.color_type != 'GRADIENT':
                    self.prop_unified_color_picker(col, context, brush, "color", value_slider=True)

                # Show palette if available
                if settings.palette:
                    col.template_palette(settings, "palette", color=True)
                    col.operator(D2P_OT_SetColorFamilies.bl_idname)
                # If the brush uses gradients
                if brush.color_type == 'GRADIENT':
                    col.label(text="Gradient Colors")
                    # Show the gradient color ramp
                    col.template_color_ramp(brush, "gradient", expand=True)
                    col.operator("brush.generate_gradient_from_palette", text="Gradient from Palette")

                    if brush.image_tool != 'FILL':
                        col.label(text="Background Color")
                        row = col.row(align=True)
                        self.prop_unified_color(row, context, brush, "secondary_color", text="")

                    if brush.image_tool == 'DRAW':
                        # Gradient stroke mode options
                        col.prop(brush, "gradient_stroke_mode", text="Mode")
                        if brush.gradient_stroke_mode in {'SPACING_REPEAT', 'SPACING_CLAMP'}:
                            col.prop(brush, "grad_spacing")
                    elif brush.image_tool == 'FILL':
                        col.prop(brush, "gradient_fill_mode")
                else:
                    # For non-gradient brushes, show the primary and secondary color options
                    row = col.row(align=True)
                    self.prop_unified_color(row, context, brush, "color", text="")
                    if brush.image_tool == 'FILL' and not projpaint:
                        col.prop(brush, "fill_threshold")
                    else:
                        self.prop_unified_color(row, context, brush, "secondary_color", text="")
                        row.separator()
                        row.operator("paint.brush_colors_flip", icon='FILE_REFRESH', text="")

        # Additional tool-specific settings
        elif brush.image_tool == 'SOFTEN':
            col = layout.column(align=True)
            col.row().prop(brush, "direction", expand=True)
            col.separator()
            col.prop(brush, "sharp_threshold")
            if not projpaint:
                col.prop(brush, "blur_kernel_radius")
            col.separator()
            col.prop(brush, "blur_mode")

        elif brush.image_tool == 'MASK':
            col.prop(brush, "weight", text="Mask Value", slider=True)

        elif brush.image_tool == 'CLONE':
            col.separator()

            # Handle project paint settings
            if projpaint:
                if settings.mode == 'MATERIAL':
                    col.prop(settings, "use_clone_layer", text="Clone from paint slot")
                elif settings.mode == 'IMAGE':
                    col.prop(settings, "use_clone_layer", text="Clone from image/UV map")

                if settings.use_clone_layer:
                    ob = context.active_object
                    col = layout.column()

                    # Handle MATERIAL mode
                    if settings.mode == 'MATERIAL':
                        if len(ob.material_slots) > 1:
                            col.label(text="Materials")
                            col.template_list("MATERIAL_UL_matslots", "", ob, "material_slots", ob,
                                              "active_material_index", rows=2)

                        mat = ob.active_material
                        if mat:
                            # Display active clone slot
                            col.label(text=f"Active Clone Slot: {mat.paint_clone_slot}")

                            # Display texture paint slots
                            if mat.texture_paint_slots:
                                for i, slot in enumerate(mat.texture_paint_slots):
                                    if slot:
                                        slot_name = slot.name if slot.name else f"Slot {i}"
                                        row = col.row()
                                        row.operator("view3d.set_active_clone_slot", text=slot_name).slot_index = i
                                    else:
                                        col.label(text=f"Slot {i} is empty", icon='ERROR')
                            else:
                                col.label(text="No texture slots available", icon='ERROR')


                    # Handle IMAGE mode
                    elif settings.mode == 'IMAGE':
                        mesh = ob.data
                        clone_text = mesh.uv_texture_clone.name if mesh.uv_texture_clone else ""
                        col.label(text="Source Clone Image")
                        col.template_ID(settings, "clone_image")
                        col.label(text="Source Clone UV Map")
                        col.menu("VIEW3D_MT_tools_projectpaint_clone", text=clone_text, translate=False)

            # Standard clone settings if not using project paint
            else:
                col.prop(brush, "clone_image", text="Image")
                col.prop(brush, "clone_alpha", text="Alpha")

        col.separator()

        if capabilities.has_radius:
            row = col.row(align=True)
            self.prop_unified_size(row, context, brush, "size", slider=True, text="Radius")
            row.prop(brush, "use_pressure_size", text="")

        row = col.row(align=True)
        self.prop_unified_strength(row, context, brush, "strength", text="Strength")
        self.prop_unified_strength(row, context, brush, "use_pressure_strength")

        if brush.image_tool in {'DRAW', 'FILL'}:
            col.separator()
            col.prop(brush, "blend", text="Blend")

        col = layout.column()
        if capabilities.has_accumulate:
            col.prop(brush, "use_accumulate")

        if projpaint:
            col.prop(brush, "use_alpha")

        col.prop(brush, "use_gradient")
        col.separator()
        col.template_ID(settings, "palette", new="palette.new")
        # col.operator(D2P_OT_SetColorFamilies.bl_idname)

    def draw(self, context):
        # Init values
        toolsettings = context.tool_settings
        settings = self.paint_settings(context)

        layout = self.layout
        col = layout.column()

        if not settings:
            row = col.row(align=True)
            row.label(text="Setup texture paint, please!")
        else:
            brush = settings.brush
            ipaint = toolsettings.image_paint
            # Stroke mode
            col.prop(brush, "stroke_method", text="")

            if brush.use_airbrush:
                col.separator()
                col.prop(brush, "rate", text="Rate", slider=True)

            if brush.use_space:
                col.separator()
                row = col.row(align=True)
                row.prop(brush, "spacing", text="Spacing")
                row.prop(brush, "use_pressure_spacing", toggle=True, text="")

            if brush.use_line or brush.use_curve:
                col.separator()
                row = col.row(align=True)
                row.prop(brush, "spacing", text="Spacing")

            if brush.use_curve:
                col.separator()
                col.template_ID(brush, "paint_curve", new="paintcurve.new")
                col.operator("paintcurve.draw")

            else:
                col.separator()

                row = col.row(align=True)
                row.prop(brush, "use_pressure_jitter", icon_only=True)
                if brush.use_pressure_jitter:
                    row.prop(brush, "jitter", slider=True)
                else:
                    row.prop(brush, "jitter_absolute")
                row.prop(brush, "use_pressure_jitter", toggle=True, text="")

                col = layout.column()
                col.separator()

                if brush.brush_capabilities.has_smooth_stroke:
                    col.prop(brush, "use_smooth_stroke")
                    if brush.use_smooth_stroke:
                        sub = col.column()
                        sub.prop(brush, "smooth_stroke_radius", text="Radius", slider=True)
                        sub.prop(brush, "smooth_stroke_factor", text="Factor", slider=True)

            layout.prop(settings, "input_samples")

            # Curve stroke
            if brush.curve_preset == 'CUSTOM':
                layout.template_curve_mapping(brush, "curve", brush=True)

            col = layout.column(align=True)
            row = col.row(align=True)
            row.operator("brush.curve_preset", icon='SMOOTHCURVE', text="").shape = 'SMOOTH'
            row.operator("brush.curve_preset", icon='SPHERECURVE', text="").shape = 'ROUND'
            row.operator("brush.curve_preset", icon='ROOTCURVE', text="").shape = 'ROOT'
            row.operator("brush.curve_preset", icon='SHARPCURVE', text="").shape = 'SHARP'
            row.operator("brush.curve_preset", icon='LINCURVE', text="").shape = 'LINE'
            row.operator("brush.curve_preset", icon='NOCURVE', text="").shape = 'MAX'

            # Symetries mode
            col = layout.column(align=True)
            row = col.row(align=True)
            obj = bpy.context.active_object

            # row.prop(ipaint, "use_mesh_mirror_x", text="X", toggle=False)
            # row.prop(ipaint, "use_mesh_mirror_y", text="Y", toggle=False)
            # row.prop(ipaint, "use_mesh_mirror_z", text="Z", toggle=False)
            # bpy.context.object.use_mesh_mirror_x = True
            row.prop(obj, "use_mesh_mirror_x", text="X", toggle=True)
            row.prop(obj, "use_mesh_mirror_y", text="Y", toggle=True)
            row.prop(obj, "use_mesh_mirror_z", text="Z", toggle=True)

            # imagepaint tool operate  buttons: UILayout.template_ID_preview()
            col = layout.split().column()
            ###################################### ICI PROBLEME d'icones de brosse !
            # bpy.context.tool_settings.image_paint.brush

            col.template_ID_preview(settings, "brush", new="brush.add", rows=1, cols=3)

            ########################################################################

            # Texture Paint Mode #
            if context.image_paint_object and brush:
                self.brush_texpaint_common(layout, context, brush, settings, True)

            ########################################################################
            # Weight Paint Mode #
            elif context.weight_paint_object and brush:

                col = layout.column()

                row = col.row(align=True)
                self.prop_unified_weight(row, context, brush, "weight", slider=True, text="Weight")

                row = col.row(align=True)
                self.prop_unified_size(row, context, brush, "size", slider=True, text="Radius")
                self.prop_unified_size(row, context, brush, "use_pressure_size")

                row = col.row(align=True)
                self.prop_unified_strength(row, context, brush, "strength", text="Strength")
                self.prop_unified_strength(row, context, brush, "use_pressure_strength")
                ####### need work here, Blend mode doesn't draw in popup
                col.prop(brush, "vertex_tool", text="Blend")

                if brush.vertex_tool == 'BLUR':
                    col.prop(brush, "use_accumulate")
                    col.separator()

                col = layout.column()
                col.prop(toolsettings, "use_auto_normalize", text="Auto Normalize")
                col.prop(toolsettings, "use_multipaint", text="Multi-Paint")

            ########################################################################
            # Vertex Paint Mode #
            elif context.vertex_paint_object and brush:
                col = layout.column()
                self.prop_unified_color_picker(col, context, brush, "color", value_slider=True)
                if settings.palette:
                    col.template_palette(settings, "palette", color=True)
                self.prop_unified_color(col, context, brush, "color", text="")

                col.separator()
                row = col.row(align=True)
                self.prop_unified_size(row, context, brush, "size", slider=True, text="Radius")
                self.prop_unified_size(row, context, brush, "use_pressure_size")

                row = col.row(align=True)
                self.prop_unified_strength(row, context, brush, "strength", text="Strength")
                self.prop_unified_strength(row, context, brush, "use_pressure_strength")

                col.separator()
                # col.prop(brush, "vertex_tool", text="Blend")
                col.prop(brush, "blend", text="Blend")

                col.separator()
                col.template_ID(settings, "palette", new="palette.new")

    def invoke(self, context, event):
        if context.space_data.type == 'IMAGE_EDITOR':
            context.space_data.mode = 'PAINT'

        return context.window_manager.invoke_props_dialog(self, width=180)
        # return context.window_manager.invoke_props_dialog(self, width=148)
        # return {'PASS_THROUGH'} ou {'CANCELLED'} si le bouton ok est cliqué

    def execute(self, context):
        return {'FINISHED'}

class D2P_OT_TexturePopup(bpy.types.Operator):
    """Texture popup"""
    bl_idname = "view3d.texture_popup"
    bl_label = "Texture & Mask"
    COMPAT_ENGINES = {'EEVEE', 'CYCLES'}
    bl_options = {'REGISTER', 'UNDO'}

    toggleMenu: bpy.props.BoolProperty(default=True)  # toogle texture or Mask menu

    def check(self, context):
        return True

    @classmethod
    def poll(self, context):
        obj =  context.active_object
        if obj is not None:
            A = obj.type == 'MESH'
            B = context.mode == 'PAINT_TEXTURE'
            return A and B

    def draw(self, context):
        # Init values
        toolsettings = context.tool_settings
        brush = toolsettings.image_paint.brush
        tex_slot = brush.texture_slot
        mask_tex_slot = brush.mask_texture_slot

        unified = toolsettings.unified_paint_settings
        settings = toolsettings.image_paint

        # ================================================== textures panel
        layout = self.layout

        # Parameter Toggle Menu
        _TITLE = 'TEXTURES' if self.toggleMenu else 'MASKS'
        _ICON = 'TEXTURE' if self.toggleMenu else 'MOD_MASK'
        Menu = layout.row()
        Menu.prop(self, "toggleMenu", text=_TITLE, icon=_ICON)


        if self.toggleMenu:
            col = layout.column()                                   #TEXTURES
            col.template_ID_preview(brush, "texture", new="texture.new", rows=3, cols=8)

            if brush.texture:
                row = layout.row(align=True)
                row.operator("paint.modify_brush_textures", text="Modify brush Texture", icon='ADD').toggleType: True

            layout.label(text="Brush Mapping:")

            # texture_map_mode
            layout.row().prop(tex_slot, "map_mode", text="")
            #layout.prop(tex_slot, "map_mode", text="Mapping")
            layout.separator()

            if tex_slot.map_mode == 'STENCIL':
                if brush.texture and brush.texture.type == 'IMAGE':
                    layout.operator("brush.stencil_fit_image_aspect")
                layout.operator("brush.stencil_reset_transform")

            # angle and texture_angle_source
            if tex_slot.has_texture_angle:
                col = layout.column()
                col.label(text="Angle:")
                col.prop(tex_slot, "angle", text="")
                if tex_slot.has_texture_angle_source:
                    col.prop(tex_slot, "use_rake", text="Rake")

                    if brush.brush_capabilities.has_random_texture_angle \
                                        and tex_slot.has_random_texture_angle:
                        col.prop(tex_slot, "use_random", text="Random")
                        if tex_slot.use_random:
                            col.prop(tex_slot, "random_angle", text="")


            # scale and offset
            split = layout.split()
            split.prop(tex_slot, "offset")
            split.prop(tex_slot, "scale")

            row = layout.row()
            row.operator(D2P_OT_MakeBrushImageTexture.bl_idname)
        else:
            col = layout.column()                                 #MASK TEXTURE
            col.template_ID_preview(brush, "mask_texture", new="texture.new", \
                                                                rows=3, cols=8)

            if brush.mask_texture:
                row = layout.row(align=True)
                row.operator("paint.modify_brush_textures", text="Modify brush Texture", icon='ADD').toggleType: False

            layout.label(text="Mask Mapping:")
            # map_mode
            layout.row().prop(mask_tex_slot, "mask_map_mode", text="")
            layout.separator()

            if mask_tex_slot.map_mode == 'STENCIL':
                if brush.mask_texture and brush.mask_texture.type == 'IMAGE':
                    layout.operator("brush.stencil_fit_image_aspect").mask = True
                layout.operator("brush.stencil_reset_transform").mask = True

            col = layout.column()
            col.prop(brush, "use_pressure_masking", text="")
            # angle and texture_angle_source
            if mask_tex_slot.has_texture_angle:
                col = layout.column()
                col.label(text="Angle:")
                col.prop(mask_tex_slot, "angle", text="")
                if mask_tex_slot.has_texture_angle_source:
                    col.prop(mask_tex_slot, "use_rake", text="Rake")

                    if brush.brush_capabilities.has_random_texture_angle and mask_tex_slot.has_random_texture_angle:
                        col.prop(mask_tex_slot, "use_random", text="Random")
                        if mask_tex_slot.use_random:
                            col.prop(mask_tex_slot, "random_angle", text="")

            # scale and offset
            split = layout.split()
            split.prop(mask_tex_slot, "offset")
            split.prop(mask_tex_slot, "scale")
            row = layout.row()
            row.operator(D2P_OT_MakeBrushImageTextureMask.bl_idname)


    def invoke(self, context, event):
        if context.space_data.type == 'IMAGE_EDITOR':
            context.space_data.mode = 'PAINT'
        return context.window_manager.invoke_props_dialog(self, width=146)

    def execute(self, context):
        return {'FINISHED'}
# new operator to fix selection of texslots
class D2P_OT_set_active_texture_slot(bpy.types.Operator):
    """Set the active texture slot"""
    bl_idname = "view3d.set_active_texture_slot"
    bl_label = "Set Active Texture Slot"

    slot_index: bpy.props.IntProperty()

    def execute(self, context):
        obj = context.object
        mat = obj.active_material

        if mat and mat.texture_paint_slots:
            mat.paint_active_slot = self.slot_index
            self.report({'INFO'}, f"Active texture slot set to: {self.slot_index}")
        else:
            self.report({'ERROR'}, "No texture slots found")

        return {'FINISHED'}


class D2P_OT_set_active_clone_slot(bpy.types.Operator):  # hack to get image layers for use as clone source
    """Set the active texture slot"""
    bl_idname = "view3d.set_active_clone_slot"
    bl_label = "Set Active Clone Slot"

    slot_index: bpy.props.IntProperty()

    def execute(self, context):
        obj = context.object
        mat = obj.active_material

        if mat and mat.texture_paint_slots:
            mat.paint_clone_slot = self.slot_index
            self.report({'INFO'}, f"Active texture slot set to: {self.slot_index}")
        else:
            self.report({'ERROR'}, "No texture slots found")

        return {'FINISHED'}


class D2P_OT_BrushPopup(bpy.types.Operator):
    """Brush popup"""
    bl_idname = "view3d.brush_popup"
    bl_label = "Brush Settings"
    COMPAT_ENGINES = {'BLENDER_EEVEE_NEXT', 'CYCLES'}
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        if context.active_object:
            A = context.active_object.type == 'MESH'
            B = context.mode in {'PAINT_TEXTURE', 'PAINT_VERTEX', 'PAINT_WEIGHT'}
            return A and B

    @staticmethod
    def check(self, context):
        return True

    @staticmethod
    def paint_settings(context):
        toolsettings = context.tool_settings

        if context.vertex_paint_object:
            return toolsettings.vertex_paint
        elif context.weight_paint_object:
            return toolsettings.weight_paint
        elif context.image_paint_object:
            if (toolsettings.image_paint and toolsettings.image_paint.detect_data()):
                return toolsettings.image_paint

            return None
        return None

    @staticmethod
    def unified_paint_settings(parent, context):
        ups = context.tool_settings.unified_paint_settings
        parent.label(text="Unified Settings:")
        row = parent.row()
        row.prop(ups, "use_unified_size", text="Size")
        row.prop(ups, "use_unified_strength", text="Strength")
        if context.weight_paint_object:
            parent.prop(ups, "use_unified_weight", text="Weight")
        elif context.vertex_paint_object or context.image_paint_object:
            parent.prop(ups, "use_unified_color", text="Color")
        else:
            parent.prop(ups, "use_unified_color", text="Color")

    @staticmethod
    def prop_unified_size(parent, context, brush, prop_name, icon='NONE', text="", slider=False):
        ups = context.tool_settings.unified_paint_settings
        ptr = ups if ups.use_unified_size else brush
        parent.prop(ptr, prop_name, icon=icon, text=text, slider=slider)

    @staticmethod
    def prop_unified_strength(parent, context, brush, prop_name, icon='NONE', text="", slider=False):
        ups = context.tool_settings.unified_paint_settings
        ptr = ups if ups.use_unified_strength else brush
        parent.prop(ptr, prop_name, icon=icon, text=text, slider=slider)

    @staticmethod
    def prop_unified_weight(parent, context, brush, prop_name, icon='NONE', text="", slider=False):
        ups = context.tool_settings.unified_paint_settings
        ptr = ups if ups.use_unified_weight else brush
        parent.prop(ptr, prop_name, icon=icon, text=text, slider=slider)

    @staticmethod
    def prop_unified_color(parent, context, brush, prop_name, text=""):
        ups = context.tool_settings.unified_paint_settings
        ptr = ups if ups.use_unified_color else brush
        parent.prop(ptr, prop_name, text=text)

    @staticmethod
    def prop_unified_color_picker(parent, context, brush, prop_name, value_slider=True):
        ups = context.tool_settings.unified_paint_settings
        ptr = ups if ups.use_unified_color else brush
        parent.template_color_picker(ptr, prop_name, value_slider=value_slider)

    def brush_texpaint_common(self, layout, context, brush, settings, projpaint=False):
        capabilities = brush.image_paint_capabilities
        col = layout.column()
        row = col.row(align=True)
        row.use_property_split = False
        row.prop(brush, "color_type", expand=True)

        if brush.image_tool in {'DRAW', 'FILL'}:
            if brush.blend not in {'ERASE_ALPHA', 'ADD_ALPHA'}:
                # If the color type is not 'GRADIENT', show the color picker
                if brush.color_type != 'GRADIENT':
                    self.prop_unified_color_picker(col, context, brush, "color", value_slider=True)

                # Show palette if available
                if settings.palette:
                    col.template_palette(settings, "palette", color=True)
                    col.operator(D2P_OT_SetColorFamilies.bl_idname)
                # If the brush uses gradients
                if brush.color_type == 'GRADIENT':
                    col.label(text="Gradient Colors")
                    # Show the gradient color ramp
                    col.template_color_ramp(brush, "gradient", expand=True)
                    col.operator("brush.generate_gradient_from_palette", text="Gradient from Palette")

                    if brush.image_tool != 'FILL':
                        col.label(text="Background Color")
                        row = col.row(align=True)
                        self.prop_unified_color(row, context, brush, "secondary_color", text="")

                    if brush.image_tool == 'DRAW':
                        # Gradient stroke mode options
                        col.prop(brush, "gradient_stroke_mode", text="Mode")
                        if brush.gradient_stroke_mode in {'SPACING_REPEAT', 'SPACING_CLAMP'}:
                            col.prop(brush, "grad_spacing")
                    elif brush.image_tool == 'FILL':
                        col.prop(brush, "gradient_fill_mode")
                else:
                    # For non-gradient brushes, show the primary and secondary color options
                    row = col.row(align=True)
                    self.prop_unified_color(row, context, brush, "color", text="")
                    if brush.image_tool == 'FILL' and not projpaint:
                        col.prop(brush, "fill_threshold")
                    else:
                        self.prop_unified_color(row, context, brush, "secondary_color", text="")
                        row.separator()
                        row.operator("paint.brush_colors_flip", icon='FILE_REFRESH', text="")

        # Additional tool-specific settings
        elif brush.image_tool == 'SOFTEN':
            col = layout.column(align=True)
            col.row().prop(brush, "direction", expand=True)
            col.separator()
            col.prop(brush, "sharp_threshold")
            if not projpaint:
                col.prop(brush, "blur_kernel_radius")
            col.separator()
            col.prop(brush, "blur_mode")

        elif brush.image_tool == 'MASK':
            col.prop(brush, "weight", text="Mask Value", slider=True)

        elif brush.image_tool == 'CLONE':
            col.separator()

            # Handle project paint settings
            if projpaint:
                if settings.mode == 'MATERIAL':
                    col.prop(settings, "use_clone_layer", text="Clone from paint slot")
                elif settings.mode == 'IMAGE':
                    col.prop(settings, "use_clone_layer", text="Clone from image/UV map")

                if settings.use_clone_layer:
                    ob = context.active_object
                    col = layout.column()

                    # Handle MATERIAL mode
                    if settings.mode == 'MATERIAL':
                        if len(ob.material_slots) > 1:
                            col.label(text="Materials")
                            col.template_list("MATERIAL_UL_matslots", "", ob, "material_slots", ob,
                                              "active_material_index", rows=2)

                        mat = ob.active_material
                        if mat:
                            # Display active clone slot
                            col.label(text=f"Active Clone Slot: {mat.paint_clone_slot}")

                            # Display texture paint slots
                            if mat.texture_paint_slots:
                                for i, slot in enumerate(mat.texture_paint_slots):
                                    if slot:
                                        slot_name = slot.name if slot.name else f"Slot {i}"
                                        row = col.row()
                                        row.operator("view3d.set_active_clone_slot", text=slot_name).slot_index = i
                                    else:
                                        col.label(text=f"Slot {i} is empty", icon='ERROR')
                            else:
                                col.label(text="No texture slots available", icon='ERROR')


                    # Handle IMAGE mode
                    elif settings.mode == 'IMAGE':
                        mesh = ob.data
                        clone_text = mesh.uv_texture_clone.name if mesh.uv_texture_clone else ""
                        col.label(text="Source Clone Image")
                        col.template_ID(settings, "clone_image")
                        col.label(text="Source Clone UV Map")
                        col.menu("VIEW3D_MT_tools_projectpaint_clone", text=clone_text, translate=False)

            # Standard clone settings if not using project paint
            else:
                col.prop(brush, "clone_image", text="Image")
                col.prop(brush, "clone_alpha", text="Alpha")

        col.separator()

        if capabilities.has_radius:
            row = col.row(align=True)
            self.prop_unified_size(row, context, brush, "size", slider=True, text="Radius")
            row.prop(brush, "use_pressure_size", text="")

        row = col.row(align=True)
        self.prop_unified_strength(row, context, brush, "strength", text="Strength")
        self.prop_unified_strength(row, context, brush, "use_pressure_strength")

        if brush.image_tool in {'DRAW', 'FILL'}:
            col.separator()
            col.prop(brush, "blend", text="Blend")

        col = layout.column()
        if capabilities.has_accumulate:
            col.prop(brush, "use_accumulate")

        if projpaint:
            col.prop(brush, "use_alpha")

        col.prop(brush, "use_gradient")
        col.separator()
        col.template_ID(settings, "palette", new="palette.new")

    def draw(self, context):
        # Init values
        toolsettings = context.tool_settings
        settings = self.paint_settings(context)

        layout = self.layout
        col = layout.column()

        if not settings:
            row = col.row(align=True)
            row.label(text="Setup texture paint, please!")
        else:
            brush = settings.brush
            ipaint = toolsettings.image_paint

            col = layout.column(align=True)
            row = col.row(align=False)
            row.scale_x = 1.5  # Increase the horizontal scale of the row
            row.scale_y = 1.5  # Increase vertical scale (makes icons appear larger vertically too)

            # Tool buttons with larger icons
            row.operator("wm.tool_set_by_id", text="", icon='BRUSH_TEXDRAW').name = "builtin_brush.Draw"
            row.operator("wm.tool_set_by_id", text="", icon='BRUSH_SOFTEN').name = "builtin_brush.Soften"
            row.operator("wm.tool_set_by_id", text="", icon='BRUSH_SMEAR').name = "builtin_brush.Smear"
            row.operator("wm.tool_set_by_id", text="", icon='BRUSH_CLONE').name = "builtin_brush.Clone"
            row.operator("wm.tool_set_by_id", text="", icon='BRUSH_TEXFILL').name = "builtin_brush.Fill"
            row.operator("wm.tool_set_by_id", text="", icon='BRUSH_TEXMASK').name = "builtin_brush.Mask"

            # imagepaint tool operate  buttons: UILayout.template_ID_preview()
            col = layout.split().column()
            ###################################### ICI PROBLEME d'icones de brosse !
            # bpy.context.tool_settings.image_paint.brush

            col.template_ID_preview(settings, "brush", new="brush.add", rows=1, cols=3)

            ########################################################################

            # Texture Paint Mode #
            if context.image_paint_object and brush:
                self.brush_texpaint_common(layout, context, brush, settings, True)

            ########################################################################
            # Weight Paint Mode #
            elif context.weight_paint_object and brush:

                col = layout.column()

                row = col.row(align=True)
                self.prop_unified_weight(row, context, brush, "weight", slider=True, text="Weight")

                row = col.row(align=True)
                self.prop_unified_size(row, context, brush, "size", slider=True, text="Radius")
                self.prop_unified_size(row, context, brush, "use_pressure_size")

                row = col.row(align=True)
                self.prop_unified_strength(row, context, brush, "strength", text="Strength")
                self.prop_unified_strength(row, context, brush, "use_pressure_strength")
                ####### need work here, Blend mode doesn't draw in popup
                col.prop(brush, "vertex_tool", text="Blend")

                if brush.vertex_tool == 'BLUR':
                    col.prop(brush, "use_accumulate")
                    col.separator()

                col = layout.column()
                col.prop(toolsettings, "use_auto_normalize", text="Auto Normalize")
                col.prop(toolsettings, "use_multipaint", text="Multi-Paint")

            ########################################################################
            # Vertex Paint Mode #
            elif context.vertex_paint_object and brush:
                col = layout.column()
                self.prop_unified_color_picker(col, context, brush, "color", value_slider=True)
                if settings.palette:
                    col.template_palette(settings, "palette", color=True)
                self.prop_unified_color(col, context, brush, "color", text="")

                col.separator()
                row = col.row(align=True)
                self.prop_unified_size(row, context, brush, "size", slider=True, text="Radius")
                self.prop_unified_size(row, context, brush, "use_pressure_size")

                row = col.row(align=True)
                self.prop_unified_strength(row, context, brush, "strength", text="Strength")
                self.prop_unified_strength(row, context, brush, "use_pressure_strength")

                col.separator()
                # col.prop(brush, "vertex_tool", text="Blend")
                col.prop(brush, "blend", text="Blend")

                col.separator()
                col.template_ID(settings, "palette", new="palette.new")

            # Stroke mode
            col.prop(brush, "stroke_method", text="")

            if brush.use_airbrush:
                col.separator()
                col.prop(brush, "rate", text="Rate", slider=True)

            if brush.use_space:
                col.separator()
                row = col.row(align=True)
                row.prop(brush, "spacing", text="Spacing")
                row.prop(brush, "use_pressure_spacing", toggle=True, text="")

            if brush.use_line or brush.use_curve:
                col.separator()
                row = col.row(align=True)
                row.prop(brush, "spacing", text="Spacing")

            if brush.use_curve:
                col.separator()
                col.template_ID(brush, "paint_curve", new="paintcurve.new")
                col.operator("paintcurve.draw")

            else:
                col.separator()

                row = col.row(align=True)
                # row.prop(brush, "use_pressure_jitter", icon_only=True)
                if brush.use_pressure_jitter:
                    row.prop(brush, "jitter", slider=True)
                else:
                    row.prop(brush, "jitter_absolute")
                row.prop(brush, "use_pressure_jitter", toggle=True, text="")

                col = layout.column()
                col.separator()

                if brush.brush_capabilities.has_smooth_stroke:
                    col.prop(brush, "use_smooth_stroke")
                    if brush.use_smooth_stroke:
                        sub = col.column()
                        sub.prop(brush, "smooth_stroke_radius", text="Radius", slider=True)
                        sub.prop(brush, "smooth_stroke_factor", text="Factor", slider=True)

            layout.prop(settings, "input_samples")

            # Curve stroke
            if brush.curve_preset == 'CUSTOM':
                layout.template_curve_mapping(brush, "curve", brush=True)

            col = layout.column(align=True)
            row = col.row(align=True)
            row.operator("brush.curve_preset", icon='SMOOTHCURVE', text="").shape = 'SMOOTH'
            row.operator("brush.curve_preset", icon='SPHERECURVE', text="").shape = 'ROUND'
            row.operator("brush.curve_preset", icon='ROOTCURVE', text="").shape = 'ROOT'
            row.operator("brush.curve_preset", icon='SHARPCURVE', text="").shape = 'SHARP'
            row.operator("brush.curve_preset", icon='LINCURVE', text="").shape = 'LINE'
            row.operator("brush.curve_preset", icon='NOCURVE', text="").shape = 'MAX'

            # Symetries mode
            col = layout.column(align=True)
            row = col.row(align=True)
            obj = bpy.context.active_object

            row.prop(obj, "use_mesh_mirror_x", text="X", toggle=True)
            row.prop(obj, "use_mesh_mirror_y", text="Y", toggle=True)
            row.prop(obj, "use_mesh_mirror_z", text="Z", toggle=True)

    def invoke(self, context, event):
        if context.space_data.type == 'IMAGE_EDITOR':
            context.space_data.mode = 'PAINT'

        return context.window_manager.invoke_props_dialog(self, width=180)

    def execute(self, context):
        return {'FINISHED'}


##################### main popup operator
class D2P_OT_SlotsVGroupsPopup(bpy.types.Operator):
    """Slots ProjectPaint popup"""
    bl_idname = "view3d.projectpaint"
    bl_label = "Slots & VGroups"
    bl_options = {'REGISTER', 'UNDO'}
    ##################################################################
    # Properties to toggle visibility of subsections
    use_basic_settings: bpy.props.BoolProperty(
        name="Show Basic Settings",
        default=True  # Starts as expanded
    )

    use_advanced_settings: bpy.props.BoolProperty(
        name="Show Advanced Settings",
        default=False  # Starts as collapsed
    )

    ####################################################################

    def check(self, context):
        return True

    @classmethod
    def poll(cls, context):
        brush = context.tool_settings.image_paint.brush
        ob = context.active_object
        if brush is not None and ob is not None and ob.type == 'MESH':
            print("Object is a mesh and brush is active")
            if context.space_data.type in {'VIEW_3D', 'IMAGE_EDITOR'}:
                print(f"Space type is {context.space_data.type}")
                return True
        print("poll failed")
        return False

    def draw(self, context):
        settings = context.tool_settings.image_paint
        ob = context.active_object
        layout = self.layout
        col = layout.column()
        box = col.box()
        row = box.row()
        row.prop(self, "use_advanced_settings",
                 text="Face Mask Groups",
                 icon='TRIA_RIGHT' if self.use_basic_settings else 'TRIA_DOWN',
                 emboss=False)

        # row = layout.row()
        # row.label(text="Face Mask Groups")
        if self.use_advanced_settings:
            box = layout.box()  # HORIZONTAL ALIGN
            col = box.column(align=True)
            row = col.row(align=True)
            row1 = row.split(align=True)
            row1.label(text="Generate FMG from Islands")
            row1.operator("d2p.getfacemaskgroups", text="FMG+", icon='SHADERFX')

            # Vertex Paint Section (unchanged)
            group = ob.vertex_groups.active
            rows = 4 if group else 2

            row = layout.row()
            row.template_list("MESH_UL_vgroups", "", ob, "vertex_groups", ob.vertex_groups, "active_index", rows=rows)
            ############borrowed
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

        col = layout.column()

        # Paint Mode Selection
        if context.mode == 'PAINT_TEXTURE':
            col.label(text="Painting Mode")
            col.prop(settings, "mode", text="")
            col.separator()

            if settings.mode == 'MATERIAL':
                # Material Mode Section
                if len(ob.material_slots) > 1:
                    col.label(text="Materials")
                    col.template_list("MATERIAL_UL_matslots", "layers", ob, "material_slots", ob,
                                      "active_material_index", rows=4)

                mat = ob.active_material
                if mat and mat.use_nodes:
                    col.label(text="Available Paint Slots")

                    # Display texture paint slots
                    if mat.texture_paint_slots:
                        for i, slot in enumerate(mat.texture_paint_slots):
                            if slot:
                                slot_name = slot.name if slot.name else f"Slot {i}"
                                row = col.row()
                                row.operator("view3d.set_active_texture_slot", text=slot_name).slot_index = i
                            else:
                                col.label(text=f"Slot {i} is empty", icon='ERROR')
                    else:
                        col.label(text="No texture slots available", icon='ERROR')

                    if ob.data.uv_layers:
                        # col.label(text="UV Map")
                        slot = mat.texture_paint_slots[mat.paint_active_slot] if mat.texture_paint_slots else None
                        if slot:
                            col.prop_search(slot, "uv_layer", ob.data, "uv_layers", text="Select UV Map")
                            col.label(text="Active UV Layer: " + ob.data.uv_layers.active.name)
                        else:
                            col.label(text="No active UV map found", icon='ERROR')
                col.operator("paint.add_texture_paint_slot", text="Add Texture", icon='TEXTURE_DATA')
            elif settings.mode == 'IMAGE':
                # Image Mode Section
                mesh = ob.data
                uv_text = mesh.uv_layers.active.name if mesh.uv_layers.active else ""
                col.label(text="Canvas Image")
                col.template_ID(settings, "canvas")

                col.operator("image.new", text="New Single Image")
                col.label(text="UV Map")
                col.menu("VIEW3D_MT_tools_projectpaint_uvlayer", text=uv_text, translate=False)

            col.separator()

        # Ensure that the button block is drawn **once**, outside the mode checks
        if bpy.context.scene.render.engine in {'CYCLES', 'BLENDER_EEVEE_NEXT'}:
            col.label(text="Save/Reload")
            col.operator("d2p.display_active_slot", text="Slot2Display")
            row = col.row(align=True)
            row.scale_x = 0.50
            row.scale_y = 1.25
            row = row.split(align=True)

            row.operator("d2p.save_current", text="Save")
            row.operator("d2p.reload_saved_state", text="Reload")

            row = col.row(align=True)
            row.scale_x = 0.50
            row.scale_y = 1.25
            row = row.split(align=True)

            row.operator("d2p.save_increm", text="Save +1")
            row.operator("d2p.reload_all", text="Reload ALL")

            col.operator("d2p.save_dirty", text="Save/Pack ALL")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=240)

    def execute(self, context):
        return {'FINISHED'}
class D2P_OT_MakeBrushImageTexture(bpy.types.Operator):
    bl_label = "New Texture from Image"
    bl_idname = "gizmo.image_texture"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self,context):
        tex = bpy.data.textures.new("ImageTexture",'NONE')
        tex.use_nodes = True
        remove = tex.node_tree.nodes[1]
        tex.node_tree.nodes.remove(remove)
        tex.node_tree.nodes.new("TextureNodeImage")
        tex.node_tree.links.new(tex.node_tree.nodes[0].inputs[0],tex.node_tree.nodes[1].outputs[0])
        tex.node_tree.nodes[1].location = [0,50]
        tex.node_tree.nodes[0].location = [200,50]

        i = bpy.data.images.load(self.filepath)
        tex.node_tree.nodes[1].image = i

        if bpy.context.mode == 'PAINT_TEXTURE':
            bpy.context.tool_settings.image_paint.brush.texture = tex
        elif bpy.context.mode == 'PAINT_VERTEX':
            bpy.context.tool_settings.vertex_paint.brush.texture = tex
        elif bpy.context.mode == 'PAINT_WEIGHT':
            bpy.context.tool_settings.weight_paint.brush.texture = tex
        #elif bpy.context.mode == 'SCULPT':
            #bpy.context.tool_settings.sculpt.brush.texture = tex

        return set()


class D2P_OT_MakeBrushImageTextureMask(bpy.types.Operator):
    bl_label = "New Mask Texture from Image"
    bl_idname = "gizmo.image_texture_mask"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self,context):
        tex = bpy.data.textures.new("ImageTextureMask",'NONE')
        tex.use_nodes = True
        remove = tex.node_tree.nodes[1]
        tex.node_tree.nodes.remove(remove)
        tex.node_tree.nodes.new("TextureNodeImage")
        tex.node_tree.nodes.new("TextureNodeRGBToBW")

        tex.node_tree.links.new(tex.node_tree.nodes[0].inputs[0],tex.node_tree.nodes[2].outputs[0])
        tex.node_tree.links.new(tex.node_tree.nodes[2].inputs[0],tex.node_tree.nodes[1].outputs[0])
        tex.node_tree.nodes[1].location = [0,50]
        tex.node_tree.nodes[2].location = [200,50]
        tex.node_tree.nodes[0].location = [400,50]

        i = bpy.data.images.load(self.filepath)
        tex.node_tree.nodes[1].image = i

        if bpy.context.mode == 'PAINT_TEXTURE':
            bpy.context.tool_settings.image_paint.brush.mask_texture = tex
        elif bpy.context.mode == 'PAINT_VERTEX':
            bpy.context.tool_settings.vertex_paint.brush.mask_texture = tex
        elif bpy.context.mode == 'PAINT_WEIGHT':
            bpy.context.tool_settings.weight_paint.brush.mask_texture = tex
        #elif bpy.context.mode == 'SCULPT':
            #bpy.context.tool_settings.sculpt.brush.mask_texture = tex

        return set()

class D2P_OT_ToggleAddMultiply(bpy.types.Operator):
    '''Toggle between Add and Multiply blend modes'''
    bl_idname = "paint.toggle_add_multiply"
    bl_label = "Toggle add/multiply"

    @classmethod
    def poll(cls, context):
        return bpy.ops.paint.image_paint.poll()

    def invoke(self, context, event):
        brush = context.tool_settings.image_paint.brush
        if brush.blend != 'MUL':
            brush.blend = 'MUL'
        else:
            brush.blend = 'ADD'


        return {"FINISHED"}


class D2P_OT_ToggleColorSoftLightScreen(bpy.types.Operator):
    '''Toggle between Color and Softlight and Screen blend modes'''
    bl_idname = "paint.toggle_color_soft_light_screen"
    bl_label = "Toggle color-softlight-screen"

    @classmethod
    def poll(cls, context):
        return bpy.ops.paint.image_paint.poll()

    def invoke(self, context, event):
        brush = context.tool_settings.image_paint.brush
        if brush.blend != 'COLOR' and brush.blend != 'SOFTLIGHT':
            brush.blend = 'COLOR'
        elif brush.blend == 'COLOR':
            brush.blend = 'SOFTLIGHT'
        elif brush.blend == 'SOFTLIGHT':
            brush.blend = 'SCREEN'


        return{'FINISHED'}

class D2P_OT_InitPaintBlend(Operator):
    '''Init to mix paint  mode'''
    bl_idname = "paint.init_blend_mode"
    bl_label = "Init paint blend mode"

    @classmethod
    def poll(cls, context):
        return bpy.ops.paint.image_paint.poll()

    def invoke(self, context, event):
        brush = context.tool_settings.image_paint.brush
        brush.blend = 'MIX'


        return{'FINISHED'}
    
class D2P_OT_ToggleAlphaMode(bpy.types.Operator):
    '''Toggle between Add Alpha and Erase Alpha blend modes'''
    bl_idname = "paint.toggle_alpha_mode"
    bl_label = "Toggle alpha mode"

    @classmethod
    def poll(cls, context):
        return bpy.ops.paint.image_paint.poll()


    def invoke(self, context, event):
        brush = context.tool_settings.image_paint.brush
        if brush.blend != 'ERASE_ALPHA':
            brush.blend = 'ERASE_ALPHA'
        else:
            brush.blend = 'ADD_ALPHA'

        return{'FINISHED'}

class D2P_OT_ModifyBrushTextures(bpy.types.Operator):
    '''Modify Active Brush Textures in new window'''
    bl_label = "Modify active Brush Texture"
    bl_idname = "paint.modify_brush_textures"
    bl_options = {'REGISTER', 'UNDO'}

    toggleType: bpy.props.BoolProperty(default=True)  # toogle texture or Mask menu

    @classmethod
    def poll(cls, context):
        brush = find_brush(context)
        return brush

    def execute(self, context):
        brush = find_brush(context)
        name_tex = brush.texture_slot.name
        name_mask = brush.mask_texture_slot.name


        if brush:
            # Get the brush Texture
            j = -1
            tux  = name_tex if self.toggleType else  name_mask
            for i in range(len(bpy.data.textures)):
                 if bpy.data.textures[i].name == tux:
                    j = i

            # Call user prefs window
            bpy.ops.screen.userpref_show('INVOKE_DEFAULT')
            area = context.window_manager.windows[-1].screen.areas[0]
            area.type = 'IMAGE_EDITOR'
            if j != -1:
                context.area.spaces.active.image = bpy.data.images[j]
            context.space_data.mode = 'PAINT'
        else:
            self.report({'INFO'}, "No selected texture")
        return {'FINISHED'}

## NEED TO ADD OPERATORS FOR IMAGE RESIZER HERE
class IMAGE_RESIZE_OT_width_mul2(bpy.types.Operator):
    bl_idname = "image.resize_ex_width_mul2"
    bl_label = "*2"
    bl_description = "*2"

    shift_key_down = False

    @classmethod
    def poll(cls, context):
        return hasattr(context.space_data, "image") and context.space_data.image is not None

    def invoke(self, context, event):
        self.shift_key_down = event.shift
        return self.execute(context)

    def execute(self, context):
        scene = context.scene
        if self.shift_key_down:
            scene.image_resize_addon_width = next_power_of_2(scene.image_resize_addon_width)
        else:
            scene.image_resize_addon_width = scene.image_resize_addon_width * 2
        return {"FINISHED"}

class IMAGE_RESIZE_OT_height_mul2(bpy.types.Operator):
    bl_idname = "image.resize_ex_height_mul2"
    bl_label = "*2"
    bl_description = "*2"

    shift_key_down = False

    @classmethod
    def poll(cls, context):
        return hasattr(context.space_data, "image") and context.space_data.image is not None

    def invoke(self, context, event):
        self.shift_key_down = event.shift
        return self.execute(context)

    def execute(self, context):
        scene = context.scene
        if self.shift_key_down:
            scene.image_resize_addon_height = next_power_of_2(scene.image_resize_addon_height)
        else:
            scene.image_resize_addon_height = scene.image_resize_addon_height * 2
        return {"FINISHED"}

class IMAGE_RESIZE_OT_width_div2(bpy.types.Operator):
    bl_idname = "image.resize_ex_width_div2"
    bl_label = "/2"
    bl_description = "/2"

    shift_key_down = False

    @classmethod
    def poll(cls, context):
        return hasattr(context.space_data, "image") and context.space_data.image is not None

    def invoke(self, context, event):
        self.shift_key_down = event.shift
        return self.execute(context)

    def execute(self, context):
        scene = context.scene
        if self.shift_key_down:
            scene.image_resize_addon_width = previous_power_of_2(scene.image_resize_addon_width)
        else:
            scene.image_resize_addon_width = scene.image_resize_addon_width // 2
        return {"FINISHED"}

class IMAGE_RESIZE_OT_height_div2(bpy.types.Operator):
    bl_idname = "image.resize_ex_height_div2"
    bl_label = "/2"
    bl_description = "/2"

    shift_key_down = False

    @classmethod
    def poll(cls, context):
        return hasattr(context.space_data, "image") and context.space_data.image is not None

    def invoke(self, context, event):
        self.shift_key_down = event.shift
        return self.execute(context)

    def execute(self, context):
        scene = context.scene
        if self.shift_key_down:
            scene.image_resize_addon_height = previous_power_of_2(scene.image_resize_addon_height)
        else:
            scene.image_resize_addon_height = scene.image_resize_addon_height // 2
        return {"FINISHED"}

class IMAGE_RESIZE_OT_getcurrentsize(bpy.types.Operator):
    bl_idname = "image.resize_ex_getcurrentsize"
    bl_label = "Get Current Size"
    bl_description = "Get Current Size"

    @classmethod
    def poll(cls, context):
        return hasattr(context.space_data, "image") and context.space_data.image is not None

    def execute(self, context):
        scene = context.scene
        image = context.space_data.image
        scene.image_resize_addon_width, scene.image_resize_addon_height = image.size
        return {"FINISHED"}

class IMAGE_RESIZE_OT_scale_percentage(bpy.types.Operator):
    bl_idname = "image.resize_ex_scale_percentage"
    bl_label = "Scale by Percentage"
    bl_description = "Scale Width and Height by Percentage"

    @classmethod
    def poll(cls, context):
        return hasattr(context.space_data, "image") and context.space_data.image is not None

    def execute(self, context):
        scene = context.scene
        percentage = scene.image_resize_addon_percentage / 100.0
        scene.image_resize_addon_width = int(scene.image_resize_addon_width * percentage)
        scene.image_resize_addon_height = int(scene.image_resize_addon_height * percentage)
        return {"FINISHED"}

class IMAGE_RESIZE_OT_main(bpy.types.Operator):
    bl_idname = "image.resize_ex_main"
    bl_label = "Resize Image"
    bl_description = "Resize Image"

    shift_key_down = False

    @classmethod
    def poll(cls, context):
        return hasattr(context.space_data, "image") and context.space_data.image is not None

    def execute(self, context):
        scene = context.scene
        image = context.space_data.image
        if self.shift_key_down:
            image.reload()
        width, height = scene.image_resize_addon_width, scene.image_resize_addon_height
        image.scale(width, height)
        bpy.ops.image.resize()
        return {"FINISHED"}

    def invoke(self, context, event):
        self.shift_key_down = event.shift
        return self.execute(context)

### Color Families Palette Generator
class D2P_OT_SetColorFamilies(bpy.types.Operator):
    """Set Complementary Brush Color and Create Color Palettes"""
    bl_idname = "object.set_complementary_brush_color"
    bl_label = "Generate Color Families"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Access the active brush depending on the current mode
        settings = bpy.context.tool_settings

        if context.mode == 'PAINT_TEXTURE':
            brush = settings.image_paint.brush
        elif context.mode == 'PAINT_VERTEX':
            brush = settings.vertex_paint.brush
        elif context.mode == 'PAINT_WEIGHT':
            brush = settings.weight_paint.brush
        else:
            self.report({'WARNING'}, "Active mode does not support brush color")
            return {'CANCELLED'}

        # Get the current brush color
        primary_color = brush.color
        primary_color_hex = rgb_to_hex(primary_color)

        # Calculate the complementary color
        comp_color = complementary_color(primary_color)

        # Set the complementary color as the secondary color
        brush.secondary_color = comp_color

        # Set the brush name to the primary color hex code
        brush.name = f"Brush Color {primary_color_hex}"

        # Calculate split complementary, triadic, tetradic, and analogous colors
        split_comps = split_complementary_colors(primary_color)
        triads = triadic_colors(primary_color)
        tetrads = tetradic_colors(primary_color)
        analogous = analogous_colors(primary_color)

        # Create color palettes
        create_palette(f"Complementary Colors {primary_color_hex}", [primary_color, comp_color])
        create_palette(f"Split Complementary Colors {primary_color_hex}", [primary_color] + list(split_comps))
        create_palette(f"Triadic Colors {primary_color_hex}", [primary_color] + list(triads))
        create_palette(f"Tetradic Colors {primary_color_hex}", [primary_color] + list(tetrads))
        create_palette(f"Analogous Colors {primary_color_hex}", [primary_color] + list(analogous))

        self.report({'INFO'}, "Brush Colors and Palettes Set")
        return {'FINISHED'}

####nodes selected to compositor and back as one node
class NODE_OT_flatten_images(bpy.types.Operator):
    bl_idname = "node.flatten_images"
    bl_label = "Flatten Images"
    bl_description = "Flatten selected image nodes using a mix node and create a composite image"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Ensure we are in the Shader Editor
        if context.area.type != 'NODE_EDITOR' or context.space_data.tree_type != 'ShaderNodeTree':
            self.report({'ERROR'}, "This operator must be run in the Shader Editor")
            return {'CANCELLED'}

        obj = context.active_object
        if not obj:
            self.report({'ERROR'}, "No active object")
            return {'CANCELLED'}

        material = obj.active_material
        if not material:
            self.report({'ERROR'}, "Active object has no active material")
            return {'CANCELLED'}

        if not material.use_nodes:
            self.report({'ERROR'}, "Active material does not use nodes")
            return {'CANCELLED'}

        node_tree = material.node_tree
        nodes = node_tree.nodes

        # Get selected nodes from the node tree
        selected_nodes = [node for node in nodes if node.select]

        # Debug print to verify selected nodes
        print("Selected nodes:", [(node.name, node.type) for node in selected_nodes])

        image_nodes = [node for node in selected_nodes if node.type == 'TEX_IMAGE']
        mix_nodes = [node for node in selected_nodes if node.type == 'MIX']

        # Debug print to verify filtered nodes
        print("Selected image nodes:", [node.name for node in image_nodes])
        print("Selected mix nodes:", [node.name for node in mix_nodes])

        # Debug print the actual types of all selected nodes to diagnose the issue
        for node in selected_nodes:
            print(f"Node {node.name} has type {node.type}")

        if len(image_nodes) != 2 or len(mix_nodes) != 1:
            self.report({'ERROR'}, "Select exactly two image nodes and one mix node")
            return {'CANCELLED'}

        image_node1, image_node2 = image_nodes
        mix_node = mix_nodes[0]

        blend_mode = mix_node.blend_type

        image1 = image_node1.image
        image2 = image_node2.image

        if not image1.has_data or not image2.has_data:
            self.report({'ERROR'}, "One or both images are not loaded")
            return {'CANCELLED'}

        width1, height1 = image1.size
        width2, height2 = image2.size

        if (width1, height1) != (width2, height2):
            self.report({'ERROR'}, "Images must be the same size")
            return {'CANCELLED'}

        render_width, render_height = width1, height1
        create_compositor_node_tree(image1, image2, blend_mode)
        combined_image = render_and_extract_image("CombinedImage", render_width, render_height)

        bpy.context.area.ui_type = 'ShaderNodeTree'

        # Create a group from the selected nodes
        bpy.ops.node.group_make()

        # Find the newly created group node
        group_node = None
        for node in nodes:
            if node.type == 'GROUP' and node.name not in [n.name for n in selected_nodes]:
                group_node = node
                break

        if group_node:
            group_node.label = "Flatten Input"

        # Add the new image texture node
        new_image_node = nodes.new('ShaderNodeTexImage')
        new_image_node.image = combined_image
        new_image_node.label = "Flatten result"
        new_image_node.location = group_node.location.x + 300, group_node.location.y

        return {'FINISHED'}

#flip gradient direction
class D2P_OT_flip_gradient(bpy.types.Operator):
    bl_idname = "brush.flip_gradient"
    bl_label = "Flip Brush Gradient"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        brush = self.get_active_brush(context)
        if not brush:
            self.report({'WARNING'}, "No active brush found.")
            return {'CANCELLED'}

        if not hasattr(brush, "gradient") or brush.gradient is None:
            self.report({'WARNING'}, "The active brush does not use a gradient.")
            return {'CANCELLED'}

        self.flip_color_ramp(brush.gradient)

        return {'FINISHED'}

    def get_active_brush(self, context):
        tool_settings = context.tool_settings

        if context.sculpt_object:
            return tool_settings.sculpt.brush
        elif context.vertex_paint_object:
            return tool_settings.vertex_paint.brush
        elif context.weight_paint_object:
            return tool_settings.weight_paint.brush
        elif context.image_paint_object:
            return tool_settings.image_paint.brush
        else:
            return None

    def flip_color_ramp(self, color_ramp):
        elements = color_ramp.elements
        n = len(elements)

        # Create lists to hold the positions and colors temporarily
        positions = [e.position for e in elements]
        colors = [e.color[:] for e in elements]  # Use slicing to copy the color values

        for i in range(n):
            elements[i].position = 1.0 - positions[n - 1 - i]
            elements[i].color = colors[n - 1 - i]


class D2P_OT_CalculateTexelDensity(Operator):
    """Selected Object is Examined for Surface Area and Suggests Power of 2 Texture Size"""
    bl_idname = "object.calculate_texel_density"
    bl_label = "Calculate Texel Density"

    result: bpy.props.StringProperty(name="Result", default="")

    def execute(self, context):
        obj = context.active_object

        # Ensure object has valid data
        if not obj or obj.type != 'MESH':
            self.result = "Please select a valid mesh object."
            return {'FINISHED'}

        # Desired texel density (texels per meter)
        desired_texel_density = 1024  # Modify this value as needed

        # Calculate ideal texture size
        texture_size = calculate_texel_density(obj, desired_texel_density)

        self.result = f"Suggested Texture Size: {texture_size}x{texture_size}"

        # Store the result in the context scene to display in the panel
        context.scene.texel_density_result = self.result

        return {'FINISHED'}

### Viewer Node to Shader Node and Shader Node to Viewer Node experiments here
class D2P_OT_Shader2ViewerNode(bpy.types.Operator):
    bl_idname = "viewer.shader2viewer"
    bl_label = "Shader to Viewer"
    bl_description = "Copy the active image node from the shader to a new image node connected to the Viewer Node in the compositor"

    def execute(self, context):
        obj = context.active_object

        # Ensure an object is selected and it has a material
        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, "No active mesh object found")
            return {'CANCELLED'}

        mat = obj.active_material
        if mat is None or not mat.use_nodes:
            self.report({'ERROR'}, "No active material with nodes found")
            return {'CANCELLED'}

        # Find the active image texture node
        shader_tree = mat.node_tree
        active_node = shader_tree.nodes.active

        if not isinstance(active_node, bpy.types.ShaderNodeTexImage):
            self.report({'ERROR'}, "Active node is not an image texture node")
            return {'CANCELLED'}

        image = active_node.image
        if image is None:
            self.report({'ERROR'}, "No image found in the active image texture node")
            return {'CANCELLED'}

        # Ensure the compositor is enabled
        scene = context.scene
        if not scene.use_nodes:
            scene.use_nodes = True

        comp_node_tree = scene.node_tree

        # Check if there is already a Viewer Node, if not create one
        viewer_node = None
        for node in comp_node_tree.nodes:
            if node.type == 'VIEWER':
                viewer_node = node
                break

        if viewer_node is None:
            viewer_node = comp_node_tree.nodes.new(type='CompositorNodeViewer')
            viewer_node.location = (300, 200)

        # Create a new Image node and set the image
        image_node = comp_node_tree.nodes.new(type='CompositorNodeImage')
        image_node.image = image
        image_node.location = (100, 200)

        # Connect the image node to the Viewer Node
        comp_node_tree.links.new(image_node.outputs['Image'], viewer_node.inputs['Image'])
        
        # Turn on Backdrop for Viewer Node
        bpy.context.space_data.show_backdrop = True

        self.report({'INFO'}, f"Image '{image.name}' copied to a new viewer node in the compositor")
        return {'FINISHED'}


class D2P_OT_Viewer2Image(bpy.types.Operator):
    bl_idname = "viewer.viewer2image"
    bl_label = "Save Viewer Image"
    bl_description = "Save the Viewer Node result to a unique image file and update the shader tree if necessary"

    def execute(self, context):
        # Ensure the context is correct
        if not context.scene.use_nodes:
            self.report({'ERROR'}, "Compositing nodes are not enabled")
            return {'CANCELLED'}

        node_tree = context.scene.node_tree
        viewer_node = None
        base_image_name = "viewer_image"
        group_node_name = ""

        # Find the Viewer Node
        for node in node_tree.nodes:
            if node.type == 'VIEWER':
                viewer_node = node
                break

        if not viewer_node:
            self.report({'ERROR'}, "No Viewer Node found in the Compositor")
            return {'CANCELLED'}

        # Helper function to trace back and get the base image name and connected group node name
        def get_image_and_group_name_from_node(node):
            base_name = None
            group_name = None
            if node.type == 'IMAGE' and node.image:
                base_name = bpy.path.clean_name(node.image.name)  # Base image name
            if node.type == 'GROUP':
                group_name = bpy.path.clean_name(node.name)  # Group node name
            if node.type == 'RENDER_LAYERS':
                base_name = "render_layer"
            for input_socket in node.inputs:
                if input_socket.is_linked:
                    linked_node = input_socket.links[0].from_node
                    linked_base_name, linked_group_name = get_image_and_group_name_from_node(linked_node)
                    if linked_base_name:
                        base_name = linked_base_name
                    if linked_group_name:
                        group_name = linked_group_name
            return base_name, group_name

        # Trace the inputs to find base image name and group node name
        base_image_name, group_node_name = get_image_and_group_name_from_node(viewer_node)

        if not base_image_name:
            base_image_name = "viewer_image"  # Fallback if no image source is found

        if group_node_name:
            # Append the Group Node name to the base image name
            image_name = f"{base_image_name}_{group_node_name}_Process"
        else:
            image_name = base_image_name  # Fallback to just the base image name if no Group Node is found

        # Ensure that Viewer Node has a valid image buffer
        if not bpy.data.images.get('Viewer Node'):
            self.report({'ERROR'}, "Viewer Node has no image data available")
            return {'CANCELLED'}

        viewer_image = bpy.data.images['Viewer Node']

        # Explicitly set the directory to C:\tmp\
        temp_dir = "C:\\tmp\\"

        # Ensure the temp directory exists
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        # Generate a unique filename based on the number of existing files
        existing_files = [f for f in os.listdir(temp_dir) if f.startswith(image_name) and f.endswith('.png')]
        iteration = len(existing_files) + 1
        image_filename = f"{image_name}_{iteration:03d}.png"
        temp_filepath = os.path.join(temp_dir, image_filename)

        # Save the image to the unique file
        viewer_image.save_render(temp_filepath)

        # Load the unique image into Blender
        image = bpy.data.images.load(temp_filepath)

        # Add or update the image in the active object's shader tree
        obj = context.active_object
        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, "No active mesh object found")
            return {'CANCELLED'}

        mat = obj.active_material
        if mat is None:
            mat = bpy.data.materials.new(name="Material")
            obj.data.materials.append(mat)

        if mat.use_nodes is False:
            mat.use_nodes = True

        # Get the material's node tree
        shader_tree = mat.node_tree

        # Check if an Image Texture node with the corresponding name already exists
        target_node_name = f"{image_name}_viewer_image"
        image_node = None

        for node in shader_tree.nodes:
            if isinstance(node, bpy.types.ShaderNodeTexImage) and node.name.startswith(target_node_name):
                image_node = node
                break

        if image_node:
            # If it exists, update the image data in the existing node
            image_node.image = image
            self.report({'INFO'}, f"Viewer image '{image_filename}' updated in existing shader node '{image_node.name}'")
        else:
            # If it doesn't exist, create a new Image Texture node
            image_node = shader_tree.nodes.new(type='ShaderNodeTexImage')
            image_node.image = image
            image_node.name = target_node_name
            image_node.label = target_node_name
            image_node.location = (0, 0)
            self.report({'INFO'}, f"Viewer image '{image_filename}' saved and added as new node in active object shader")

        return {'FINISHED'}


class D2P_OT_EditorSwap(bpy.types.Operator):
    """Toggle Shader and Compositor Editor"""
    bl_idname = "d2p.editor_swap"
    bl_label = "Editor Swap Compositor and Shader"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        area = bpy.context.area

        if area.ui_type != 'ShaderNodeTree':
            area.ui_type = 'ShaderNodeTree'
        else:
            area.ui_type = 'CompositorNodeTree'
            # add a way to make sure the backdrop is on, might be here or in shader2viewernode
            #bpy.context.space_data.show_backdrop = True


        # toggle node editor for compositor and shader windows

        return {'FINISHED'}