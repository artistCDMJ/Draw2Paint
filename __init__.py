# GNU General Public License
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
    "author": "CDMJ, Spirou4D, Lapineige, Bart Crouch, batFINGER, stacker, todashuta",
    "version": (4, 1, 3),
    "blender": (4, 3, 0),
    "location": "UI > Draw2Paint",
    "description": "2D Paint in 3D View, Mask Manipulation, EZPaint Adoption",
    "warning": "",
    "category": "Paint",
}


##### imports
import os
import bpy
import bmesh
import colorsys

import bgl, blf, bpy, mathutils, time, copy, math, re

from bpy.props import *
from bpy.utils import *
from bpy.types import Operator, Menu, Panel, UIList
from bpy_extras.io_utils import ImportHelper

# Ensure all modules and classes are imported correctly
from .operators import *
from .ui import *
from . import keymaps, properties




classes = (
    properties.D2P_Properties,
    D2P_OT_UV2Mask,
    D2P_OT_CanvasX,
    D2P_OT_CanvasY,
    D2P_OT_ImageReload,
    D2P_OT_ReloadAll,
    D2P_OT_CanvasReset,
    D2P_OT_SaveImage,
    D2P_OT_SaveDirty,
    D2P_OT_Guide2Canvas,
    D2P_OT_PixelsToBorder,
    D2P_OT_BorderToPixels,
    D2P_OT_BorderCrop,
    D2P_OT_BorderUnCrop,
    D2P_OT_Copy2Eraser,
    D2P_OT_LiquidSculpt,
    D2P_OT_ReprojectMask,
    D2P_OT_CanvasMaterial,
    D2P_OT_SolidifyDifference,
    D2P_OT_SolidifyUnion,
    D2P_OT_RemoveMods,
    D2P_OT_BorderCropToggle,
    D2P_OT_Align2Face,
    D2P_OT_getFaceMaskGroups,
    D2P_OT_UnassignVertgroup,
    D2P_OT_AssignVertgroup,
    D2P_OT_DeselectVertgroup,
    D2P_OT_SelectVertgroup,
    D2P_OT_holdout_shader,
    D2P_OT_Recenter,
    D2P_OT_my_enum_shapes,
    D2P_OT_GPencil2Canvas,
    D2P_OT_Image2Scene,
    D2P_OT_Slot2Display,
    D2P_OT_ModifyBrushTextures,
    D2P_OT_InitPaintBlend,
    D2P_OT_ToggleAlphaMode,
    D2P_OT_ToggleColorSoftLightScreen,
    D2P_OT_ToggleAddMultiply,
    D2P_OT_MakeBrushImageTextureMask,
    D2P_OT_MakeBrushImageTexture,
    D2P_OT_SlotsVGroupsPopup,
    D2P_OT_TexturePopup,
    D2P_OT_BrushPopup,
    D2P_OT_Subject2Canvas,
    D2P_OT_Image2CanvasPlus,
    D2P_OT_ToggleUV2Camera,
    D2P_OT_ToggleCollectionView,
    D2P_OT_SaveIncrem,
    D2P_PT_ImageCreation,
    D2P_PT_PhotoStack,
    D2P_PT_GreasePencil,
    D2P_PT_FlipRotate,
    D2P_PT_Crop2Camera,
    D2P_PT_3dImageEditor,
    D2P_PT_Symmetry2Guide,
    D2P_PT_MaskTools,
    D2P_PT_Sculpt2D,
    D2P_OT_SetMultiTexturePaintView,
    D2P_OT_SetSingleTexturePaintView,
    D2P_OT_GetImageSizeOperator,
    D2P_OT_NewTextureNode,
    D2P_PT_Image2CanvasPlus,
    IMAGE_RESIZE_OT_width_mul2,
    IMAGE_RESIZE_OT_height_mul2,
    IMAGE_RESIZE_OT_width_div2,
    IMAGE_RESIZE_OT_height_div2,
    IMAGE_RESIZE_OT_getcurrentsize,
    IMAGE_RESIZE_OT_scale_percentage,
    IMAGE_RESIZE_OT_main,
    IMAGE_RESIZE_PT_panel,
    D2P_PT_node_editor_panel,
    D2P_OT_SetColorFamilies,
    D2P_OT_Trace2Curve,
    D2P_OT_flip_gradient,
    D2P_OT_CalculateTexelDensity,
    D2P_OT_Shader2ViewerNode,
    D2P_OT_Viewer2Image,
    D2P_OT_EditorSwap,
    UV_WireColor,
    VIEW3D_WireColor,
    D2P_OT_set_active_texture_slot,
    D2P_OT_set_active_clone_slot,
    PhotoStackProperties,
    PhotoStack,
    NODE_OT_copy_photostack_to_compositor,
    TextureSwapProperties,
    SwapSelectedTextures,
    D2P_PT_PalettePopup

)

def register():
    for cls in classes:
        if hasattr(bpy.types, cls.__name__):
            bpy.utils.unregister_class(cls)
        bpy.utils.register_class(cls)
    bpy.types.IMAGE_MT_image.append(draw_image_editor_button)
    bpy.types.NODE_MT_node.append(draw_node_editor_button)
    bpy.types.Scene.my_mask = bpy.props.PointerProperty(type=properties.D2P_Properties)
    bpy.types.Scene.image_resize_addon_width = bpy.props.IntProperty(name="Width")
    bpy.types.Scene.image_resize_addon_height = bpy.props.IntProperty(name="Height")
    bpy.types.Scene.image_resize_addon_percentage = bpy.props.FloatProperty(name="Scale Percentage", default=100.0,
                                                                            min=0.0)
    bpy.types.Scene.texel_density_result = bpy.props.StringProperty(name="Texel Density Result", default="")
    bpy.types.Node.texture_swap_props = bpy.props.PointerProperty(type=TextureSwapProperties)
    bpy.types.Scene.view_mode = bpy.props.EnumProperty(
        name="View Mode",
        description="Current view mode",
        items=[
            ('SINGLE', "Single Texture", "Single Texture Paint View"),
            ('MULTI', "Multi Texture", "Multi Texture Paint View"),
        ],
        default='SINGLE'
    )

    if hasattr(keymaps, 'register'):
        keymaps.register()
    bpy.types.VIEW3D_PT_tools_brush_color.append(draw_func)

    bpy.types.Scene.num_textures = bpy.props.IntProperty(
        name="Number of Textures",
        default=1,  # Set default to 1
        min=1,
        max=10,
        description="Number of image textures to add",
        update=update_texture_settings  # Ensure we update texture settings on change
    )

    bpy.types.Scene.texture_settings = bpy.props.CollectionProperty(type=PhotoStackProperties)


def unregister():
    if hasattr(keymaps, 'unregister'):
        keymaps.unregister()
    for cls in reversed(classes):
        if hasattr(bpy.types, cls.__name__):
            bpy.utils.unregister_class(cls)
    bpy.types.IMAGE_MT_image.remove(draw_image_editor_button)
    bpy.types.NODE_MT_node.remove(draw_node_editor_button)

    del bpy.types.Scene.my_tool
    del bpy.types.Scene.image_resize_addon_width
    del bpy.types.Scene.image_resize_addon_height
    del bpy.types.Scene.image_resize_addon_percentage
    del bpy.types.Scene.view_mode
    del bpy.types.Scene.texel_density_result
    bpy.types.VIEW3D_PT_tools_brush_color.remove(draw_func)
    del bpy.types.Node.texture_swap_props

    del bpy.types.Scene.num_textures
    del bpy.types.Scene.texture_settings


if __name__ == "__main__":
    register()
