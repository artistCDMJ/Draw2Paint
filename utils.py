import bpy
import os
import re

import math


# Get the active texture node and its size
def get_active_texture_node_image_size():
    if bpy.context.space_data.type == 'NODE_EDITOR':
        node_tree = bpy.context.space_data.node_tree
        if node_tree:
            active_node = node_tree.nodes.active
            if active_node and active_node.type == 'TEX_IMAGE' and active_node.image:
                width = active_node.image.size[0]
                height = active_node.image.size[1]
                return width, height
    return None, None


# Get size of image in image editor
def get_active_image_size():
    if bpy.context.space_data.type == 'IMAGE_EDITOR':
        active_image = bpy.context.space_data.image
        if active_image:
            width = int(active_image.size[0])
            height = int(active_image.size[1])
            return width, height
    return None, None


# Create a new texture node based on the active node size
def create_new_texture_node_with_size(width, height):
    image_name = f"Texture_{width}x{height}"
    new_image = bpy.data.images.new(name=image_name, width=width, height=height)

    if bpy.context.space_data.type == 'NODE_EDITOR':
        node_tree = bpy.context.space_data.node_tree
        if node_tree:
            new_texture_node = node_tree.nodes.new(type='ShaderNodeTexImage')
            new_texture_node.image = new_image
            new_texture_node.label = image_name

            active_node = node_tree.nodes.active
            if active_node:
                new_texture_node.location = (active_node.location.x, active_node.location.y - 260)

# Function to set up single texture paint view
def single_texture_paint_view():
    # Iterate through all areas in the current screen context
    for area in bpy.context.screen.areas:
        # Check if the area is a 3D Viewport
        if area.type == 'VIEW_3D':
            space = area.spaces.active
            # Check if the active space is a 3D Viewport
            if space.type == 'VIEW_3D':
                # Set shading type to Solid
                space.shading.type = 'SOLID'
                # Set lighting to Flat
                space.shading.light = 'FLAT'
                # Set color type to Texture
                space.shading.color_type = 'TEXTURE'

# Function to set up multi texture paint view
def multi_texture_paint_view():
    # Iterate through all areas in the current screen context
    for area in bpy.context.screen.areas:
        # Check if the area is a 3D Viewport
        if area.type == 'VIEW_3D':
            space = area.spaces.active
            # Check if the active space is a 3D Viewport
            if space.type == 'VIEW_3D':
                # Set shading type to Material
                space.shading.type = 'MATERIAL'

# Function to set color management settings for painting
def paint_view_color_management_settings():
    scene = bpy.context.scene
    # Set the display device to sRGB
    scene.display_settings.display_device = 'sRGB'
    # Set the view transform to Standard
    scene.view_settings.view_transform = 'Standard'
    # Set the look to Medium High Contrast
    scene.view_settings.look = 'Medium Contrast'
    # Set the exposure to 0
    scene.view_settings.exposure = 0
    # Set the gamma to 1
    scene.view_settings.gamma = 1





def next_power_of_2(x):
    return 1 if x == 0 else 2**math.ceil(math.log2(x))

def previous_power_of_2(x):
    return 1 if x == 0 else 2**math.floor(math.log2(x))


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
    im_name = image_plane_obj.name + "_camera_view"
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


def find_brush(context):
    tool_settings = context.tool_settings
    if context.mode == 'SCULPT':
        return tool_settings.sculpt.brush
    elif context.mode == 'PAINT_TEXTURE':
        return tool_settings.image_paint.brush
    elif context.mode == 'PAINT_VERTEX':
        return tool_settings.vertex_paint.brush
    else:
        return None
