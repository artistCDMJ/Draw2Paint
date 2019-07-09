# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
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




class PAINT_OT_MacroCreateBrush(bpy.types.Operator):
    """Image Brush Scene Setup Macro"""
    bl_idname = "image.create_brush"
    bl_label = "Setup Scene for Image Brush Maker"
    bl_options = { 'REGISTER', 'UNDO' }

    def execute(self, context):

        scene = context.scene
        #add new scene and name it 'Brush'
        bpy.ops.scene.new(type='NEW')
        bpy.context.scene.name = "Brush"
        #add lamp and move up 4 units in z
        bpy.ops.object.light_add( # you can sort elements like this if the code
                                 # is gettings long
          type = 'POINT',
          radius = 1,
          align='VIEW',
          location = (0, 0, 4)
        )
        #add camera to center and move up 4 units in Z
        bpy.ops.object.camera_add(
          align='VIEW',
          enter_editmode=False,
          location=(0, 0, 4),
          rotation=(0, 0, 0)
        )
        #rename selected camera
        bpy.context.object.name="Tex Camera"
        #change scene size to 1K
        bpy.context.scene.render.resolution_x=1024
        bpy.context.scene.render.resolution_y=1024
        bpy.context.scene.render.resolution_percentage = 100
        #save scene size as preset
        bpy.ops.render.preset_add(name = "1K Texture")
        #change to camera view
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                override = bpy.context.copy()
                override['area'] = area
                bpy.ops.view3d.view_camera( )#view3d.view_axis
                break # this will break the loop after it is first ran

        return {'FINISHED'}



#flip horizontal macro
class PAINT_OT_CanvasHoriz(bpy.types.Operator):
    """Canvas Flip Horizontal Macro"""
    bl_idname = "image.canvas_horizontal" 
    bl_label = "Canvas Horizontal"
    bl_options = { 'REGISTER', 'UNDO' }


    def execute(self, context):

        scene = context.scene
        layer = bpy.context.view_layer
        layer.update()

        #toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()


        #flip canvas horizontal
        bpy.ops.transform.resize(value=(1, -1, 1),
        orient_type='GLOBAL',
        orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
        orient_matrix_type='GLOBAL',
        constraint_axis=(False, True, False),
        mirror=True,
        use_proportional_edit=False,
        proportional_edit_falloff='SMOOTH',
        proportional_size=1,
        use_proportional_connected=False,
        use_proportional_projected=False)


        #toggle object to texture
        bpy.ops.paint.texture_paint_toggle()





        return {'FINISHED'}


#--------------------------------flip vertical macro

class PAINT_OT_CanvasVertical(bpy.types.Operator):
    """Canvas Flip Vertical Macro"""
    bl_idname = "image.canvas_vertical" 
    bl_label = "Canvas Vertical"
    bl_options = { 'REGISTER', 'UNDO' }


    def execute(self, context):

        scene = context.scene
        layer = bpy.context.view_layer
        layer.update()

        #toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()

        #flip canvas horizontal
        bpy.ops.transform.resize(value=(-1, 1, 1),
        orient_type='GLOBAL',
        orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
        orient_matrix_type='GLOBAL',
        constraint_axis=(True, False, False),
        mirror=True, use_proportional_edit=False,
        proportional_edit_falloff='SMOOTH',
        proportional_size=1,
        use_proportional_connected=False,
        use_proportional_projected=False)


        #toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()


        return {'FINISHED'}



#--------------------------ccw15

class PAINT_OT_RotateCanvasCCW15(bpy.types.Operator):
    """Image Rotate CounterClockwise 15 Macro"""
    bl_idname = "image.rotate_ccw_15"
    bl_label = "Canvas Rotate CounterClockwise 15"
    bl_options = { 'REGISTER', 'UNDO' }


    def execute(self, context):

        scene = context.scene
        layer = bpy.context.view_layer
        layer.update()

        #toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()

        #rotate canvas 15 degrees left
        bpy.ops.transform.rotate(value=0.261799,
            orient_axis='Z', orient_type='GLOBAL',
            orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
            orient_matrix_type='GLOBAL',
            constraint_axis=(False, False, True), mirror=True,
            use_proportional_edit=False,
            proportional_edit_falloff='SMOOTH', proportional_size=1,
            use_proportional_connected=False,
            use_proportional_projected=False)

        #toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()

        return {'FINISHED'}
    



#--------------------------cw15

class PAINT_OT_RotateCanvasCW15(bpy.types.Operator):
    """Image Rotate Clockwise 15 Macro"""
    bl_idname = "image.rotate_cw_15" 
    bl_label = "Canvas Rotate Clockwise 15"
    bl_options = { 'REGISTER', 'UNDO' }


    def execute(self, context):

        scene = context.scene
        layer = bpy.context.view_layer
        layer.update()

        #toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()

        #rotate canvas 15 degrees left
        bpy.ops.transform.rotate(value=-0.261799,
            orient_axis='Z', orient_type='GLOBAL',
            orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
            orient_matrix_type='GLOBAL',
            constraint_axis=(False, False, True), mirror=True,
            use_proportional_edit=False,
            proportional_edit_falloff='SMOOTH', proportional_size=1,
            use_proportional_connected=False,
            use_proportional_projected=False)

        #toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()




        return {'FINISHED'} 

#---------------------------ccw 90


class PAINT_OT_RotateCanvasCCW(bpy.types.Operator):
    """Image Rotate CounterClockwise 90 Macro"""
    bl_idname = "image.rotate_ccw_90" 
    bl_label = "Canvas Rotate CounterClockwise 90"
    bl_options = { 'REGISTER', 'UNDO' }


    def execute(self, context):

        scene = context.scene
        layer = bpy.context.view_layer
        layer.update()

        #toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()

        #rotate canvas 90 degrees left
        bpy.ops.transform.rotate(value=1.5708,
            orient_axis='Z', orient_type='GLOBAL',
            orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
            orient_matrix_type='GLOBAL',
            constraint_axis=(False, False, True), mirror=True,
            use_proportional_edit=False,
            proportional_edit_falloff='SMOOTH', proportional_size=1,
            use_proportional_connected=False,
            use_proportional_projected=False)

        #toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()




        return {'FINISHED'} 



#-----------------------------------cw 90

class PAINT_OT_RotateCanvasCW(bpy.types.Operator):
    """Image Rotate Clockwise 90 Macro"""
    bl_idname = "image.rotate_cw_90" 
    bl_label = "Canvas Rotate Clockwise 90"
    bl_options = { 'REGISTER', 'UNDO' }


    def execute(self, context):

        scene = context.scene
        layer = bpy.context.view_layer
        layer.update()

        #toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()

        #rotate canvas 90 degrees left
        bpy.ops.transform.rotate(value=-1.5708,
            orient_axis='Z', orient_type='GLOBAL',
            orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
            orient_matrix_type='GLOBAL',
            constraint_axis=(False, False, True), mirror=True,
            use_proportional_edit=False,
            proportional_edit_falloff='SMOOTH', proportional_size=1,
            use_proportional_connected=False,
            use_proportional_projected=False)

        #toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()




        return {'FINISHED'}


#-----------------------------------reload image


class PAINT_OT_ImageReload(bpy.types.Operator):
    """Reload Image Last Saved State"""
    bl_idname = "image.reload_saved_state"
    bl_label = "Reload Image Save Point"
    bl_options = { 'REGISTER', 'UNDO' }


    def execute(self, context):

        layer = bpy.context.view_layer
        layer.update()
        original_type = bpy.context.area.type
        bpy.context.area.type = 'IMAGE_EDITOR'

        #return image to last saved state
        bpy.ops.image.reload()

        bpy.context.area.type = original_type



        return {'FINISHED'} 



#--------------------------------image rotation reset

class PAINT_OT_CanvasResetrot(bpy.types.Operator):
    """Canvas Rotation Reset Macro"""
    bl_idname = "image.canvas_resetrot" 
    bl_label = "Canvas Reset Rotation"
    bl_options = { 'REGISTER', 'UNDO' }


    def execute(self, context):

        scene = context.scene
        layer = bpy.context.view_layer
        layer.update()

        #reset canvas rotation
        bpy.ops.object.rotation_clear()




        return {'FINISHED'} 

#-----------------------------cameraview paint

class PAINT_OT_CameraviewPaint(bpy.types.Operator):

    bl_idname = "image.cameraview_paint" 
    bl_label = "Cameraview Paint"
    bl_options = { 'REGISTER', 'UNDO' }



    def execute(self, context):

        scene = context.scene

        #toggle on/off textpaint

        obj = context.active_object

        if obj:
            mode = obj.mode
            # aslkjdaslkdjasdas
            if mode == 'TEXTURE_PAINT':
                bpy.ops.paint.texture_paint_toggle()

        #save selected plane by rename
        bpy.context.object.name = "canvas"


        #variable to get image texture dimensions - thanks to Mutant Bob http://blender.stackexchange.com/users/660/mutant-bob
        #select_mat = bpy.context.active_object.data.materials[0].texture_slots[0].texture.image.size[:]
        
        #select_mat = []

        for ob in bpy.context.scene.objects:
            for s in ob.material_slots:
                if s.material and s.material.use_nodes:
                    for n in s.material.node_tree.nodes:
                        if n.type == 'TEX_IMAGE':
                            select_mat = n.image.size[:]
                            #print(obj.name,'uses',n.image.name,'saved at',n.image.filepath)

        #add camera
        bpy.ops.object.camera_add(enter_editmode=False,
        align='VIEW',
        location=(0, 0, 0),
        rotation=(0, -0, 0))

        #ratio full
        bpy.context.scene.render.resolution_percentage = 100

        #name it
        bpy.context.object.name = "Camera View Paint"


        #switch to camera view
        bpy.ops.view3d.object_as_camera()

        #ortho view on current camera
        bpy.context.object.data.type = 'ORTHO'
        #move cam up in Z by 1 unit
        bpy.ops.transform.translate(value=(0, 0, 1),
            orient_type='GLOBAL',
            orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
            orient_matrix_type='GLOBAL',
            constraint_axis=(False, False, True),
            mirror=True,
            use_proportional_edit=False,
            proportional_edit_falloff='SMOOTH',
            proportional_size=1,
            use_proportional_connected=False,
            use_proportional_projected=False)



        #switch on composition guides for use in cameraview paint
        #bpy.context.space_data.context = 'DATA'
        bpy.context.object.data.show_composition_thirds = True



        #found on net Atom wrote this simple script

        #image_index = 0

        rnd = bpy.data.scenes[0].render
        rnd.resolution_x, rnd.resolution_y = select_mat
        #bpy.context.object.data.ortho_scale = orthoscale

        rndx = rnd.resolution_x
        rndy = rnd.resolution_y
        #orthoscale = ((rndx - rndy)/rndy)+1


        if rndx >= rndy:
            orthoscale = ((rndx - rndy)/rndy)+1

        elif rndx < rndy:
            orthoscale = 1


        #set to orthographic
        bpy.context.object.data.ortho_scale = orthoscale
        #try to constrain cam to canvas here
        bpy.ops.object.constraint_add(type='COPY_ROTATION')
        bpy.context.object.constraints["Copy Rotation"].target = bpy.data.objects["canvas"]
        
        bpy.context.object.data.show_name = True
        #hide camera itself
        bpy.ops.object.hide_view_set(unselected=False)




        bpy.context.selectable_objects

        #deselect camera
        bpy.ops.object.select_all(action='TOGGLE')
       # bpy.ops.object.select_all(action='TOGGLE')



        #select plane
        bpy.ops.object.select_all(action='DESELECT')
        ob = bpy.data.objects["canvas"]
        bpy.context.view_layer.objects.active = ob
        

        

        #selection to texpaint toggle
        bpy.ops.paint.texture_paint_toggle()




        return {'FINISHED'}



#-----------------------------image save

class PAINT_OT_SaveImage(bpy.types.Operator):
    """Save Image"""
    bl_idname = "image.save_current"
    bl_label = "Save Image Current"
    bl_options = { 'REGISTER', 'UNDO' }


    def execute(self, context):

        scene = context.scene
        layer = bpy.context.view_layer
        layer.update()
        original_type = bpy.context.area.type
        bpy.context.area.type = 'IMAGE_EDITOR'

        #return image to last saved state
        bpy.ops.image.save()

        bpy.context.area.type = original_type







        return {'FINISHED'} 




########################################
## panel


class PAINT_OT_ArtistPanel(bpy.types.Panel):
    """A custom panel in the viewport toolbar"""
    bl_label = "2D Painter"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Artist Macros"

    def draw(self, context):
        layout = self.layout

        row = layout.row()

        row.label(text="Image State")

        row = layout.row()
        #bpy.ops.import_image.to_plane()
        row.operator("import_image.to_plane", text = "Image to plane", icon = 'IMAGE_PLANE')

        row = layout.row()
        row.operator("image.reload_saved_state", text = "Reload Image", icon = 'IMAGE')

        row = layout.row()
        row.operator("image.save_current", text = "Save Image", icon = 'FILE_IMAGE')


        row = layout.row()

        row.label(text="Flip")

        row = layout.row()
        row.operator("image.canvas_horizontal", text = "Canvas Flip Horizontal", icon = 'TRIA_RIGHT')

        row = layout.row()
        row.operator("image.canvas_vertical", text = "Canvas Flip Vertical", icon = 'TRIA_UP')


        row = layout.row()

        row.label(text="Special Macros")



        '''row = layout.row()
        row.operator("image.canvas_shadeless", text = "Shadeless Canvas", icon = 'EMPTY_SINGLE_ARROW')'''

        row = layout.row()
        row.operator("image.cameraview_paint", text = "Camera View Paint", icon = 'OUTLINER_OB_CAMERA')

        row = layout.row()
        row.operator("image.create_brush", text = "Brush Maker Scene", icon = 'GPBRUSH_INK')

        '''row = layout.row()
        row.operator("image.mirror_canvas", text = "Mirror Canvas Paint", icon = 'EMPTY_SINGLE_ARROW')'''

        row = layout.row()

        row.label(text="Rotation")


        row = layout.row()
        row.operator("image.rotate_ccw_15", text = "Rotate 15 CCW", icon = 'TRIA_LEFT')

        row = layout.row()
        row.operator("image.rotate_cw_15", text = "Rotate 15 CW", icon = 'TRIA_RIGHT')

        row = layout.row()
        row.operator("image.rotate_ccw_90", text = "Rotate 90 CCW", icon = 'TRIA_LEFT_BAR')

        row = layout.row()
        row.operator("image.rotate_cw_90", text = "Rotate 90 CW", icon = 'TRIA_RIGHT_BAR')

        row = layout.row()
        row.operator("image.canvas_resetrot", text = "Reset Rotation", icon = 'RECOVER_LAST')

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
