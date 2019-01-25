import bpy
from bpy.types import Operator

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

            if mode == 'TEXTURE_PAINT':
                bpy.ops.paint.texture_paint_toggle()

        #save selected plane by rename
        bpy.context.object.name = "canvas"


        #variable to get image texture dimensions - thanks to Mutant Bob
        # http://blender.stackexchange.com/users/660/mutant-bob
        #node solution from batFINGER

        for ob in bpy.context.scene.objects:
            for s in ob.material_slots:
                if s.material and s.material.use_nodes:
                    for n in s.material.node_tree.nodes:
                        if n.type == 'TEX_IMAGE':
                            select_mat = n.image.size[:]
                            #print(obj.name,'uses',n.image.name,
                            #'saved at',n.image.filepath)

        #add camera
        bpy.ops.object.camera_add(view_align=False,
            enter_editmode=False,
            location=(0, 0, 0),
            rotation=(0, 0, 0))
        #ratio full
        bpy.context.scene.render.resolution_percentage = 100

        #name it
        bpy.context.object.name = "Canvas View Paint"

        #switch to camera view
        bpy.ops.view3d.object_as_camera()

        #ortho view on current camera
        bpy.context.object.data.type = 'ORTHO'
        #move cam up in Z by 1 unit
        bpy.ops.transform.translate(value=(0, 0, 1),
            constraint_axis=(False, False, True),
            constraint_orientation='GLOBAL',
            mirror=False,
            proportional='DISABLED',
            proportional_edit_falloff='SMOOTH',
            proportional_size=1)


        #found on net Atom wrote this simple script

        rnd = bpy.data.scenes[0].render
        rnd.resolution_x, rnd.resolution_y = select_mat

        rndx = rnd.resolution_x
        rndy = rnd.resolution_y


        if rndx >= rndy:
            orthoscale = ((rndx - rndy)/rndy)+1

        elif rndx < rndy:
            orthoscale = 1

        bpy.context.object.data.ortho_scale = orthoscale

        bpy.context.selectable_objects

        #deselect camera
        bpy.ops.object.select_all(action='TOGGLE')

        #select plane
        bpy.ops.object.select_all(action='DESELECT')
        ob = bpy.data.objects["canvas"]
        bpy.context.view_layer.objects.active = ob

        #selection to texpaint toggle
        bpy.ops.paint.texture_paint_toggle()

        return {'FINISHED'}
