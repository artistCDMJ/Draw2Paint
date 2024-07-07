# Draw2Paint Macros

This is an add-on for 4.2 series Blender to enable manipulation of images.
The panel can be found in the N panel once installed, and the plane must be in Texture Paint mode to begin work.
New Version Here!

**Image State Tools**

**New Image** 

Popup image editor for creating a new canvas image, open the Tool Bar to Image Panel to generate a Canvas and Camera \
from the new image, or Open an Existing Image. Image DOES NOT HAVE TO BE SAVED TO DISK TO GENERATE, unlike Import \
Images as Planes addon from before the 4.6 version of Draw2Paint. Also: Image Resize by todashuta is incorporated here\
with a small upgrade of adding a Scale Percentage.

**+Scene** 

A clean new scene for working outside of your regular 3d file, this also sets Color Management to optimum settings for\
hand painting textures to get them out flat. Use Emmission shader to deal with rendering GP and other objects into the \
canvas.


**Set Multi Layer View/ Set Single Texture View**

This is a toggle to go back and forth to settings optimum for display of the paint depending on what you are working on.

**Canvas and Camera**

If an image already exists in the file and is active in the Image Editor, this will generate a Canvas and Camera for \
you to work with solo, without being tied to another object. Same as if you were still in the Image Editor, but more \
likely to snap to Camera View immediately.

**Camera from Canvas** 

This is if you delete the camera by accident, the will make a new camera set to the selected image plane/canvas

**Display Active Slot** 

A pop-up Image Editor that is already displaying the current active paint slot - useful for creating iterations of \
brush images or isolating the details for examination, even taking advantage of the Fill Tool Threshold only available \
in the 2D Image Editor :D

**Reload**

Reloads the Active Image from the 3D View

**Save** 

Saves the image to previous disk location from the 3D View

**Save+1** 

Iterates the save to disk, useful for making animated brushes or different versions of brush images or layer painting

**Save All Pack All** 

This will attempt to save the images in the file that have been painted, or pack them to file if they haven't been \
saved to disk, saving then keeps the changes in the packed images.


**Canvas Controls**

**Flip X/ Flip Y** 

These flip the canvas image on UV scaled to X or Y for checking composition - useful when uncertain if forms are aligned

**Rotate Canvas**

Rotates the canvas on the Z xis while still in Texture Paint Mode, and the icon to the right will reset rotation.
TODO: need to set it to ONLY work on the object with suffix '_canvas'

**Crop PRBA** 

A panel of crop controls for the image in the camera view, shamelessly stolen from Lapineige tools

**3D Image Editor Work**

**Subject to Canvas** 

Select your model to be texture painted, and press this to add a new Canvas and Camera linked to share the Subject's \
material, UV Map is sent to the Camera foreground

**Show Canvas/Show Subject** 

Press to toggle view and render between the Canvas View collection and the Subject View collection. Using this will \
help with masking, rotating, and even adding objects to the surface of the Canvas. 
TBD: maybe add all secondary objects to Canvas View collection with a button, as in Mask objects and additional \
3d elements like GPencil

**Toggle UV in Camera**

Toggle on and off the UV Map in the Camera view over the Canvas

**Guide Controls**

**Guide** 

Sets the Empty Guide used for repositioning the Object Center for painting Symmetry, press a second time to reposition \
the Object Center. Symmetry controls are in the upper toolbar by 'Options'

**Recenter Guide** 

Press to snap the guide and the Object Center back to origin

**Sculpt 2D Controls**

**Copy and Erase** 

Duplicates the canvas and subdivides it, sets an Erase Alpha brush to eliminate unwanted areas for manipulation

**Liquid Sculpt** 

Poor Man's liquid modifier using Sculpt tool in Blender - comes in handy for fixing errors in paintings

**Grease Pencil Shorts** 

**New GPencil** 

Sets a new GPencil in play that is a child of the Canvas, so rotation of the Canvas will rotate the Gpencil.
More tools to follow later once I get the hang of incorporating GPencil into the workflow beyond detail and alignment.

**Mask Controls**

**Draw Curve**

Dropdown to choose what type of curve object to generate for making a mask - Curve Bezier, Curve Vector, Circle, Square

**Add Mask Object** 

Adds the chosen mask object curve type and makes it a Child of the Canvas, so it will follow the rotation while painting

**Subtract Masks** 

Difference bool of two masks, it adds a few modifiers to them to allow this

**Join Masks** 

Union bool using a few modifiers as well

**Remove Mods** 

This makes the masks into mesh to use with the next step

**Create UV Mask**

New Feature thanks to stacker on blender.stackexchange

Select your Subject (the object your are going to paint) if it has a UV map that you loaded in Camera, you can press \
this to generate a new flat mesh object that is generated from the UV Map of the Subject. It will align to the lower \
left vertex in Camera View, and you have to be in Canvas View to see it. Scale to match the UV in Camera, and then \
Reproject 2x to begin painting it as a full object mask or use Linked selection to limit to islands. This is a masking \
by UV that has been a requested feature for the 2d editor but we have it in our 3D Image Editor!

**Map and Apply Material to Mask**

**(Re)project**

Project/Reproject the Mask into the UV Layer of the Canvas through the Camera View (Press Twice, sometimes needs extra)

**Copy Canvas**

Since the Mask Objects from curves already copy the canvas material, this can be used for anything manually added \
to the Camera View for painting

**Holdout** 

Adds a Holdout Shader to the selected mask object to make cutting out alphas much faster than manually \
erasing them repeatedly


**Face Mask Groups**

**Generate FMG from Islands** 

press FMG+ and the groups will popup for selecting the islands of the Subject for using in Face Mask Selection. \
Selection and Deselection, Set and Remove all work INSIDE TEXTURE PAINT

Mask objects or anything else will need to be arranged with the Align addon that ships with Blender.
Import Images as Planes is no longer necessary here for using Draw2Paint, as this uses a much simpler and direct \
approach.

**EZPaint Additions** 

Press W for the Brush Pop-up, Alt-W for the Texture and Mask Popup, and Shift-W brings up a \
broken Vert Group and Texture Slot popup. I will be fixing these as I get time.

D toggles Multiply and Add

Alt-D returns to Mix mode

Shift D toggles Screen, Color, and Soft Light. 

**Color Families**
Now we have a button in the Header to the right that will generate a set of color palettes based on the current brush \
color, and they are named by the Hex number of the original color. Easier way to choose relational colors in palettes \
automatically. These are also present in vertex Paint mode.
Have Fun.
![suzanne_painted_up](https://github.com/artistCDMJ/Draw2Paint/assets/16747273/d8841895-66e9-41b5-9868-890b606465ca)


![suzanne_painted_up2](https://github.com/artistCDMJ/Draw2Paint/assets/16747273/8c62bc34-3e85-416a-a080-94af5e6d0ef4)

![](C:\Users\artis\Desktop\D2P Examples\image_editor_d2p.png)






