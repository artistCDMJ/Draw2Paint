import os
import bpy


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
                    )

from bpy.types import Operator, Menu, Panel, UIList
from bpy_extras.io_utils import ImportHelper

# Define your operators here

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


class D2P_OT_SelectedToUVMask(bpy.types.Operator):
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

class D2P_OT_CanvasAndCamera(bpy.types.Operator):
    """Create Canvas and Camera from Active Image"""
    bl_description = "Create Canvas and Camera from Active Image"
    bl_idname = "object.canvas_and_camera"
    bl_label = "Generate Image Plane and Matching Camera"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        # Check if 'subject_view' collection exists
        return 'canvas_view' not in bpy.data.collections

    def execute(self, context):
        active_image = None
        for area in bpy.context.screen.areas:
            if area.type == 'IMAGE_EDITOR':
                active_image = area.spaces.active.image
                break

        if not active_image:
            self.report({'WARNING'}, "No active image found.")
            return {'CANCELLED'}
        

        image_name = active_image.name
        image_plane_obj, width, height = create_image_plane_from_image(active_image)
        if not image_plane_obj:
            self.report({'WARNING'}, "Failed to create image plane.")
            return {'CANCELLED'}
        
        camera_obj = create_matching_camera(image_plane_obj, width, height)
        camera_obj.data.show_name = True
        
        switch_to_camera_view(camera_obj)
        
        # Move camera and image plane to 'canvas_view' collection
        move_object_to_collection(image_plane_obj, 'canvas_view')
        move_object_to_collection(camera_obj, 'canvas_view')
        
        bpy.context.space_data.shading.type = 'SOLID'
        bpy.context.space_data.shading.light = 'FLAT'
        bpy.context.space_data.shading.color_type = 'TEXTURE'

        return {'FINISHED'}

class D2P_OT_CameraFromCanvas(bpy.types.Operator):
    """New Camera from Selected Canvas"""
    bl_description = "New Camera from Selected Canvas"
    bl_idname = "object.create_camera_from_selected_image_plane"
    bl_label = "Create Camera from Selected Image Plane"
    bl_options = {'REGISTER', 'UNDO'}
    
    
    @classmethod
    def poll(cls, context):
        # Check if 'subject_view' collection exists
        return 'subject_view' not in bpy.data.collections
    
    
    def execute(self, context):
        selected_objects = context.selected_objects
        if not selected_objects:
            self.report({'WARNING'}, "No selected objects found.")
            return {'CANCELLED'}
        
        selected_object = selected_objects[0]
        active_image = get_image_from_selected_object(selected_object)
        if not active_image:
            self.report({'WARNING'}, "Selected object has no image texture.")
            return {'CANCELLED'}
        
        image_plane_obj = selected_objects[0]
        width = (image_plane_obj.dimensions.x) * 5
        height = (image_plane_obj.dimensions.y) * 5
        
        camera_obj = create_matching_camera(image_plane_obj, width, height)
        camera_obj.data.show_name = True
        switch_to_camera_view(camera_obj)
        
        # Move camera and image plane to 'canvas_view' collection
        move_object_to_collection(image_plane_obj, 'canvas_view')
        move_object_to_collection(camera_obj, 'canvas_view')
        
        bpy.context.space_data.shading.type = 'SOLID'
        bpy.context.space_data.shading.color_type = 'TEXTURE'
        return {'FINISHED'}

class D2P_OT_SelectedToCanvasAndCamera(bpy.types.Operator):
    """New Canvas and Camera from Selected Subject"""
    bl_description = "New Canvas and Camera from Selected Subject"
    bl_idname = "object.canvas_and_camera_from_selected_object"
    bl_label = "Generate Image Plane and Camera from Selected Object"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        # Check if 'subject_view' collection exists
        return 'subject_view' and 'canvas_view' not in bpy.data.collections
    
    
    def execute(self, context):
        selected_objects = context.selected_objects
        if not selected_objects:
            self.report({'WARNING'}, "No selected objects found.")
            return {'CANCELLED'}

        selected_object = selected_objects[0]
        
        if not selected_object.data.uv_layers:
            self.report({'WARNING'}, "Please Create UV Layer")
            return {'CANCELLED'}
        
        # Move object to 'subject_view' collection
        move_object_to_collection(selected_object, 'subject_view')

        # Export UV layout
        uv_filepath = os.path.join("C:/tmp", selected_object.name + ".png")
        export_uv_layout(selected_object, uv_filepath)

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
        return {'FINISHED'}

class D2P_OT_ImageEditorToCanvasAndCamera(bpy.types.Operator):
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
        bpy.context.area.ui_type = 'VIEW_3D'
        

        #image_name = active_image.name
        image_plane_obj, width, height = create_image_plane_from_image(active_image)
        if not image_plane_obj:
            self.report({'WARNING'}, "Failed to create image plane.")
            return {'CANCELLED'}
        
        camera_obj = create_matching_camera(image_plane_obj, width, height)
        bpy.context.view_layer.objects.active = camera_obj
                
        camera_obj.data.show_name = True
        bpy.context.space_data.shading.type = 'SOLID'
        bpy.context.space_data.shading.light = 'FLAT'
        bpy.context.space_data.shading.color_type = 'TEXTURE'
        if area.type == 'VIEW3D' :
            #Blender refuses to switch to camera view here        
            switch_to_camera_view(camera_obj)
            
        # Move camera and image plane to 'canvas_view' collection
        move_object_to_collection(image_plane_obj, 'canvas_view')
        move_object_to_collection(camera_obj, 'canvas_view')
        
        
        bpy.context.area.ui_type = 'IMAGE_EDITOR'

        return {'FINISHED'}    
    
class D2P_OT_ToggleUVInCamera(bpy.types.Operator):
    """Toggle UV Image Visibility in Camera"""
    bl_description = "Toggle UV Image Visibility in Camera"
    bl_idname = "object.toggle_uv_image_visibility"
    bl_label = "Toggle UV Image Visibility in Camera"
    bl_options = {'REGISTER', 'UNDO'}

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
                #bpy.context.space_data.shading.light = 'FLAT'
                
            else:
                subject_view.hide_viewport = True
                subject_view.hide_render = True
                canvas_view.hide_viewport = False
                canvas_view.hide_render = False
                # Switch to camera view
                switch_to_camera_view(context.scene.camera)
                bpy.context.space_data.shading.type = 'SOLID'
                bpy.context.space_data.shading.light = 'FLAT'

            
            # Update the view layer to reflect visibility changes
            bpy.context.view_layer.update()
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "One or both collections not found.")
            return {'CANCELLED'}


class D2P_OT_D2PaintScene(bpy.types.Operator):
    """Create Draw2Paint Scene"""
    bl_description = "Create Scene for Working in Draw2Paint"
    bl_idname = "d2p.create_d2p_scene"
    bl_label = "Create Scene for Draw2Paint"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        for sc in bpy.data.scenes:
            if sc.name == "Draw2Paint":
                return False
        return context.area.type == 'VIEW_3D'

    def execute(self, context):
        _name = "Draw2Paint"
        for sc in bpy.data.scenes:
            if sc.name == _name:
                return {'FINISHED'}

        bpy.ops.scene.new(type='NEW')
        context.scene.name = _name

        # Set to top view
        bpy.ops.view3d.view_axis(type='TOP', align_active=True)

        # Set the render engine based on Blender version
        if bpy.app.version >= (4, 2, 0):
            context.scene.render.engine = 'BLENDER_EEVEE_NEXT'
        else:
            context.scene.render.engine = 'BLENDER_EEVEE'

        paint_view_color_management_settings()

        return {'FINISHED'}

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
        # output = mask.node_tree.nodes.get('ShaderNodeOutputMaterial')
        material_output = bpy.context.active_object.active_material.node_tree.\
                                                nodes.get('Material Output')

        # Principled Main Shader in Tree
        principled_node = mask.node_tree.nodes.get('Principled BSDF')
        mask.node_tree.nodes.remove(principled_node)

        ###Tex Coordinate Node
        hold = mask.node_tree.nodes.new('ShaderNodeHoldout')
        hold.location = (-100, 0)
        hold.label = ("Holdout Mask")

        # output = mask.node_tree.nodes.new('ShaderNodeOutputMaterial')
        # newout = mask.node_tree.nodes.new('ShaderNodeOutputMaterial')

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
    
class D2P_OT_SculptDuplicate(bpy.types.Operator):
    """Duplicate Selected Image Plane, Single User for Eraser Paint"""
    bl_idname = "d2p.sculpt_duplicate"
    bl_label = "Sculpt Liquid Duplicate"
    bl_options = {'REGISTER', 'UNDO'}

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

class D2P_OT_SculptLiquid(bpy.types.Operator):
    """Convert to Subdivided Plane & Sculpt Liquid"""
    bl_idname = "d2p.sculpt_liquid"
    bl_label = "Sculpt like Liquid"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        # main_canvas = obj.name

        if obj is not None:
            A = context.active_object.type == 'MESH'
            # B = context.active_object.name == obj.name[0]+ '.001'
            return A  # and B

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

class D2P_OT_CanvasHoriz(bpy.types.Operator):
    """Flip the Canvas Left/Right"""
    bl_idname = "d2p.canvas_horizontal"
    bl_label = "Canvas Horizontal"
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

class D2P_OT_CanvasVertical(bpy.types.Operator):
    """Flip the Canvas Top/Bottom"""
    bl_idname = "d2p.canvas_vertical"
    bl_label = "Canvas Vertical"
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

class D2P_OT_CanvasResetrot(bpy.types.Operator):
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

class D2P_OT_NewImage(bpy.types.Operator):
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

class D2P_OT_SaveImage(bpy.types.Operator):
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

class D2P_OT_SaveIncrem(bpy.types.Operator):
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

class D2P_OT_SaveDirty(bpy.types.Operator):
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
        for image in bpy.data.images:
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

class D2P_OT_ImageReload(bpy.types.Operator):
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
        original_type = context.area.ui_type
        context.area.ui_type = 'IMAGE_EDITOR'

        #obdat = context.active_object.data
        #ima = obdat.materials[0].texture_paint_images[0]
        mat = bpy.context.object.active_material
        image = mat.texture_paint_images[mat.paint_active_slot]
        context.space_data.image = image
        bpy.ops.image.reload()  # return image to last saved state

        context.area.ui_type = original_type
        return {'FINISHED'}

class D2P_OT_EmptyGuides(bpy.types.Operator):
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


class D2P_OT_center_object(bpy.types.Operator):
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

class D2P_OT_FrontOfPaint(bpy.types.Operator):
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
            add_child_constraint(new_obj)
            bpy.ops.object.editmode_toggle()
            bpy.ops.curve.delete(type='VERT')
            bpy.ops.object.editmode_toggle()
            copy_material_to_new_object(new_obj)
            new_obj.data.dimensions = '2D'
            new_obj.data.fill_mode = 'BOTH'
            bpy.ops.wm.tool_set_by_id(name="builtin.draw")

        elif mytool.my_enum == 'OP2':
            # Add a new bezier curve and set handle type to VECTOR
            bpy.ops.curve.primitive_bezier_curve_add(enter_editmode=True, align='WORLD', location=(0, 0, 0.15), scale=(1, 1, 1))
            new_obj = bpy.context.object
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
                # bpy.ops.mesh.select_linked(delimit={'SEAM'})
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

class D2P_OT_NewGpencil(bpy.types.Operator):
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
        bpy.ops.object.gpencil_add(align='WORLD', location=(0, 0, 0), scale=(1, 1, 1), type='EMPTY')
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

class D2P_OT_DisplayActivePaintSlot(bpy.types.Operator):
    '''Display selected paint slot in new window'''
    bl_label = "Display active Slot"
    bl_idname = "d2p.display_active_slot"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        return context.object.active_material.texture_paint_images

    def execute(self, context):
        if context.object.active_material.texture_paint_images:
            # Get the Image
            mat = bpy.context.object.active_material
            image = mat.texture_paint_images[mat.paint_active_slot]
            # Call user prefs window
            #bpy.ops.screen.userpref_show('INVOKE_DEFAULT')
            bpy.ops.wm.window_new()
            # Change area type
            area = context.window_manager.windows[-1].screen.areas[0]
            area.type = 'IMAGE_EDITOR'
            # Assign the Image
            context.area.spaces.active.image = image
            context.space_data.mode = 'PAINT'
        else:
            self.report({'INFO'}, "No active Slot")
        return {'FINISHED'}

########################################
#EZPaint Adopted Testing   needs work
########################################

class  D2P_OT_BrushPopup(bpy.types.Operator):
    """Brush popup"""
    bl_idname = "view3d.brush_popup"
    bl_label = "Brush settings"
    COMPAT_ENGINES = {'EEVEE', 'CYCLES'}
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        if context.active_object:
            A = context.active_object.type == 'MESH'
            B = context.mode in {'PAINT_TEXTURE','PAINT_VERTEX','PAINT_WEIGHT'}
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

        if brush.image_tool in {'DRAW', 'FILL'}:
            if brush.blend not in {'ERASE_ALPHA', 'ADD_ALPHA'}:
                if not brush.color_type == 'GRADIENT':
                    self.prop_unified_color_picker(col, context, brush, "color", value_slider=True)

                if settings.palette:
                    col.template_palette(settings, "palette", color=True)

                if brush.color_type =='GRADIENT':
                    col.label("Gradient Colors")
                    col.template_color_ramp(brush, "gradient", expand=True)

                    if brush.image_tool != 'FILL':
                        col.label("Background Color")
                        row = col.row(align=True)
                        self.prop_unified_color(row, context, brush, "secondary_color", text="")

                    if brush.image_tool == 'DRAW':
                        col.prop(brush, "gradient_stroke_mode", text="Mode")
                        if brush.gradient_stroke_mode in {'SPACING_REPEAT', 'SPACING_CLAMP'}:
                            col.prop(brush, "grad_spacing")
                    elif brush.image_tool == 'FILL':
                        col.prop(brush, "gradient_fill_mode")
                else:
                    row = col.row(align=True)
                    self.prop_unified_color(row, context, brush, "color", text="")
                    if brush.image_tool == 'FILL' and not projpaint:
                        col.prop(brush, "fill_threshold")
                    else:
                        self.prop_unified_color(row, context, brush, "secondary_color", text="")
                        row.separator()
                        row.operator("paint.brush_colors_flip", icon='FILE_REFRESH', text="")

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
            if projpaint:
                if settings.mode == 'MATERIAL':
                    col.prop(settings, "use_clone_layer", text="Clone from paint slot")
                elif settings.mode == 'IMAGE':
                    col.prop(settings, "use_clone_layer", text="Clone from image/UV map")

                if settings.use_clone_layer:
                    ob = context.active_object
                    col = layout.column()

                    if settings.mode == 'MATERIAL':
                        if len(ob.material_slots) > 1:
                            col.label("Materials")
                            col.template_list("MATERIAL_UL_matslots", "",
                                              ob, "material_slots",
                                              ob, "active_material_index", rows=2)

                        mat = ob.active_material
                        if mat:
                            col.label("Source Clone Slot")
                            col.template_list("TEXTURE_UL_texpaintslots", "",
                                              mat, "texture_paint_images",
                                              mat, "paint_clone_slot", rows=2)

                    elif settings.mode == 'IMAGE':
                        mesh = ob.data

                        clone_text = mesh.uv_texture_clone.name if mesh.uv_texture_clone else ""
                        col.label("Source Clone Image")
                        col.template_ID(settings, "clone_image")
                        col.label("Source Clone UV Map")
                        col.menu("VIEW3D_MT_tools_projectpaint_clone", text=clone_text, translate=False)
            else:
                col.prop(brush, "clone_image", text="Image")
                col.prop(brush, "clone_alpha", text="Alpha")

        col.separator()

        if capabilities.has_radius:
            row = col.row(align=True)
            self.prop_unified_size(row, context, brush, "size", slider=True, text="Radius")
            self.prop_unified_size(row, context, brush, "use_pressure_size")

        row = col.row(align=True)

        #if capabilities.has_space_attenuation:
            #row.prop(brush, "use_space_attenuation", toggle=True, icon_only=True)

        self.prop_unified_strength(row, context, brush, "strength", text="Strength")
        self.prop_unified_strength(row, context, brush, "use_pressure_strength")

        if brush.image_tool in {'DRAW', 'FILL'}:
            col.separator()
            col.prop(brush, "blend", text="Blend")

        col = layout.column()

        # use_accumulate
        if capabilities.has_accumulate:
            col = layout.column(align=True)
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
            # Stroke mode
            col.prop(brush, "stroke_method", text="")

            if brush.use_anchor:
                col.separator()
                col.prop(brush, "use_edge_to_edge", "Edge To Edge")

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
            row.prop(ipaint, "use_symmetry_x", text="X", toggle=True)
            row.prop(ipaint, "use_symmetry_y", text="Y", toggle=True)
            row.prop(ipaint, "use_symmetry_z", text="Z", toggle=True)

            # imagepaint tool operate  buttons: UILayout.template_ID_preview()
            col = layout.split().column()
            ###################################### ICI PROBLEME d'icones de brosse !
            # bpy.context.tool_settings.image_paint.brush

            col.template_ID_preview(settings, "brush", new="brush.add", rows=1, cols=3   )

            ########################################################################

            # Texture Paint Mode #
            if context.image_paint_object and brush:
                self.brush_texpaint_common( layout, context, brush, settings, True)

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
                col.prop(brush, "vertex_tool", text="Blend")

                col.separator()
                col.template_ID(settings, "palette", new="palette.new")




    def invoke(self, context, event):
        if context.space_data.type == 'IMAGE_EDITOR':
            context.space_data.mode = 'PAINT'

        return context.window_manager.invoke_props_dialog(self, width=148)
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

class D2P_OT_ProjectpaintPopup(bpy.types.Operator):
    """Slots ProjectPaint popup"""
    bl_idname = "view3d.projectpaint"
    bl_label = "Slots & VGroups"
    bl_options = {'REGISTER', 'UNDO'}

    def check(self, context):
        return True

    @classmethod
    def poll(cls, context):
        brush = context.tool_settings.image_paint.brush
        ob = context.active_object
        if brush is not None and ob is not None:
            A = ob.type == 'MESH'
            B = context.space_data.type == 'VIEW_3D'
            if A:
                C = context.mode in {'PAINT_TEXTURE', 'PAINT_VERTEX', 'PAINT_WEIGHT'}
                D = context.mode == 'EDIT_MESH'
            E = context.space_data.type == 'IMAGE_EDITOR'
            if E:
                F = context.mode == 'EDIT_MESH'
                G = context.space_data.mode == 'PAINT'
            H = context.mode == 'WEIGHT_PAINT' and ob.vertex_groups and ob.data.use_paint_mask_vertex
            return A and ((B and (C or D)) or (E and (F or G) or H))
        return False

    def draw(self, context):
        settings = context.tool_settings.image_paint
        ob = context.active_object

        layout = self.layout

        # Vertex Paint
        group = ob.vertex_groups.active
        rows = 4 if group else 2

        row = layout.row()
        row.template_list("MESH_UL_vgroups", "", ob, "vertex_groups", ob.vertex_groups, "active_index", rows=rows)

        col = row.column(align=True)
        col.operator("object.vertex_group_add", icon='ADD', text="")
        col.operator("object.vertex_group_remove", icon='REMOVE', text="").all = False
        col.menu("MESH_MT_vertex_group_specials", icon='DOWNARROW_HLT', text="")

        if group:
            col.separator()
            col.operator("object.vertex_group_move", icon='TRIA_UP', text="").direction = 'UP'
            col.operator("object.vertex_group_move", icon='TRIA_DOWN', text="").direction = 'DOWN'

        if ob.vertex_groups and (ob.mode == 'EDIT' or (ob.mode == 'WEIGHT_PAINT' and ob.type == 'MESH' and ob.data.use_paint_mask_vertex)):
            row = layout.row()

            sub = row.row(align=True)
            sub.operator("object.vertex_group_assign", text="Assign")
            sub.operator("object.vertex_group_remove_from", text="Remove")

            sub = row.row(align=True)
            sub.operator("object.vertex_group_select", text="Select")
            sub.operator("object.vertex_group_deselect", text="Deselect")

            layout.prop(context.tool_settings, "vertex_group_weight", text="Weight")

        # Material Paint
        if context.mode == 'PAINT_TEXTURE':
            col = layout.column()
            col.label(text="Painting Mode")
            col.prop(settings, "mode", text="")
            col.separator()

            if settings.mode == 'MATERIAL':
                if len(ob.material_slots) > 1:
                    col.label(text="Materials")
                    col.template_list("MATERIAL_UL_matslots", "layers", ob, "material_slots", ob, "active_material_index", rows=4)

                mat = ob.active_material
                if mat:
                    col.label(text="Available Paint Slots")
                    col.template_list("TEXTURE_UL_texpaintslots", "", mat, "texture_paint_images", mat, "paint_active_slot", rows=4)

                    if mat.texture_paint_slots:
                        slot = mat.texture_paint_slots[mat.paint_active_slot]
                    else:
                        slot = None

                    if not mat.use_nodes and context.scene.render.engine in {'BLENDER_EEVEE', 'CYCLES'}:
                        row = col.row(align=True)
                        row.operator_menu_enum("paint.add_texture_paint_slot", "type")
                        row.operator("paint.delete_texture_paint_slot", text="", icon='X')

                        if slot:
                            col.prop(mat.texture_slots[slot.index], "blend_type")
                            col.separator()

                    if slot:
                        col.label(text="UV Map")
                        col.prop_search(slot, "uv_layer", ob.data, "uv_textures", text="")

            elif settings.mode == 'IMAGE':
                mesh = ob.data
                uv_text = mesh.uv_textures.active.name if mesh.uv_textures.active else ""
                col.label(text="Canvas Image")
                col.template_ID(settings, "canvas")
                col.operator("image.new", text="New").gen_context = 'PAINT_CANVAS'
                col.label(text="UV Map")
                col.menu("VIEW3D_MT_tools_projectpaint_uvlayer", text=uv_text, translate=False)

            col.separator()
            if bpy.context.scene.render.engine == 'CYCLES':
                col.operator("paint.add_texture_paint_slot", text="Add Texture", icon="").type = "DIFFUSE_COLOR"
                col.operator("object.save_ext_paint_texture", text="Save selected Slot")
            else:
                col.operator("image.save_all_modified", text="Save All Images")

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

        wm = context.window_manager
        if "tpp_toolmode_on_screen" in wm:
            init_temp_props()
            co2d = (event.mouse_region_x, event.mouse_region_y)
            wm["tpp_toolmode_brushloc"] = co2d
            args = (self, context)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(\
                                                        toolmode_draw_callback,
                                                        args,
                                                        'WINDOW',
                                                        'POST_PIXEL')
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

        wm = context.window_manager
        if "tpp_toolmode_on_screen" in wm:
            init_temp_props()
            co2d = (event.mouse_region_x, event.mouse_region_y)
            wm["tpp_toolmode_brushloc"] = co2d
            args = (self, context)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(\
                                                        toolmode_draw_callback,
                                                        args,
                                                        'WINDOW',
                                                        'POST_PIXEL')
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

        wm = context.window_manager
        if "tpp_toolmode_on_screen" in wm:
            init_temp_props()
            co2d = (event.mouse_region_x, event.mouse_region_y)
            wm["tpp_toolmode_brushloc"] = co2d
            args = (self, context)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(\
                                                        toolmode_draw_callback,
                                                        args,
                                                        'WINDOW',
                                                        'POST_PIXEL')
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

        wm = context.window_manager
        if "tpp_toolmode_on_screen" in wm:
            init_temp_props()
            co2d = (event.mouse_region_x, event.mouse_region_y)
            wm["tpp_toolmode_brushloc"] = co2d
            args = (self, context)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(\
                                                        toolmode_draw_callback,
                                                        args,
                                                        'WINDOW',
                                                        'POST_PIXEL')
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
class OBJECT_OT_set_complementary_brush_color(bpy.types.Operator):
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


