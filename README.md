# Draw2Paint Macros
This is an add-on for 4.2 series Blender to enable manipulation of images the new inbuilt image.import_as_mesh_planes.
The panel can be found in the N panel once installed, and the plane must be in Texture Paint mode to begin work.
**Image State Tools**

New Version Here!

**New Image** 
popup image editor for creating a new canvas image, open the Tool Bar to Create Panel to generate a Canvas and Camera from the new image

**+Scene** 
a clean new scene for working outside of your regular 3d file

**Canvas and Camera** 
if an image already exists in the file and is active, this will generate a Canvas and Camera for you

**Camera from Canvas** 
this is if you delete the camera by accident, new camera set to the selected iamge plane/canvas

**Display Active Slot** 
A pop-up Image Editor that is already displaying the current active paint slot - useful for creating iterations of brush images or isolating the details for examination

**Reload**
reload the image

**Save** 
saves the image to previous disk location

**Save+1** 
iteration of the image save to disk location

**Save All Pack All** 
this will attempt to save the images in the file that have been painted, or pack them to file if they haven't been saved to disk, saving then keeps the changes in the packed images.

**Canvas Controls**

**Flip X/ Flip Y** 
these flip the canvas image on UV scaled to X or Y for checking composition

**Rotate Canvas**
this rotates the canvas on the Z xis while still in Texture Paint Mode, and the icon to the right will reset rotation.

**Crop PRBA** 
this is a panel of crop controls for the image in the camera view, shamelessly stolen from Lapineige tools

**3D Image Editor Work**

**Subject to Canvas** 
select your model to be texture painted, and press this to add a new Canvas and Camera linked to share the Subject's material, UV Map is sent to the Camera foreground

**Show Canvas/Show Subject**  
press this to toggle view and render between the Canvas View collection and the Subject View collection. Using this will help with masking, rotating, and even adding objects to the surface of the Canvas. TBD: maybe add all secondary objects to Canvas View collection with a button, as in Mask objects and additional 3d elements liek GPencil.

**Toggle UV in Camera** 
this will toggle on and off the UV map in the Camera view over the Canvas

**Guide Controls**
**Guide** 
sets the Empty Guide used for repositiong the Object Center for painting Symmetry, press a second time to reposition the Object Center

**Recenter Guide** 
press to snap the guide and the Obejct Center back to origin

**Sculpt 2D Controls**
**Copy and Erase** 
duplicates trhe canvas and subdivides it, sets an Erase Alpha brush to eliminate unwanted areas for manipulation

**Liquid Sculpt** 
poor man's liquid modifier using Sculpt tool in Blender - comes in handy for fixing errors in paintings

**Grease PEncil Shorts** 
**New GPencil** 
sets a new GPencil in play that is a child of the Canvas, so rotation of the Canvas will rotate the Gpencil

**Mask Controls**
**Draw Curve**
dropdown to choose what type of curve object to generate for making a mask

**Add Mask Object** 
adds the chosen mask object curve type and makes it a Child of the Canvas, so it will follow the rotation while painting

**Subtract Masks** 
difference bool of two masks, it adds a few modifiers to them to allow this

**Join Masks** 
union bool using a few modifiers as well

**Remove Mods** 
this makes the masks into mesh to use with the next step

**Map and Apply Material to Mask**

**(Re)project** 
project/reproject the Mask into the UV Layer of the Canvas throguh the Camera

**Copy Canvas** 
since the Mask Objects from curves already copy the canvas material, this can be used for anything manually added to the Camera View for painting

**Holdout** 
this adds a Holdout Shader to the selected mask object to make cutting out alphas much faster than manually erasing them repeatedly


**Face MAsk Groups**

**Generate FMG from Islands** 
press FMG+ and the groups will popup for selecting the islands of the Subject for using in Face Mask Selection. Selection and Deselection, Set and Remove all work INSIDE TEXTURE PAINT

Mask objects or anything else will need to be arranged with the Align addon that ships with Blender.
Import IMagesw as Planes is no longer necessary here for using Draw2Paint, as this uses a much simpler and direct approach.












**EZPaint Additions** - Press W for the Brush Pop-up, Alt-W for the Texture and Mask Popup, and Shift-W brings up a broken Vert Group and Texture Slot popup. I will be fixing these as I get time.
D toggles Multiply and Add, Alt-D returns to Mix mode - Shift D toggles Screen, Color, and Soft Light. Have Fun.


![new_d2p_061924](https://github.com/artistCDMJ/Draw2Paint/assets/16747273/37fe194c-ee59-49c3-842b-a6c356a48130)





