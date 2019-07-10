# 2d_painter_macros
This is an add-on for 2.8 series Blender to enable manipulation of images using the Images as Planes add-on.
The panel can be found in the N panel once installed, and the plane must be in Texture Paint mode to work.

The Camera View Paint operator will create a camera that is constrained to the rotation of the canvas image, and will be hidden from view so that you can use the rotation buttons by toggling the camera view with numpad 0. This way, you can paint in camera view with the Thirds guides visible, or you can toggle back to top view and rotate to get your stroke lined up for comfort.

Brushmaker scene is for working separately to create alpha brushes inside Blender - this is a personal choice, others might not need this.

Fixed, reworked to use UV scaling on -1 axis to enable the Camera View to use the Flip horizontal and Flip vertical now. :D [Working in Camera View, the Flip Vertical will not appear to work correctly because of the camera constraint. This is a new trial feature, so I need to research the best way to handle this maybe with a toggle button that switches constraint influence or something like that.]

Once I can really isolate the important needed features for this, then I can give better input into streamlining Spirou4D's EZDraw add-on for the 2.8 series. So much has improved in 2.8 as far as UI is concerned, so some of that add-on might not be as needed for most users.

