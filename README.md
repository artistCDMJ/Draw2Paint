# Draw2Paint Addon:
**3D-Space Image Editing for Blender**

This is an add-on for 4.2 series Blender to enable manipulation of images. Lots of this spawned from curiosity after \
watching a tutorial on making a custom tool panel by CG Cookie on their youtube channel. Early work was labeled as the \
Artist Paint Panel. then later converted to EZDraw Panel by Spirou4D, and then after the 2.8 series I started from \
scratch to get it working for the 3.x series of Blender. At that time, I came up with the idea of 'Draw2Paint' because \
of the label of the TexDraw Brush had changed to a Draw Tool, and so to paint anything the first step is to  'Press \
DRAW to PAINT', and it stuck. You will probably get tired of seeing the 'this2that' naming but it works well to \
explain the actions the operators are for.

The panel can be found in the N panel once installed.

**Image Creation**

**Image2Scene** 

Popup image editor for creating a new canvas image, open the Tool Bar to Image Panel to generate a Canvas and Camera \
from the new image, or Open an Existing Image. Image DOES NOT HAVE TO BE SAVED TO DISK TO GENERATE, unlike Import \
Images as Planes addon from before the 4.6 version of Draw2Paint. \

NEW: Creates new scene based on image name to allow multiple scenes of painting

Also: Image Resize by todashuta is incorporated herewith a small upgrade of adding a Scale Percentage. \
New Image From Active Image Size was added to the Image Editor Image Menu dropdown, and New Texture Node from Active \
Texture Node was added to the Node dropdown menu in the Shader Editor. \
These seem redundant but actually add new image texture from the active image size, so in the Image Editor we can add \
images that follow the size of the project canvas and not default to 1024x1024 new image. The Node option in the Shader\
 Editor generates a new image texture node that sizes the image based on the active selected image node in the editor. \
This is a life saver because we can't see the size of the image texture in the active node unless we look to the N  \
panel for examining the Properties.



**Set Multi Layer View/ Set Single Texture View**

This is a toggle to go back and forth to settings optimum for display of the paint depending on what you are working on.


**Slot2Display** 

A pop-up Image Editor that is already displaying the current active paint slot - useful for creating iterations of \
brush images or isolating the details for examination, even taking advantage of the Fill Tool Threshold only available \
in the 2D Image Editor :D

**Reload**

Reloads the Active Image from the 3D View

**Save** 

Saves the image to previous disk location from the 3D View

**Save+1** 

Iterates the save to disk, useful for making animated brushes or different versions of brush images or layer painting

**Save/Pack All** 

This will attempt to save the images in the file that have been painted, or pack them to file if they haven't been \
saved to disk, saving then keeps the changes in the packed images.


**Canvas Controls**

**Flip X/ Flip Y** 

These flip the Canvas image on UV scaled to X or Y for checking composition - useful when uncertain if forms are aligned

**Rotate Canvas**

Rotates the Canvas on the Z xis while still in Texture Paint Mode, and the icon to the right will reset rotation.


**Crop2Camera** 

A panel of crop controls for the image in the camera view, shamelessly stolen from Lapineige tools

**3D-2D Image Editor**

**Subject2Canvas** 

Select your model to be texture painted, and press this to add a new Canvas and Camera linked to share the Subject's \
material, UV Map is sent to the Camera foreground and object is renamed (obj.name+_subject), Init is Canvas_view

This also creates a new scene named after the active image node

**Canvas2View/Subject2View** 

Press to toggle view and render between the Canvas View collection and the Subject View collection. Using this will \
help with masking, rotating, and even adding objects to the surface of the Canvas. 
TBD: maybe add all secondary objects to Canvas View collection with a button, as in Mask objects and additional \
3d elements like GPencil

**Toggle UV2Camera**

Toggle on and off the UV Map in the Camera view over the Canvas

**Align2Face**

Select a face or subset of faces in Face Select Masking mode and this will align the view to Top

**Calculate Texel Density**

With object scale applied, this will examine surface area and suggest a power of 2 image texture size

**Symmetry2Guide** Only for canvas_view for now

**Guide2Canvas** 

Sets the Empty Guide used for repositioning the Object Center for painting Symmetry, press a second time to reposition \
the Object Center. Symmetry controls are in the upper toolbar by 'Options'

**Recenter** 

Press to snap the guide and the Object Center back to origin

**PhotoStack Tools**

**PhotoStack**
Add the number of images you want to add in combination with the active image node of the object.

Generate/Extend PhotoStack - adds the number of images based on the count and the size of the active image in the \
active object, and uses a default of 0 alpha and mix blend mode in the color mix nodes. 

To move painted images, we 'swap' them in assignment to the image nodes instead of connecting/disconnecting. \
Select two(2) images in the PhotoStack to Swap them. This is helpful if you have already painted but want to  \
reverse the order.

**Sculpt Canvas Copy** Only for canvas_view for now

**Copy2Eraser** 

Duplicates the canvas and subdivides it, sets an Erase Alpha brush to eliminate unwanted areas for manipulation

**Liquid Sculpt** 

Poor Man's liquid modifier using Sculpt tool in Blender - comes in handy for fixing errors in paintings

**Grease Pencil Tools** 

**GPencil2Canvas** 

Sets a new GPencil in play that is a child of the Canvas, so rotation of the Canvas will rotate the Gpencil.
More tools to follow later once I get the hang of incorporating GPencil into the workflow beyond detail and alignment.

**Mask Creation**

**Curve2Mask**

Dropdown to choose what type of curve object to generate for making a mask - Curve Bezier, Curve Vector, Circle, Square

**Add Mask Object** 

Adds the chosen mask object curve type and makes it a Child of the Canvas, so it will follow the rotation while painting

**Subtract Masks** 

Difference bool of two masks, it adds a few modifiers to them to allow this

**Join Masks** 

Union bool using a few modifiers as well

**Remove Mods** 

This makes the masks into mesh to use with the (Re)project

**UV2Mask**

New Feature thanks to stacker on blender.stackexchange

Select your Subject (the object you're going to paint) if it has a UV map that you loaded in Camera, you can press \
this to generate a new flat mesh object that is generated from the UV Map of the Subject. It will align to the lower \
left vertex in Camera View, and you have to be in Canvas View to see it. Scale to match the UV in Camera, and then \
Reproject 2x to begin painting it as a full object mask or use Linked selection to limit to islands. This is a masking \
by UV that has been a requested feature for the 2d editor but we have it in our 3D Image Editor!

**Trace2Curve**

Experimental for now, this will allow one to autotrace an image plane of high contrast. It uses a ladder of steps to  \
get there, turning an Image Plane into an Image Empty, using Trace to Gpencil and converting the GPencil to Curve. \
A lot going on, so the elements to get there are stuffed into a collection to keep the result separate.
Have Fun.

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
Selection and Deselection, Set and Remove all work INSIDE TEXTURE PAINT - used to have to tab in and out of Edit Mode \
to set new vertex groups by face selection for Face Select Masking. 

Mask objects or anything else will need to be arranged with the Align addon that ships with Blender.
Import Images as Planes is no longer necessary here for using Draw2Paint, as this uses a much simpler and direct \
approach.

**Extras outside the 3D View Panel**

**2Compositor and 2ShaderEditor** 
This is a toggle from the Shader Editor back and forth to the Compositor for the use of the Compositor for Image \
editing with the Composite nodes. 

**Image2Compositor**
This loads a copy of the shader's active image node's image to an image node connected to the Viewer in the \
Compositor node editor. The user can then press 2Compositor to take the next step of adding Filter nodes, Color \
Adjustment nodes, additional images or textures combined with Color Mix nodes and Transform/Scale/Rotate nodes etc.
Presets are going to be made later for some basic effects to apply to the target painting as if using Flash Layer \
Styles. Lots of stuff possible. Edit: added swap editor to automatically take you to Compositor.

**PhotoStack2Compositor**
Similar to Image2Compositor, but this is for a whole group node called the PhotoStack that we can now manipulate \
a way to send the whole lot of images and mix nodes to the Compositor to edit. Automatic editor swap.

**Compositor2Image**
This sends the render of the Viewer node to the C:\tmp\ folder and then loads it into a new image texture node in \
the shader tree. Press 2ShaderEditor to go back and connect the new image node to the shader color input. Might be \
already automatic on the return, I've been adding the operator for swap editor to as much of this as possible.


**New Texture Node from Active Texture**
This will duplicate the size of the image in the active image node to a new generated image node in the Compositor

**New Image from Active Image Size**
This will create a new image texture from the size of the active image in the Image Editor

**EZPaint Additions** 

Press W for the Brush Pop-up that helps as a color wheel tool panel \
Alt-W for the Texture and Mask Popup, can create texture and mask from new image \
and Shift-W brings up a ProjectPaint popup for Vertex Groups and Texture Slots in Material Mode and Single Image for IMage Mode \

D toggles Multiply and Add

Alt-D returns to Mix mode

Shift D toggles Screen, Color, and Soft Light. 

A toggles Erase Alpha/Add Alpha when the Face Select Masking is OFF. If ON, then A defaults to select tool.

'K' Flips Brush Gradient in the active Brush 

**Color Families**
Now we have a button in the Header to the right that will generate a set of color palettes based on the current brush \
color, and they are named by the Hex number of the original color. Easier way to choose relational colors in palettes \
automatically. These are also present in vertex Paint mode.






![d2p_bleeding_4](https://github.com/user-attachments/assets/2d2dcfa6-3e4a-4785-bd6b-cc99019c9c32)
![d2p_bleeding_3](https://github.com/user-attachments/assets/6906e4af-f1c5-48a9-883e-2fc373204d7b)
![d2p_bleeding_2](https://github.com/user-attachments/assets/3dc45ba1-3c13-469b-8700-de420277a279)








