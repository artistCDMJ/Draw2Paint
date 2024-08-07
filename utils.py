import bpy
import os
import re
import colorsys

import math


### nodes to compositor and back
def create_compositor_node_tree(image1, image2, blend_mode):
    bpy.context.scene.use_nodes = True
    tree = bpy.context.scene.node_tree

    # Clear existing nodes
    for node in tree.nodes:
        tree.nodes.remove(node)

    # Create image input nodes
    image_node1 = tree.nodes.new(type='CompositorNodeImage')
    image_node1.image = image1
    image_node1.location = -300, 200

    image_node2 = tree.nodes.new(type='CompositorNodeImage')
    image_node2.image = image2
    image_node2.location = -300, -200

    # Create a Mix node
    mix_node = tree.nodes.new(type='CompositorNodeMixRGB')
    mix_node.blend_type = blend_mode
    mix_node.location = 200, 0
    mix_node.use_alpha = True  # Enable the use_alpha property

    # Connect image nodes to the Mix node
    tree.links.new(image_node1.outputs['Image'], mix_node.inputs[1])
    tree.links.new(image_node2.outputs['Image'], mix_node.inputs[2])

    # Connect the alpha output of the second image to the factor input of the Mix node
    tree.links.new(image_node2.outputs['Alpha'], mix_node.inputs[0])

    # Add a Composite node to output the result
    composite_node = tree.nodes.new(type='CompositorNodeComposite')
    composite_node.location = 400, 0

    tree.links.new(mix_node.outputs['Image'], composite_node.inputs['Image'])

def render_and_extract_image(output_name, width, height):
    bpy.context.scene.render.resolution_x = width
    bpy.context.scene.render.resolution_y = height
    bpy.context.scene.render.image_settings.file_format = 'PNG'
    bpy.context.scene.render.filepath = f'/tmp/{output_name}.png'
    bpy.ops.render.render(write_still=True)
    combined_image = bpy.data.images.load(bpy.context.scene.render.filepath)
    return combined_image

#define function for check if mesh and _canvas in name
def is_canvas_mesh(obj):
    return obj and obj.type == 'MESH' and '_canvas' in obj.name
def is_subject_mesh(obj):
    return obj and obj.type == 'MESH' and '_subject' in obj.name

# workup functions for Trace2Curve to work
def new_convert_curve_object(collection, name):
    curve = bpy.data.curves.new(name=name, type="CURVE")
    curve.dimensions = "2D"
    convert_object = bpy.data.objects.new(name=name, object_data=curve)
    collection.objects.link(convert_object)
    return convert_object


def convert_gpencil_to_curve(gpencil_object, flatten_layers=True):
    gp_col = gpencil_object.users_collection[0]
    gp = gpencil_object.data
    if flatten_layers:
        obj = new_convert_curve_object(gp_col, gpencil_object.name + "_curve")
    for layer in gp.layers:
        if not flatten_layers:
            obj = new_convert_curve_object(gp_col, f"{gpencil_object.name}_curve_layer_{layer.info}")
        for frame in layer.frames:
            for stroke in frame.strokes:
                spline = obj.data.splines.new(type="POLY")
                spline.points.add(len(stroke.points) - 1)  # Spline starts with 1 point
                for i, point in enumerate(stroke.points):
                    # Adjust the point coordinate to match the original GPencil position
                    co = gpencil_object.matrix_world @ point.co
                    spline.points[i].co = [co.x, co.y, co.z, 1]
    return obj


def move_trace_objects_to_collection(objects, collection_name):
    # Create a new collection if it doesn't exist
    if collection_name not in bpy.data.collections:
        new_collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(new_collection)
    else:
        new_collection = bpy.data.collections[collection_name]

    for obj in objects:
        if obj.name not in new_collection.objects:
            new_collection.objects.link(obj)
        for coll in obj.users_collection:
            if coll.name != collection_name:
                coll.objects.unlink(obj)


def convert_image_plane_to_curve(plane_obj):
    # Ensure the object is of type 'MESH'
    if plane_obj.type != 'MESH':
        print(f"Selected object {plane_obj.name} is not a mesh.")
        return

    # Retrieve the image from the plane's material
    material = plane_obj.active_material
    if not material or not material.use_nodes:
        print(f"No material with nodes found on {plane_obj.name}.")
        return

    # Find the image texture node
    texture_node = None
    for node in material.node_tree.nodes:
        if node.type == 'TEX_IMAGE':
            texture_node = node
            break

    if not texture_node:
        print(f"No image texture node found in the material of {plane_obj.name}.")
        return

    # Get the image from the texture node
    image = texture_node.image
    if not image:
        print(f"No image found in the texture node of {plane_obj.name}.")
        return

    # Get the size of the plane
    scale_x = plane_obj.dimensions.x
    scale_y = plane_obj.dimensions.y

    # Create a new empty object
    bpy.ops.object.empty_add(type='IMAGE', location=plane_obj.location)
    empty_obj = bpy.context.object
    empty_obj.name = plane_obj.name + "_Empty"

    # Assign the image to the empty
    empty_obj.data = image

    # Make the image data single user
    bpy.ops.object.make_single_user(object=True, obdata=True, material=True, animation=False)

    # Set the scale of the empty to match the plane
    empty_obj.scale = (scale_x, scale_y, 1)

    # Apply the scale to the empty
    bpy.context.view_layer.objects.active = empty_obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    print(f"Converted {plane_obj.name} to {empty_obj.name}.")

    # Convert the Image Empty to Grease Pencil using Trace Image to Grease Pencil
    bpy.context.view_layer.objects.active = empty_obj
    bpy.ops.gpencil.trace_image()

    # Ensure the created object is a GPencil object before conversion
    gpencil_objs = [obj for obj in bpy.context.view_layer.objects if obj.type == 'GPENCIL']
    if gpencil_objs:
        gpencil_obj = gpencil_objs[-1]  # Get the most recently created GPencil object
        gpencil_obj.name = empty_obj.name + "_GPencil"

        # Convert the Grease Pencil to a Curve
        curve_obj = convert_gpencil_to_curve(gpencil_obj, flatten_layers=True)

        # Match the orientation and scaling of the original plane
        curve_obj.location = plane_obj.location
        curve_obj.rotation_euler = plane_obj.rotation_euler
        curve_obj.scale = plane_obj.scale

        print(f"Converted {gpencil_obj.name} to {curve_obj.name}.")

        # Move the original plane, image empty, and GPencil objects to the new collection
        collection_name = 'autotrace_objects_' + plane_obj.name
        move_trace_objects_to_collection([plane_obj, empty_obj, gpencil_obj], collection_name)

    else:
        print("The converted object is not a Grease Pencil object.")


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

### color calculations for palettes of color families
def rgb_to_hex(color):
    return "#{:02x}{:02x}{:02x}".format(int(color[0] * 255), int(color[1] * 255), int(color[2] * 255))


def complementary_color(color):
    return 1.0 - color[0], 1.0 - color[1], 1.0 - color[2]


def split_complementary_colors(color):
    h, s, v = colorsys.rgb_to_hsv(color[0], color[1], color[2])
    split1 = (h + 150.0 / 360.0) % 1.0
    split2 = (h - 150.0 / 360.0) % 1.0
    rgb1 = colorsys.hsv_to_rgb(split1, s, v)
    rgb2 = colorsys.hsv_to_rgb(split2, s, v)
    return rgb1, rgb2


def triadic_colors(color):
    h, s, v = colorsys.rgb_to_hsv(color[0], color[1], color[2])
    triad1 = (h + 120.0 / 360.0) % 1.0
    triad2 = (h - 120.0 / 360.0) % 1.0
    rgb1 = colorsys.hsv_to_rgb(triad1, s, v)
    rgb2 = colorsys.hsv_to_rgb(triad2, s, v)
    return rgb1, rgb2


def tetradic_colors(color):
    h, s, v = colorsys.rgb_to_hsv(color[0], color[1], color[2])
    tetrad1 = (h + 90.0 / 360.0) % 1.0
    tetrad2 = (h + 180.0 / 360.0) % 1.0
    tetrad3 = (h - 90.0 / 360.0) % 1.0
    rgb1 = colorsys.hsv_to_rgb(tetrad1, s, v)
    rgb2 = colorsys.hsv_to_rgb(tetrad2, s, v)
    rgb3 = colorsys.hsv_to_rgb(tetrad3, s, v)
    return rgb1, rgb2, rgb3


def analogous_colors(color):
    h, s, v = colorsys.rgb_to_hsv(color[0], color[1], color[2])
    ana1 = (h + 30.0 / 360.0) % 1.0
    ana2 = (h - 30.0 / 360.0) % 1.0
    rgb1 = colorsys.hsv_to_rgb(ana1, s, v)
    rgb2 = colorsys.hsv_to_rgb(ana2, s, v)
    return rgb1, rgb2


def create_palette(name, colors):
    if name in bpy.data.palettes:
        palette = bpy.data.palettes[name]
        palette.colors.clear()
    else:
        palette = bpy.data.palettes.new(name=name)

    # Add white and black to the palette
    white = (1.0, 1.0, 1.0)
    black = (0.0, 0.0, 0.0)

    # Add the primary colors
    colors = [white, black] + colors

    for color in colors:
        palette_color = palette.colors.new()
        palette_color.color = color
