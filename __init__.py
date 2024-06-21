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
    "author": "CDMJ, Spirou4D, Lapineige, Bart Crouch, batFINGER",
    "version": (4, 0, 6),
    "blender": (4, 2, 0),
    "location": "UI > Draw2Paint",
    "description": "2D Paint in 3D View, Mask Manipulation, EZPaint Adoption",
    "warning": "",
    "category": "Paint",
}


##### imports
import os
import bpy
import bmesh

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
    D2P_OT_SelectedToUVMask,
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
    D2P_OT_InitPaintBlend,
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
    D2P_PT_ImagePlanePanel,
)

def register():
    for cls in classes:
        if hasattr(bpy.types, cls.__name__):
            bpy.utils.unregister_class(cls)
        bpy.utils.register_class(cls)
    bpy.types.Scene.my_tool = bpy.props.PointerProperty(type=properties.D2P_Properties)
    if hasattr(keymaps, 'register'):
        keymaps.register()

def unregister():
    if hasattr(keymaps, 'unregister'):
        keymaps.unregister()
    for cls in reversed(classes):
        if hasattr(bpy.types, cls.__name__):
            bpy.utils.unregister_class(cls)
    del bpy.types.Scene.my_tool

if __name__ == "__main__":
    register()
