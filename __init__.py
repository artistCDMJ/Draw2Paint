bl_info = {
    "name": "2D Painter",
    "author": "CDMJ",
    "version": (3, 0, 0),
    "blender": (2, 80, 0),
    "location": "UI > 2D Painter",
    "description": "Art Macros.",
    "warning": "",
    "category": "Paint",
}
import bpy

from . paint_ot_macrocreatebrush     import PAINT_OT_MacroCreateBrush
from . paint_ot_canvashoriz          import PAINT_OT_CanvasHoriz
from . paint_ot_canvasvertical       import PAINT_OT_CanvasVertical
from . paint_ot_rotatecanvasccw15   import PAINT_OT_RotateCanvasCCW15
from . paint_ot_rotatecanvascw15     import PAINT_OT_RotateCanvasCW15
from . paint_ot_rotatecanvasccw      import PAINT_OT_RotateCanvasCCW
from . paint_ot_rotatecanvascw       import PAINT_OT_RotateCanvasCW
from . paint_ot_imagereload          import PAINT_OT_ImageReload
from . paint_ot_canvasresetrot       import PAINT_OT_CanvasResetrot
from . paint_ot_cameraviewpaint      import PAINT_OT_CameraviewPaint
from . paint_ot_saveimage            import PAINT_OT_SaveImage
from . paint_ot_artistpanel          import PAINT_OT_ArtistPanel



classes = (
            PAINT_OT_ArtistPanel,
            PAINT_OT_MacroCreateBrush,
            PAINT_OT_CanvasHoriz,
            PAINT_OT_CanvasVertical,
            PAINT_OT_RotateCanvasCCW15,
            PAINT_OT_RotateCanvasCW15,
            PAINT_OT_RotateCanvasCCW,
            PAINT_OT_RotateCanvasCW,
            PAINT_OT_ImageReload,
            PAINT_OT_CanvasResetrot,
            PAINT_OT_SaveImage,
            PAINT_OT_CameraviewPaint,
)

register, unregister = bpy.utils.register_classes_factory(classes)

if __name__ == '__main__':
    register()
