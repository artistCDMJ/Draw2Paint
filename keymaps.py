import bpy

#############

addon_keymaps = []

# kmi_defs entry: (identifier, key, action, CTRL, SHIFT, ALT, OSKEY , props, nice name)
# props entry: ,((property name, property value), (property name, property value), ...),....
kmi_defs = (

    # Brushes Popup [Image Paint] with: W.
    (('Image Paint', 'EMPTY'), "view3d.brush_popup", 'W', 'PRESS', False, False, False, False, None, "Brushes Popup"),
    # 2D Editor Popup with Active Paint Slot with Shift + Alt + W
    (('Image Paint', 'EMPTY'), "paint.display_active_slot", 'W', 'PRESS', False, True, True, False, None, "2D Editor Popup"),
    # Slots Popup [Image Paint] with: Shift + W.
    (('Image Paint', 'EMPTY'), "view3d.projectpaint", 'W', 'PRESS', False, True, False, False, None, "Slots Popup"),
    # Textures Popup [Image Paint] with: Alt + W.
    (('Image Paint', 'EMPTY'), "view3d.texture_popup", 'W', 'PRESS', False, False, True, False, None, "Textures Popup"),


    # Toggle add/multily modes [Image Paint] with: D.
    (('Image Paint', 'EMPTY'), "paint.toggle_add_multiply", 'D', 'PRESS', False, False, False, False, None, "Toggle add/multiply modes"),
    # Toggle color/soft light modes [Image Paint] with: Ctrl + D
    (('Image Paint', 'EMPTY'), "paint.toggle_color_soft_light_screen", 'D', 'PRESS', False, True, False, False, None, "Toggle color/soft light modes"),
    # Toggle Alpha modes [Image Paint] with: A.
    (('Image Paint', 'EMPTY'), "paint.toggle_alpha_mode", 'A', 'PRESS', False, False, False, False, None, "Toggle Alpha modes"),
    # Re-init Mix mode [Image Paint] with: Alt + D.
    (('Image Paint', 'EMPTY'), "paint.init_blend_mode", 'D', 'PRESS', False, False, True, False, None, "Re-init Mix mode")

)

def Register_Shortcuts():
    addon_keymaps.clear()
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        # for each kmi_def:
        for (spacetype, identifier, key, action, CTRL, SHIFT, ALT, OS_KEY, props, nicename) in kmi_defs:
            if spacetype[0] in bpy.context.window_manager.keyconfigs.addon.keymaps.keys():
                if spacetype[1] in kc.keymaps[spacetype[0]].space_type:
                    km = kc.keymaps[spacetype[0]]
            else:
                km = kc.keymaps.new(name = spacetype[0], space_type = spacetype[1])
            kmi = km.keymap_items.new(identifier, key, action, ctrl=CTRL, shift=SHIFT, alt=ALT, oskey=OS_KEY)
            if props:
                for prop, value in props:
                    setattr(kmi.properties, prop, value)
            addon_keymaps.append((km, kmi))

                    # keymaps
                    
            #Register_Shortcuts()
            

def unregister():
    global addon_keymaps
        # keymaps
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
