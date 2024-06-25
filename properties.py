import bpy

import bgl, blf, mathutils, os, time, copy, math, re

########PBRA Adopted Lapineiges (Snow Bunnies)

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

def register():
    bpy.utils.register_class(D2P_Properties)
    bpy.types.Scene.d2p_properties = bpy.props.PointerProperty(type=D2P_Properties)
    bpy.types.Scene.image_resize_addon_width = bpy.props.IntProperty(name="Width")
    bpy.types.Scene.image_resize_addon_height = bpy.props.IntProperty(name="Height")
    bpy.types.Scene.image_resize_addon_percentage = bpy.props.FloatProperty(name="Scale Percentage", default=100.0,
                                                                            min=0.0)
    bpy.types.Scene.view_mode = bpy.props.EnumProperty(
        name="View Mode",
        description="Current view mode",
        items=[
            ('SINGLE', "Single Texture", "Single Texture Paint View"),
            ('MULTI', "Multi Texture", "Multi Texture Paint View"),
        ],
        default='SINGLE'
    )

def unregister():
    del bpy.types.Scene.d2p_properties
    bpy.utils.unregister_class(D2P_Properties)
    del bpy.types.Scene.image_resize_addon_width
    del bpy.types.Scene.image_resize_addon_height
    del bpy.types.Scene.image_resize_addon_percentage
    del bpy.types.Scene.view_mode


