# Draw2Paint Macros
This is an add-on for 3.1 series Blender to enable manipulation of images using the Images as Planes add-on.
The panel can be found in the N panel once installed, and the plane must be in Texture Paint mode to begin work.
**Image State Tools**

**New Image** - this will draw a new 2D Editor and a New Image to be set up to save to file directory

**Load Canvas** - this will call the Import Images as Planes addon and allow you to go find your initial image to paint on - I suggest keeping a few different sizes for painting on.

**Camera View Paint** - this is the creation of the main camera and the rename of the initial image to 'canvas', as well as set up in the background of the main scene settings to improve the experience.

**Reload Image** - does just that, the button swaps to the image editor in the background and reloads the current image, abandoning the changes made.

**Save Image** - does exactly that, saves the current state of the painted image.

**Save Increment** - not ready, but is wip.

**Grease Pencil Shorts**

**New GPencil** - this one is new, adds a GPencil Object to the View to enable painting with GPencil on the active painting. To get that into the canvas permanently, you need to render with F12, save, and reconnect the new image to the Canvas Object. More to come with this as I experiment. 

**Canvas Controls**

**Flip X and Flip Y** - both scale the image on axis to get your eye aware of imbalanced composition

**15 CCw and 15 CW** - rotates the image plane on Z axis in 15 degree increments so that you can apply strokes comfortably in any direction needed*

**90 CCW and 90 CW** - rotates the iamge plane by 90 degrees for the same reason as previous set*
* only in non-camera view

**Reset Rotation** - brings the image plane back to original position, but will not resolve X or Y Flips

**Guide Controls**

**Guide** - while canvas is selected, this creates an Empty controller for placement as a pivot for origin. Place the created empty, and then re-press the Guide button to assign that location as the Image Pivot. Turn on X and/or Y Symmetry underneath and painting will act on the controller position. To replace the controller and reset the image pivot, press **Recenter Guide**. Hide or Delete the Guide controller depending on personal preference.

**Mask Controls**
Align Selected Mask Objects - icons indicate the relation the selected masks should reflect once pressed

Map and Apply Material to Mask

**(Re)Project** - with a mask object (closed)selected, you can use this to apply an UV Project from View through the camera view - NOTE: Press 2X if the image doesn't appear to have changed

**Subtract Masks** - a Boolean Difference of two selected mask planes/objects

**Join Masks** - a Boolean Union of two selected mask planes/objects

**Remove Mods** - this removes the modifiers left over from boolean ops

Draw and Modify Masks

**Draw Curve** - automates going into curve drawing mode by adding a curve and setting the draw tool, draw a shape and it 'should' close itself, and you can press (Re)Project and Copy Canvas to set as a Mask, or Holdout to create transparent areas

**Draw Vector** - similar, but a vector handle two control points to draw a shape manually.You can press (Re)Project and Copy Canvas to set as a Mask, or Holdout to create transparent areas

**Draw Square** - same, but a closed square curve object to scale up or down with. You can press (Re)Project and Copy Canvas to set as a Mask, or Holdout to create transparent areas

**Draw Circle** -same, but a closed circle curve object to scale up or down with. You can press (Re)Project and Copy Canvas to set as a Mask, or Holdout to create transparent areas

**Copy Canvas** - copies the Canvas Material onto what is selected, useful for setting masks up before (Re)Project

**Holdout** - sets a Holdout Shader to whatever is selected so areas appear to be transparent for prep before camera render

**Face Mask Groups**

**FMG+** -generate face mask groups from islands (based on vertex groups, just renamed for context in painting)

Select, Deselect, Set(assign) and Unset(unassign) Face Mask groups based on selections in Texture Paint while using Face Select Masking
Workflow is apparent when using 3d projection paint on complex mesh object and wanting to Fill tool areas quickly for blockout - Generate the new groups and then you can toggle through to mask them while painting with Face Select Masking on.

**Sculpt 2D Controls**

Copy, Erase and Liquid Sculpt

**Copy and Erase** - makes a copy of the canvas and lifts in Z axis, made to be single user and texpaint brush Eraser is active for painting out everything not intended on being manipulated for liquidsculpt

**Liquid Sculpt** - subdivides the canvas copy and enters Sculpt mode with the Grab brush active for manipulating the image position, stretching and shrinking the pixels

**Scene and Sculpt Extras**

Create Scenes for Brush/Sculpt Extras

**Create Brush/Mask** - setup for a brush specific scene,broken, WIP

**Sculpt Ref** - scene for setting up sculpt References, broken, WIP

**Sculpt Camera** - setup of Sculpt ref Camera, broken, WIP

**Slow Play** - broken, WIP

Extras for 3D Paint

**Align to Face** - selecting a face on a 3d model in Texpaint, this 'should' align the view to the selection





![screen_3 4 0_draw2paint](https://user-images.githubusercontent.com/16747273/161315004-19e0567e-5e09-47b5-9f08-d355775f421f.png)

