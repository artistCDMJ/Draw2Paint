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
    """Flip the Canvas Left/Right"""
    bl_idname = "image.canvas_horizontal" 
    bl_label = "Canvas Horizontal"
    bl_options = { 'REGISTER', 'UNDO' }
    
    @classmethod
    def poll(self, context):
        obj =  context.active_object
        A = obj is not None
        if A:
            B = obj.type == 'MESH'
            return B

    def execute(self, context):

        scene = context.scene
        layer = bpy.context.view_layer
        layer.update()

        #toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()
        
        scene = bpy.context.scene

        original_area = bpy.context.area.type


        #toggle edit mode
        bpy.ops.object.editmode_toggle()
        
        #####select all mesh
        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action='SELECT')
        
        ####change editor to UV Editor
        bpy.context.area.ui_type = 'UV'
        
        
        #+ select the uvs
        bpy.ops.uv.select_all(action='SELECT')
        bpy.ops.uv.select_all(action='SELECT')


        ######scale -1 on axis
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
        
        #back to Object mode
        bpy.ops.object.editmode_toggle()


        #####return to original window editor
        bpy.context.area.type = original_area

        bpy.ops.paint.texture_paint_toggle()


        return {'FINISHED'}


#--------------------------------flip vertical macro

class PAINT_OT_CanvasVertical(bpy.types.Operator):
    """Flip the Canvas Top/Bottom"""
    bl_idname = "image.canvas_vertical" 
    bl_label = "Canvas Vertical"
    bl_options = { 'REGISTER', 'UNDO' }

    @classmethod
    def poll(self, context):
        obj =  context.active_object
        A = obj is not None
        if A:
            B = obj.type == 'MESH'
            return B

    def execute(self, context):

        scene = context.scene
        layer = bpy.context.view_layer
        layer.update()

        #toggle texture mode / object mode
        bpy.ops.paint.texture_paint_toggle()
        
        scene = bpy.context.scene

        original_area = bpy.context.area.type


        #toggle edit mode
        bpy.ops.object.editmode_toggle()
        
        #####select all mesh
        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action='SELECT')
        
        ####change editor to UV Editor
        bpy.context.area.ui_type = 'UV'
        
        
        #+ select the uvs
        bpy.ops.uv.select_all(action='SELECT')
        bpy.ops.uv.select_all(action='SELECT')


        ######scale -1 on axis
        bpy.ops.transform.resize(value=(1, -1, 1),
            orient_type='GLOBAL',
            orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
            orient_matrix_type='GLOBAL',
            constraint_axis=(True, False, False),
            mirror=True, use_proportional_edit=False, 
            proportional_edit_falloff='SMOOTH',
            proportional_size=1,
            use_proportional_connected=False,
            use_proportional_projected=False)
        
        #back to Object mode
        bpy.ops.object.editmode_toggle()


        #####return to original window editor
        bpy.context.area.type = original_area

        bpy.ops.paint.texture_paint_toggle()


        return {'FINISHED'}



#--------------------------ccw15

class PAINT_OT_RotateCanvasCCW15(bpy.types.Operator):
    """Rotate Image CounterClockwise 15 degrees"""
    bl_idname = "image.rotate_ccw_15"
    bl_label = "Canvas Rotate CounterClockwise 15"
    bl_options = { 'REGISTER', 'UNDO' }
    
    @classmethod
    def poll(self, context):
        obj =  context.active_object
        A = obj is not None
        if A:
            B = obj.type == 'MESH'
            return B

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
    """Rotate Image Clockwise 15 degrees"""
    bl_idname = "image.rotate_cw_15" 
    bl_label = "Canvas Rotate Clockwise 15"
    bl_options = { 'REGISTER', 'UNDO' }
    
    @classmethod
    def poll(self, context):
        obj =  context.active_object
        A = obj is not None
        if A:
            B = obj.type == 'MESH'
            return B

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
    """Rotate Image CounterClockwise 90 degrees"""
    bl_idname = "image.rotate_ccw_90" 
    bl_label = "Canvas Rotate CounterClockwise 90"
    bl_options = { 'REGISTER', 'UNDO' }
    
    @classmethod
    def poll(self, context):
        obj =  context.active_object
        A = obj is not None
        if A:
            B = obj.type == 'MESH'
            return B

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
    """Rotate Image Clockwise 90 degrees"""
    bl_idname = "image.rotate_cw_90" 
    bl_label = "Canvas Rotate Clockwise 90"
    bl_options = { 'REGISTER', 'UNDO' }
    
    @classmethod
    def poll(self, context):
        obj =  context.active_object
        A = obj is not None
        if A:
            B = obj.type == 'MESH'
            return B

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
    
    @classmethod
    def poll(self, context):
        obj =  context.active_object
        A = obj is not None
        if A:
            B = obj.type == 'MESH'
            return B

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
    """Reset Canvas Rotation"""
    bl_idname = "image.canvas_resetrot" 
    bl_label = "Canvas Reset Rotation"
    bl_options = { 'REGISTER', 'UNDO' }
    
    @classmethod
    def poll(self, context):
        obj =  context.active_object
        A = obj is not None
        if A:
            B = obj.type == 'MESH'
            return B

    def execute(self, context):

        scene = context.scene
        layer = bpy.context.view_layer
        layer.update()

        #reset canvas rotation
        bpy.ops.object.rotation_clear()




        return {'FINISHED'} 


#-----------------------------cameraview paint

class PAINT_OT_CameraviewPaint(bpy.types.Operator):
    """Set up Camera to match and follow Canvas"""
    bl_idname = "image.cameraview_paint" 
    bl_label = "Cameraview Paint"
    bl_options = { 'REGISTER', 'UNDO' }

    
    @classmethod
    def poll(self, context):
        obj =  context.active_object
        A = obj is not None
        if A:
            B = obj.type == 'MESH'
            return B

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
    
    @classmethod
    def poll(self, context):
        obj =  context.active_object
        A = obj is not None
        if A:
            B = obj.type == 'MESH'
            return B

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

#-----------------------------image save

class PAINT_OT_ResetOrigin(bpy.types.Operator):
    """Reset Canvas Origin"""
    bl_idname = "image.reset_origin"
    bl_label = "Reset Origin"
    bl_options = { 'REGISTER', 'UNDO' }

    
    @classmethod
    def poll(self, context):
        obj =  context.active_object
        A = obj is not None
        if A:
            B = obj.type == 'MESH'
            return B
        
    def execute(self, context):

        scene = context.scene
        layer = bpy.context.view_layer
        layer.update()
        
        bpy.ops.paint.texture_paint_toggle()

        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS',
         center='MEDIAN')

        bpy.ops.paint.texture_paint_toggle()



        return {'FINISHED'}
    
class PAINT_OT_MoveOrigin(bpy.types.Operator):
    """Move Canvas Origin"""
    bl_idname = "image.move_origin"
    bl_label = "Move Origin"
    bl_options = { 'REGISTER', 'UNDO' }
    
    @classmethod
    def poll(self, context):
        obj =  context.active_object
        A = obj is not None
        if A:
            B = obj.type == 'MESH'
            return B

    def execute(self, context):

        scene = context.scene
        layer = bpy.context.view_layer
        layer.update()
        
        bpy.ops.paint.texture_paint_toggle()###to object mode
        
        #bpy.ops.view3d.snap_cursor_to_selected()

        #to set the origin to the cursor
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')


        bpy.ops.paint.texture_paint_toggle()###back to texpaint



        return {'FINISHED'}


#-----------------------------------reload image


class PAINT_OT_EmptyGuides(bpy.types.Operator):
    """experimental- create new empty guide or selected guide relocates origin"""
    bl_idname = "image.empty_guides"
    bl_label = "Empty Guides Constrained"
    bl_options = { 'REGISTER', 'UNDO' }
    
    @classmethod
    def poll(self, context):
        obj =  context.active_object
        A = obj is not None
        if A:
            B = obj.type == 'MESH' or 'EMPTY'
            return B

    def execute(self, context):
        
        scene = context.scene
        layer = bpy.context.view_layer
        layer.update()
        
        #toggle texpaint and deselect
        obj = context.active_object
        
        if obj == bpy.data.objects['canvas']:
            bpy.ops.paint.texture_paint_toggle()
            bpy.ops.object.select_all(action='DESELECT')
            #need check here for ['Symmetry Guide']
            
            for ob in bpy.data.objects:
                if ob.type == 'EMPTY' and ob.name == 'Symmetry Guide':
                    #need to set the sym empty as active
                    bpy.ops.object.select_all(action='DESELECT')
                    bpy.data.objects['Symmetry Guide'].select_set(True)
                    #need to snap cursor to it
                    bpy.ops.view3d.snap_cursor_to_selected()
                    #need to set the canvas as active again
                    bpy.data.objects['Symmetry Guide'].select_set(False)
                    bpy.data.objects['canvas'].select_set(True)
                    
                    pass
                else:                  
                    #add empty here
                    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))#add empty for reference and movement of origin
                    #rename new empty to Symmetry Guide
                    bpy.context.object.name = "Symmetry Guide"

                    bpy.ops.transform.resize(value=(10, 10, 10)) #scale up past the normal range of image plane
                    #add constraint to follow canvas rotation
                    bpy.ops.object.constraint_add(type='COPY_ROTATION')
                    bpy.context.object.constraints["Copy Rotation"].target = bpy.data.objects["canvas"]
                    #snap cursor to empty
                    bpy.ops.view3d.snap_cursor_to_selected()
                                
                    bpy.ops.object.select_all(action='DESELECT')
                    bpy.data.objects['Symmetry Guide'].select_set(False)
                    bpy.data.objects['canvas'].select_set(True)
                    bpy.context.view_layer.objects.active = bpy.data.objects['canvas']

                    bpy.ops.paint.texture_paint_toggle()
                    
                    
                    return {'FINISHED'}
        
        
         
        elif obj == bpy.data.objects['Symmetry Guide']:
            #already have empty, will work for cursors :D
            bpy.ops.view3d.snap_cursor_to_selected()
            
            #here to set origin of canvas
            bpy.ops.object.select_all(action='DESELECT')
            bpy.data.objects['Symmetry Guide'].select_set(False)
            bpy.data.objects['canvas'].select_set(True)
            bpy.context.view_layer.objects.active = bpy.data.objects['canvas']
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
            #bpy.ops.object.select_all(action='DESELECT')
            bpy.data.objects['canvas'].select_set(False)
            bpy.data.objects['Symmetry Guide'].select_set(True)
            


            #bpy.ops.paint.texture_paint_toggle()
            
            
            return {'FINISHED'}
        else:
            return {'FINISHED'}
        
        return {'FINISHED'} 


########################################
## panel

class UI_PT_ImageState(bpy.types.Panel):
    """Image State Tools"""
    bl_label = "Image State Tools"
    bl_idname = "UI_PT_ImageState"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "2D Painter"
    bl_options = {'DEFAULT_CLOSED'}

    #expanded = BoolProperty()

    def draw(self, context):
        sce = context.scene
        layout = self.layout
        ob = context.active_object

        col = layout.column(align=True)
        col.operator("import_image.to_plane", text="Load Canvas", icon = 'IMAGE_PLANE')
        col.operator("image.reload_saved_state", text="Reload Image", icon = 'IMAGE')
        col.operator("image.save_current", text="Save Image", icon = 'FILE_IMAGE')

class UI_PT_FlipRotate(bpy.types.Panel):
    """Flip and Rotate the Canvas"""
    bl_label = "Flip and Rotate Tools"
    bl_idname = "UI_PT_FlipRotate"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "2D Painter"
    bl_options = {'DEFAULT_CLOSED'}

    #expanded = BoolProperty()


    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=True, align=False)
        col = flow.column()
        col.operator("image.canvas_horizontal", text = "Flip X", icon = 'TRIA_RIGHT')
        col = flow.column()
        col.operator("image.canvas_vertical", text = "Flip Y", icon = 'TRIA_UP')
        col = flow.column()
        col.operator("image.rotate_ccw_15", text = "15 CCW", icon = 'TRIA_LEFT')
        col = flow.column()
        col.operator("image.rotate_cw_15", text = "15 CW", icon = 'TRIA_RIGHT')
        col = flow.column()
        col.operator("image.rotate_ccw_90", text = "90 CCW", icon = 'TRIA_LEFT_BAR')
        col = flow.column()
        col.operator("image.rotate_cw_90", text = "90 CW", icon = 'TRIA_RIGHT_BAR')
        
        row = layout.row()
        row.operator("image.canvas_resetrot", text = "Reset Rotation", icon = 'RECOVER_LAST')                   
        
        


class PAINT_PT_SpecialMacros(bpy.types.Panel):
    """A custom panel in the viewport toolbar"""
    bl_label = "Experimental Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "2D Painter"
    bl_options = {'DEFAULT_CLOSED'}

    

        
    def draw(self, context):
        layout = self.layout

        row = layout.row()


        row.label(text="Camera Specials")

        row = layout.row()
        row.operator("image.empty_guides", text = "Guide", icon = 'ORIENTATION_CURSOR')
        
        tool_settings = context.tool_settings
        ipaint = tool_settings.image_paint

        split = layout.split()

        col = split.column()
        col.alignment = 'RIGHT'
        col.label(text="Mirror")

        col = split.column()

        row = col.row(align=True)
        row.prop(ipaint, "use_symmetry_x", text="X", toggle=True)
        row.prop(ipaint, "use_symmetry_y", text="Y", toggle=True)
        row.prop(ipaint, "use_symmetry_z", text="Z", toggle=True)  

        row = layout.row()
        row.operator("image.cameraview_paint", text = "Camera View Paint", icon = 'CAMERA_STEREO')

        row = layout.row()
        row.operator("image.create_brush", text = "Brush Maker Scene", icon = 'BRUSH_DATA')

        
classes = (
            PAINT_PT_SpecialMacros,
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
            PAINT_OT_EmptyGuides,
            UI_PT_ImageState,
            UI_PT_FlipRotate,
            
)

register, unregister = bpy.utils.register_classes_factory(classes)

if __name__ == '__main__':
    register()
