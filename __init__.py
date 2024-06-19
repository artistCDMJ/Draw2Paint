# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Draw2Paint",
    "author": "CDMJ, Spirou4D, Lapineige, Bart Crouch",
    "version": (4, 0, 5),
    "blender": (4, 2, 0),
    "location": "UI > Draw2Paint",
    "description": "2D Paint in 3D View, Mask Manipulation, EZPaint Adoption",
    "warning": "",
    "category": "Paint",
}
#####imports

import bpy
import bmesh

import bgl, blf, bpy, mathutils, os, time, copy, math, re

from bpy.props import *
from bpy.types import Operator, Menu, Panel, UIList
from bpy_extras.io_utils import ImportHelper

################# new def for cam work

def create_image_plane_from_image(active_image, scale_factor=0.01):
    
    width = active_image.size[0]
    height = active_image.size[1]
    
    name = active_image.name + "_canvas"
    print(f"Active image dimensions: {width} x {height}")

    mesh = bpy.data.meshes.new(name=name + "Mesh")
    obj = bpy.data.objects.new(name=name, object_data=mesh)

    bpy.context.collection.objects.link(obj)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.primitive_plane_add(size=1)
    bpy.ops.transform.resize(value=(width * scale_factor / 5, height * scale_factor / 5, 1))
    bpy.ops.object.mode_set(mode='OBJECT')

    mat = bpy.data.materials.new(name=name + "Material")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    tex_image = mat.node_tree.nodes.new('ShaderNodeTexImage')
    tex_image.image = active_image
    mat.node_tree.links.new(bsdf.inputs['Base Color'], tex_image.outputs['Color'])
    obj.data.materials.append(mat)
    
     # Rename the UV map
    uv_layer = obj.data.uv_layers.active
    uv_layer.name = name + "_uvmap"

    # Update the view layer to ensure transformations are applied
    bpy.context.view_layer.update()

    return obj, width * scale_factor, height * scale_factor

def create_matching_camera(image_plane_obj, width, height, distance=1):
    im_name = image_plane_obj.name+ "_camera_view"
    cam_data = bpy.data.cameras.new(name=im_name)
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = max(width, height) / 5
    
    cam_obj = bpy.data.objects.new(name=im_name, object_data=cam_data)
    
    bpy.context.collection.objects.link(cam_obj)

    cam_obj.location = (0, 0, distance)
    cam_obj.rotation_euler = (0, 0, 0)

    scene = bpy.context.scene
    scene.render.resolution_x = int(width / 0.01)  # Converting back to original resolution
    scene.render.resolution_y = int(height / 0.01)  # Converting back to original resolution
    
    return cam_obj

def switch_to_camera_view(camera_obj):
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            space = area.spaces.active
            space.region_3d.view_perspective = 'CAMERA'
            
            bpy.context.scene.camera = camera_obj
                   
            break

def get_image_from_selected_object(selected_object):
    if selected_object.type == 'MESH' and selected_object.active_material:
        nodes = selected_object.active_material.node_tree.nodes
        for node in nodes:
            if node.type == 'TEX_IMAGE':
                return node.image
    return None

def move_object_to_collection(obj, collection_name):
    # Get the collection or create it if it doesn't exist
    collection = bpy.data.collections.get(collection_name)
    if not collection:
        collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(collection)
    
    # Unlink the object from all its current collections
    for coll in obj.users_collection:
        coll.objects.unlink(obj)
    
    # Link the object to the new collection
    collection.objects.link(obj)

def export_uv_layout(obj, filepath):
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.export_layout(filepath=filepath, mode='PNG', opacity=0)
    bpy.ops.object.mode_set(mode='OBJECT')

def set_camera_background_image(camera_obj, filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    img = bpy.data.images.load(filepath)
    camera_obj.data.show_background_images = True
    bg = camera_obj.data.background_images.new()
    bg.image = img
    bg.alpha = 1.0
    bg.display_depth = 'FRONT'
    
def get_active_image_from_image_editor():
    for area in bpy.context.screen.areas:
        if area.type == 'IMAGE_EDITOR':
            for space in area.spaces:
                if space.type == 'IMAGE_EDITOR':
                    if space.image:
                        return space.image
    raise ValueError("No active image found in the Image Editor")

def increment_filename(filepath):
    directory, filename = os.path.split(filepath)
    name, ext = os.path.splitext(filename)

    match = re.match(r"^(.*?)(\d+)$", name)
    
    if match:
        base_name = match.group(1)
        number = int(match.group(2))
        new_name = f"{base_name}{number + 1:04d}{ext}"
    else:
        base_name = name
        new_name = f"{base_name}_0001{ext}"
        
    new_filepath = os.path.join(directory, new_name)
    
    while os.path.exists(new_filepath):
        match = re.match(r"^(.*?)(\d+)$", base_name)
        if match:
            base_name = match.group(1)
            number = int(match.group(2))
            base_name = f"{base_name}{number + 1:04d}"
        else:
            base_name = base_name + "_0001"
        new_name = f"{base_name}{ext}"
        new_filepath = os.path.join(directory, new_name)
        
    return new_filepath

def save_incremental_copy(image):
    if image.packed_file:
        print(f"Unpacking image {image.name}")
        image.unpack(method='USE_ORIGINAL')
        
    filepath = bpy.path.abspath(image.filepath)
    new_filepath = increment_filename(filepath)
    
    image.save_render(new_filepath)
    
    print(f"Image saved as {new_filepath}")



    
######### NEW OPERATORS FOR CANVAS AND CAMERA WORK

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



#########################REWRITE IN PROGRESSS###############

##### main operators grouped

########### props

########PBRA Adopted

bpy.types.Scene.x_min_pixels = bpy.props.IntProperty(min=0,
                 description="Minimum X value (in pixel) for the render border")
bpy.types.Scene.x_max_pixels = bpy.props.IntProperty(min=0,
                 description="Maximum X value (in pixel) for the render border")
bpy.types.Scene.y_min_pixels = bpy.props.IntProperty(min=0,
                 description="Minimum Y value (in pixel) for the render border")
bpy.types.Scene.y_max_pixels = bpy.props.IntProperty(min=0,
                 description="Maximum Y value (in pixel) for the render border")


########### propertygroup

class D2P_Properties(bpy.types.PropertyGroup):
    my_string: bpy.props.StringProperty(name="Enter Text")

    # my_float_vector : bpy.props.FloatVectorProperty(name= "Scale", soft_min= 0,
    # soft_max= 1000, default= (1,1,1))
    my_float: bpy.props.FloatProperty(name="CVP Influence", min=0,
                                      max=1.0, default=0.0)

    my_enum: bpy.props.EnumProperty(
        name="",
        description="Choose Curve To Draw",
        items=[('OP1', "Draw Curve", ""),
               ('OP2', "Draw Vector", ""),
               ('OP3', "Draw Square", ""),
               ('OP4', "Draw Circle", "")
               ]
    )




############### must use for clean scene to paint in
# ------------------------ D2P SCENE
class D2P_OT_D2PaintScene(bpy.types.Operator):
    """Create Draw2Paint Scene"""
    bl_description = "Create Scene for Working in Draw2Paint"
    bl_idname = "d2p.create_d2p_scene"
    bl_label = "Create Scene for Draw2Paint"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
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

        # set to top view
        bpy.ops.view3d.view_axis(type='TOP', align_active=True)
        # set to Eevee
        bpy.context.scene.render.engine = 'BLENDER_EEVEE'

        return {'FINISHED'}


########## not needed for painting, this is sculpt only for using references, deprecated usage
class D2P_OT_SculptView(bpy.types.Operator):
    """Sculpt View Reference Camera"""
    bl_idname = "d2p.sculpt_camera"
    bl_label = "Sculpt Camera"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        if obj is not None:
            A = obj.type == 'MESH'
            B = context.mode == 'SCULPT'
            return A and B

    def execute(self, context):
        scene = context.scene

        bpy.ops.object.camera_add(align='VIEW',
                                  enter_editmode=False,
                                  location=(0, -4, 0),
                                  rotation=(1.5708, 0, 0)
                                  )
        context.object.name = "Reference Cam"  # add camera to front view
        context.object.data.show_passepartout = False
        context.object.data.lens = 80
        bpy.ops.view3d.object_as_camera()

        # change to camera view
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                override = bpy.context.copy()
                override['area'] = area
                # bpy.ops.view3d.viewnumpad(override, type='CAMERA')
                bpy.ops.view3d.camera_to_view()
                break
        scene.render.resolution_x = 1920
        scene.render.resolution_y = 1080

        bpy.context.object.data.show_name = True

        # collection for sculpt reference

        return {'FINISHED'}


#################### shader applications
###############test material holdout generator
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

############# FOR MASK OBJECTS FOR (RE)PROJECT
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



########## POOR MAN'S LIQUIFY FILTER, ADJUST AFTER PAINTING
######################## sculpt to liquid
class D2P_OT_SculptDuplicate(bpy.types.Operator):
    """Duplicate Selected Image Plane, Single User for Eraser Paint"""
    bl_idname = "d2p.sculpt_duplicate"
    bl_label = "Sculpt Liquid Duplicate"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene

        bpy.ops.paint.texture_paint_toggle()
        #all this was pulled to the left for pep-8, need to test if ok
        bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":
                                   False, "mode": 'TRANSLATION'},
          TRANSFORM_OT_translate={"value": (0, 0, 0), "orient_axis_ortho": 'X',
                                  "orient_type": 'GLOBAL',
                                  "orient_matrix": ((0, 0, 0), (0, 0, 0),
                                                    (0, 0, 0)),
                                  "orient_matrix_type": 'GLOBAL',
                                  "constraint_axis": (False, False, False),
                                  "mirror": False,
                                  "use_proportional_edit": False,
                                  "proportional_edit_falloff": 'SMOOTH',
                                  "proportional_size": 1,
                                  "use_proportional_connected": False,
                                  "use_proportional_projected": False, "snap":
                                      False,
                                  "snap_target": 'CLOSEST', "snap_point":
                                      (0, 0, 0),
                                  "snap_align": False, "snap_normal": (0, 0, 0),
                                  "gpencil_strokes": False, "cursor_transform":
                                      False,
                                  "texture_space": False, "remove_on_cancel":
                                      False,
                                  "view2d_edge_pan": False, "release_confirm":
                                      False,
                                  "use_accurate": False,
                                  "use_automerge_and_split": False})
        bpy.ops.transform.translate(value=(0, 0, 0.1))
        # context.object.active_material.use_shadeless = True
        # context.object.active_material.use_transparency = True
        # context.object.active_material.transparency_method = 'Z_TRANSPARENCY'
        bpy.ops.view3d.localview()
        bpy.ops.paint.texture_paint_toggle()

        # make ERASER brush or use exisitng
        try:
            context.tool_settings.image_paint.brush = bpy.data.brushes["Eraser"]
            pass
        except:
            context.tool_settings.image_paint.brush = bpy.data.brushes["TexDraw"]
            bpy.ops.brush.add()
            bpy.data.brushes["TexDraw.001"].name = "Eraser"
            # context.scene.tool_settings.unified_\
                          #paint_settings.use_pressure_size = False
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


############### canvas rotations GOOD NEW STUFF HERE

# flip horizontal macro
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


# --------------------------------flip vertical macro

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





# --------------------------------image rotation reset

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






#######################GOOD STUFF
################------------------------Precision Render Border Adjust Imported
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

############### GOOD
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


######################## bordercrop from ez-draw panel revised
############## haven't decided on setting this up as toggle or not,
# missing scene preferences stored in addon like ez-draw did
# ---------------------------------------------------------------BORDER CROP ON
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


# --------------------------------------------------------------BORDER CROP OFF
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


# -------------------------------------------------------------BORDER CROP TOGGLE
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

################ GOOD FOR MULTIPLE USE, EVEN GENERATING NEW CANVAS AND USING 
################ NEW OPS FOR IMAGE AND CAM FROM 
# ------------------------------try new image make
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
    
    
########### GOOD

# -----------------------------image save

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


############## GOOD

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

################# save all pack all

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

################# already works GOOD
# -----------------------------------reload image

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

        obdat = context.active_object.data
        ima = obdat.materials[0].texture_paint_images[0]
        context.space_data.image = ima
        bpy.ops.image.reload()  # return image to last saved state

        context.area.ui_type = original_type
        return {'FINISHED'}

    
############# probably needs work

########### pivot works
class D2P_OT_EmptyGuides(bpy.types.Operator):
    """Create new empty guide or selected guide relocate origin"""
    bl_idname = "d2p.empty_guides"
    bl_label = "Empty Guides Constrained"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        A = obj is not None
        if A:
            B = obj.type == 'MESH' or 'EMPTY'
            return B

    def execute(self, context):

        scene = context.scene
        layer = bpy.context.view_layer
        layer.update()

        # toggle texpaint and deselect
        obj = context.active_object

        if obj == bpy.data.objects[obj.name+'_canvas']:
            bpy.ops.paint.texture_paint_toggle()
            bpy.ops.object.select_all(action='DESELECT')
            # need check here for ['Symmetry Guide']

            for ob in bpy.data.objects:
                if ob.type == 'EMPTY' and ob.name == 'Symmetry Guide':
                    # need to set the symmmetry empty as active
                    bpy.ops.object.select_all(action='DESELECT')
                    bpy.data.objects['Symmetry Guide'].select_set(True)
                    # need to snap cursor to it
                    bpy.ops.view3d.snap_cursor_to_selected()
                    # need to set the canvas as active again
                    bpy.data.objects['Symmetry Guide'].select_set(False)
                    bpy.data.objects['canvas'].select_set(True)

                    pass
                else:
                    # add empty here
                    bpy.ops.object.empty_add(type='SPHERE', location=(0, 0, 0),
                                             radius=0.01)
                    # add empty for reference and movement of origin

                    # rename new empty to Symmetry Guide
                    bpy.context.object.name = "Symmetry Guide"

                    bpy.ops.transform.resize(value=(10, 10, 10))
                    # scale up past the normal range of image plane
                    # add constraint to follow canvas rotation
                    bpy.ops.object.parent_set(type='OBJECT', keep_transform=False)
                    
                    # snap cursor to empty
                    bpy.ops.view3d.snap_cursor_to_selected()

                    bpy.ops.object.select_all(action='DESELECT')
                    bpy.data.objects['Symmetry Guide'].select_set(False)
                    bpy.data.objects['canvas'].select_set(True)
                    bpy.context.view_layer.objects.active = \
                        bpy.data.objects['canvas']

                    bpy.ops.paint.texture_paint_toggle()

                    return {'FINISHED'}



        elif obj == bpy.data.objects['Symmetry Guide']:
            # already have empty, will work for cursors :D
            bpy.ops.view3d.snap_cursor_to_selected()

            # here to set origin of canvas
            bpy.ops.object.select_all(action='DESELECT')
            bpy.data.objects['Symmetry Guide'].select_set(False)
            bpy.data.objects['canvas'].select_set(True)
            bpy.context.view_layer.objects.active = bpy.data.objects['canvas']
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
            # bpy.ops.object.select_all(action='DESELECT')
            bpy.data.objects['canvas'].select_set(False)
            bpy.data.objects['Symmetry Guide'].select_set(True)

            # bpy.ops.paint.texture_paint_toggle()

            return {'FINISHED'}
        else:
            return {'FINISHED'}

        return {'FINISHED'}


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


################ legacy

############################################################
# -------------------LEGACY FOR ADDITION TO PANEL OPERATORS
############################################################


############## good
# ----------------------------------------------------------------FRONT OF PAINT
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

############ old
# -----------------------------------------------------------\BORDER CROP TOGGLE
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

############## good

#################### mask specials

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





###########new curve primitives for drawing masks

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

############## good
####################### boolean masks work
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

        '''old_mesh = obj.data  # get a reference to the current obj.data

        apply_modifiers = False  # settings for to_mesh
        new_mesh = obj.to_mesh(preserve_all_data_layers=True, depsgraph=None)
        obj.modifiers.clear()  # object will still have modifiers, remove them
        obj.data = new_mesh  # assign the new mesh to obj.data
        bpy.data.meshes.remove(old_mesh)  # remove the old mesh from the .blend
        context.object.draw_type = 'TEXTURED'''

        return {'FINISHED'}

############## good
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

############## good
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

############## good for object view collection work

############################## Vert Groups Forced into Ops
########################-------------------------vgroup force ops

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


#############################Face Mask Groups FMG+
#############################  -------FMG

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
    
############## good

######## Grease Pencil Blank Addition to Paint

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
#EZPaint Adopted Testing   GOOD
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





#-----------------------------------------------------------#Modify Texture/mask image
def find_brush(context):                 # Trouver la brosse
    tool_settings = context.tool_settings
    if context.mode == 'SCULPT':
        return tool_settings.sculpt.brush
    elif context.mode == 'PAINT_TEXTURE':
        return tool_settings.image_paint.brush
    elif context.mode == 'PAINT_VERTEX':
        return tool_settings.vertex_paint.brush
    else:
        return None


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






########################################
## panel draw for Draw2Paint
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

        '''row = layout.row()
        row = col.row(align=True)
        row.scale_x = 0.50
        row.scale_y = 1.25
        row3 = row.split(align=True)
        row3.operator("d2p.save_increm", text="Save Increment",
                      icon='FILE_IMAGE')'''


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


################################ 3D to 2D Experimental Workflow Items

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

        ##################### render.use_crop_to_border
        # box = layout.box()
        # col = box.column(align=True)
        # col.label(text="Crop Tools PRBA")
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
        # ("d2p.remove_modifiers", text='Remove Mods', icon='UNLINKED')
        row = col.row(align=True)
        row = row.split(align=True)
        row.scale_x = 0.50
        row.scale_y = 1.25
        row.operator("d2p.remove_modifiers", text='Remove Mods',
                     icon='UNLINKED')

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
        
        


classes = (

    D2P_Properties,
    D2P_OT_CanvasHoriz,
    D2P_OT_CanvasVertical,
    D2P_OT_ImageReload,
    D2P_OT_CanvasResetrot,
    D2P_OT_SaveImage,
    D2P_OT_SaveDirty,
    D2P_OT_EmptyGuides,
    D2P_OT_PixelsToBorder,
    D2P_OT_BorderToPixels,
    D2P_OT_BorderCrop,
    D2P_OT_BorderUnCrop,
    D2P_OT_SculptDuplicate,
    D2P_OT_SculptLiquid,
    D2P_OT_ReprojectMask,
    D2P_OT_CanvasMaterial,
    D2P_OT_SolidifyDifference,
    D2P_OT_SolidifyUnion,
    D2P_OT_RemoveMods,
    D2P_OT_BorderCropToggle,
    D2P_OT_FrontOfPaint,
    D2P_OT_getFaceMaskGroups,
    D2P_OT_UnassignVertgroup,
    D2P_OT_AssignVertgroup,
    D2P_OT_DeselectVertgroup,
    D2P_OT_SelectVertgroup,
    D2P_OT_holdout_shader,
    D2P_OT_center_object,
    D2P_OT_my_enum_shapes,
    D2P_OT_NewGpencil,
    D2P_OT_NewImage,
    D2P_OT_D2PaintScene,
    D2P_OT_DisplayActivePaintSlot,
    D2P_OT_ModifyBrushTextures,
    D2P_OT_ToggleAlphaMode,
    D2P_OT_ToggleColorSoftLightScreen,
    D2P_OT_ToggleAddMultiply,
    D2P_OT_MakeBrushImageTextureMask,
    D2P_OT_MakeBrushImageTexture,
    D2P_OT_ProjectpaintPopup,
    D2P_OT_TexturePopup,
    D2P_OT_BrushPopup,
    D2P_OT_CanvasAndCamera,
    D2P_OT_CameraFromCanvas,
    D2P_OT_SelectedToCanvasAndCamera,
    D2P_OT_ImageEditorToCanvasAndCamera,
    D2P_OT_ToggleUVInCamera,
    D2P_OT_ToggleCollectionView,
    D2P_OT_SaveIncrem,
    D2P_PT_ImageState,
    D2P_PT_GreasePencil,
    D2P_PT_FlipRotate,
    D2P_PT_ImageCrop,
    D2P_PT_2D_to_3D_Experimental,
    D2P_PT_GuideControls,
    D2P_PT_MaskControl,
    D2P_PT_Sculpt2D,
    D2P_PT_ImagePlanePanel
    
    
    
    

)

#############

addon_keymaps = []

# kmi_defs entry: (identifier, key, action, CTRL, SHIFT, ALT, OSKEY , props, nice name)
# props entry: ,((property name, property value), (property name, property value), ...),....
kmi_defs = (

    # Brushes Popup [Image Paint] with: W.
    (('Image Paint', 'EMPTY'), "view3d.brush_popup", 'W', 'PRESS', False, False, False, False, None, "Brushes Popup"),
    # 2D Editor Popup with Active Paint Slot with Shift + Alt + W
    (('Image Paint', 'EMPTY'), "paint.display_active_slot", 'W', 'PRESS', False, True, True, False, None, "2D Editor Popup"),
    # Slots Popup [Image Paint] with: Shift + W.
    (('Image Paint', 'EMPTY'), "view3d.projectpaint", 'W', 'PRESS', False, True, False, False, None, "Slots Popup"),
    # Textures Popup [Image Paint] with: Alt + W.
    (('Image Paint', 'EMPTY'), "view3d.texture_popup", 'W', 'PRESS', False, False, True, False, None, "Textures Popup"),


    # Toggle add/multily modes [Image Paint] with: D.
    (('Image Paint', 'EMPTY'), "paint.toggle_add_multiply", 'D', 'PRESS', False, False, False, False, None, "Toggle add/multiply modes"),
    # Toggle color/soft light modes [Image Paint] with: Ctrl + D
    (('Image Paint', 'EMPTY'), "paint.toggle_color_soft_light_screen", 'D', 'PRESS', False, True, False, False, None, "Toggle color/soft light modes"),
    # Toggle Alpha modes [Image Paint] with: A.
    (('Image Paint', 'EMPTY'), "paint.toggle_alpha_mode", 'A', 'PRESS', False, False, False, False, None, "Toggle Alpha modes"),
    # Re-init Mix mode [Image Paint] with: Alt + D.
    (('Image Paint', 'EMPTY'), "paint.init_blend_mode", 'D', 'PRESS', False, False, True, False, None, "Re-init Mix mode")

)

def Register_Shortcuts():
    addon_keymaps.clear()
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        # for each kmi_def:
        for (spacetype, identifier, key, action, CTRL, SHIFT, ALT, OS_KEY, props, nicename) in kmi_defs:
            if spacetype[0] in bpy.context.window_manager.keyconfigs.addon.keymaps.keys():
                if spacetype[1] in kc.keymaps[spacetype[0]].space_type:
                    km = kc.keymaps[spacetype[0]]
            else:
                km = kc.keymaps.new(name = spacetype[0], space_type = spacetype[1])
            kmi = km.keymap_items.new(identifier, key, action, ctrl=CTRL, shift=SHIFT, alt=ALT, oskey=OS_KEY)
            if props:
                for prop, value in props:
                    setattr(kmi.properties, prop, value)
            addon_keymaps.append((km, kmi))


#############
def register():
    # init_temp_props()
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
        
        # keymaps
    Register_Shortcuts()



    bpy.types.Scene.my_tool = bpy.props.PointerProperty(type=D2P_Properties)


def unregister():
    # remove_temp_props()
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    
        # keymaps
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()



    del bpy.types.Scene.my_tool


if __name__ == '__main__':
    register()

