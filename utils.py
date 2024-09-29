import bpy
import os
import re
import colorsys

import math
### texel density calculation
def calculate_texel_density(obj, desired_texel_density):
    # Calculate the surface area of the object
    obj_surface_area = sum(p.area for p in obj.data.polygons)

    # Calculate the required number of pixels (texels)
    required_texels = desired_texel_density * math.sqrt(obj_surface_area)

    # Determine the appropriate texture resolution
    # We assume square textures and round to the nearest power of two
    texture_size = 2 ** math.ceil(math.log2(required_texels))

    return texture_size

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

    # Create material and node setup with Emission and Principled BSDF
    mat = bpy.data.materials.new(name=name + "Material")
    mat.use_nodes = True

    # Get nodes
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.location = (-212.01303100585938, 704.966796875)
    tex_image = mat.node_tree.nodes.new('ShaderNodeTexImage')
    tex_image.location = (-617.7554931640625, 626.1090087890625)
    tex_image.image = active_image

    # Add Emission shader node
    emission = mat.node_tree.nodes.new('ShaderNodeEmission')
    emission.location = (-172.02610778808594, 348.537109375)

    # Add Mix Shader node
    mix_shader = mat.node_tree.nodes.new('ShaderNodeMixShader')
    mix_shader.location = (250.89752197265625, 651.1596069335938)

    # Connect Image texture to both shaders (BSDF and Emission)
    mat.node_tree.links.new(bsdf.inputs['Base Color'], tex_image.outputs['Color'])
    mat.node_tree.links.new(emission.inputs['Color'], tex_image.outputs['Color'])

    # Connect both shaders to the Mix Shader
    mat.node_tree.links.new(mix_shader.inputs[1], bsdf.outputs['BSDF'])
    mat.node_tree.links.new(mix_shader.inputs[2], emission.outputs['Emission'])

    # Optionally add a Value node to control the mix factor
    mix_factor = mat.node_tree.nodes.new('ShaderNodeValue')
    mix_factor.location = (243.66448974609375, 506.4412841796875)
    mix_factor.outputs[0].default_value = 0.5  # Default to 50% mix
    mat.node_tree.links.new(mix_shader.inputs[0], mix_factor.outputs[0])

    # Connect Mix Shader to Material Output
    material_output = mat.node_tree.nodes['Material Output']
    material_output.location = (453.1165466308594, 643.1837768554688)
    mat.node_tree.links.new(material_output.inputs['Surface'], mix_shader.outputs['Shader'])

    # Apply the material to the object
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

    # Set the camera as the main (active) camera
    bpy.context.scene.camera = cam_obj

    return cam_obj


def switch_to_camera_view(camera_obj):
    # Set the camera as the active camera for the scene
    bpy.context.scene.camera = camera_obj

    # Iterate over all the areas in the current screen to find the VIEW_3D areas
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            # Override the context for each 3D view area
            with bpy.context.temp_override(area=area):
                space = area.spaces.active
                space.region_3d.view_perspective = 'CAMERA'

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


### new function to move to new scene from name of active image in image editor or selected object active image node
def create_scene_based_on_active_image(selected_object=None):
    active_image = None

    # If a selected object is provided, try to get its texture image
    if selected_object:
        active_image = get_image_from_selected_object(selected_object)

    # If no image found on the selected object, try the image editor
    if not active_image:
        try:
            active_image = get_active_image_from_image_editor()
        except ValueError as e:
            print(e)

    # If an image is found, create a new scene based on the image's name
    if active_image:
        image_name = active_image.name
        new_scene = bpy.data.scenes.new(name=image_name)

        # Link the selected object to the new scene (only if an object is provided)
        if selected_object:
            new_scene.collection.objects.link(selected_object)

        # Switch to the new scene
        bpy.context.window.scene = new_scene

        # Set to transparent for the world
        new_scene.render.film_transparent = True

        # Unlock object selection for multiple objects
        new_scene.tool_settings.lock_object_mode = False

        # Set the render engine based on Blender version
        if bpy.app.version >= (4, 2, 0):
            new_scene.render.engine = 'BLENDER_EEVEE_NEXT'
        else:
            new_scene.render.engine = 'BLENDER_EEVEE'

        # Set color management settings
        paint_view_color_management_settings()

        # Copy the World shader from the original scene to the new scene
        bpy.context.scene.world = bpy.data.worlds['World']

        print(f"New scene created: {image_name}")
    else:
        print("No active image found to create a new scene.")

def export_uv_layout(obj, filepath):
    # Ensure the object is active and selected
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # Ensure the correct context is passed using context override
    with bpy.context.temp_override(object=obj):
        # Switch to Edit Mode
        bpy.ops.object.mode_set(mode="EDIT")

        # Select all faces
        bpy.ops.mesh.select_all(action='SELECT')

        # Export the UV layout to the given filepath
        bpy.ops.uv.export_layout(filepath=filepath, mode='PNG', opacity=0)

        # Switch back to Object Mode
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

# needed to swap windows to get active image to work here
def get_active_image_from_image_editor():
    # Try to get the active image from the Image Editor if it's already open
    for area in bpy.context.screen.areas:
        if area.type == 'IMAGE_EDITOR':
            for space in area.spaces:
                if space.type == 'IMAGE_EDITOR' and space.image:
                    return space.image

    # If no Image Editor is found, dynamically open one and check for an image
    image_found = False
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            # Temporarily switch the 3D Viewport to an Image Editor
            old_type = area.type
            area.type = 'IMAGE_EDITOR'
            for space in area.spaces:
                if space.type == 'IMAGE_EDITOR' and space.image:
                    image_found = True
                    active_image = space.image
                    break
            # Restore the area type back to VIEW_3D
            area.type = old_type
            if image_found:
                return active_image

    # If no image is found in the Image Editor, search in the Shader Editor
    for area in bpy.context.screen.areas:
        if area.type == 'NODE_EDITOR':
            for space in area.spaces:
                if space.type == 'NODE_EDITOR':
                    if space.node_tree and space.shader_type == 'OBJECT':
                        for node in space.node_tree.nodes:
                            if node.type == 'TEX_IMAGE' and node.image:
                                return node.image

    # If no image found in either Image or Shader Editors
    raise ValueError("No active image found in the Image Editor or Shader Editor")


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

# need for setting selection on toggle
def select_object_by_suffix(suffix):
    """Selects an object whose name ends with the given suffix in Blender and switches modes."""

    # Ensure we're in Object Mode first
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    # Deselect all objects
    bpy.ops.object.select_all(action='DESELECT')

    # Iterate through all objects in the scene
    for obj in bpy.data.objects:
        if obj.name.endswith(suffix):
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj  # Set as active object
            break

    # Switch to Texture Paint Mode after selecting the object
    bpy.ops.object.mode_set(mode='TEXTURE_PAINT')
