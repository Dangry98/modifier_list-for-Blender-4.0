import bpy
from bpy.props import *
from bpy.types import Operator
from ... import __package__ as base_package

from ..modifier_categories import ALL_MODIFIERS_NAMES_ICONS_TYPES, HAVE_GIZMO_PROPERTY
from ..utils import get_ml_active_object, assign_gizmo_object_to_modifier


class OBJECT_OT_ml_modifier_add(Operator):
    bl_idname = "object.ml_modifier_add"
    bl_label = "Add Modifier"
    bl_description = ("Hold shift to add the modifier with a gizmo object (for certain modifiers).\n"
                      "\n"
                      "Placement:\n"
                      "Ctrl: world origin.\n"
                      "If in Edit Mode and there is a selection: the average location of "
                      "the selected elements.\n"
                      "Else: active object's origin. \n"
                      "\n"
                      "Alt: add the modifier on all selected objects.")

    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    modifier_type: StringProperty(options={'HIDDEN'})
    after_active: BoolProperty(name="After Active", default=False)
    add_gizmo: BoolProperty(default=False, options={'HIDDEN', 'SKIP_SAVE'})
    use_world_origin: BoolProperty(default=False, options={'HIDDEN', 'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        ob = get_ml_active_object()
        return ob is not None and (ob.library is None or ob.override_library is not None)

    def execute(self, context):
        ob = get_ml_active_object()

        # Store initial active_index
        init_active_mod_index = ob.ml_modifier_active_index

        # Make adding modifiers possible when an object is pinned
        
        ### Draise - Removed for compatibility with 4.0.0

        #override = context.copy()
        #override['object'] = ob

        if self.modifier_type == "AUTO_SMOOTH":
            if context.mode != 'OBJECT':
                bpy.ops.object.modifier_add_node_group("INVOKE_DEFAULT", asset_library_type='ESSENTIALS', asset_library_identifier="", relative_asset_identifier="geometry_nodes\\smooth_by_angle.blend\\NodeTree\\Smooth by Angle")
            else:
                bpy.ops.object.shade_auto_smooth()
            return {'FINISHED'}
        
        if self.modifier_type == "EDIT_MESH":
            bpy.ops.object.edit_mesh_modifier("INVOKE_DEFAULT")
            return {'FINISHED'}
        
        ### Draise - Added the "with" for compatibility with 4.0.0
        try:
            with context.temp_override(id=ob): 
                bpy.ops.object.modifier_add('INVOKE_DEFAULT', type=self.modifier_type)
        except TypeError:
            for mod in ALL_MODIFIERS_NAMES_ICONS_TYPES:
                if mod[2] == self.modifier_type:
                    modifier_name = mod[0]
                    break
            self.report({'ERROR'}, f"Cannot add {modifier_name} modifier for this object type")
            return {'FINISHED'}
        # Non-editable override objects don't support adding modifiers
        except RuntimeError as rte:
            self.report(type={'ERROR'}, message=str(rte).replace("Error: ", ""))
            return {'FINISHED'}

        self.set_modifier_default_settings()

        # Set correct active_mod index
        pinned_modifiers_amount = sum(mod.use_pin_to_last for mod in ob.modifiers)

        max_active_mod_index = len(ob.modifiers) - 1
        ob.ml_modifier_active_index = max_active_mod_index - pinned_modifiers_amount

        # === Add a gizmo object ===
        #added extra check, since sometimes it can give a error, for some reson
        if ob.modifiers:
            mod = ob.modifiers[-1 - pinned_modifiers_amount] 

        if self.add_gizmo and ob.type in {'CURVE', 'FONT', 'LATTICE', 'MESH', 'SURFACE'}:
            if mod.type in HAVE_GIZMO_PROPERTY or mod.type == 'UV_PROJECT':
                placement = 'WORLD_ORIGIN' if self.use_world_origin else 'OBJECT'
                assign_gizmo_object_to_modifier(self, context, mod.name, placement=placement)

        # === Move modifier into place ===
        # This doesn't work with library overrides because the context
        # of the layout can be wrong.
        # layout.context_pointer_set("modifier", active_modifier) is
        # used to set the modifier for the context of the layout and
        # modifier_move_to_index seems to use that modifier in it's poll,
        # instead of the one passed as an argument. And linked modifiers
        # can't be moved.
        if ob.override_library:
            return {'FINISHED'}

        prefs = bpy.context.preferences.addons[base_package].preferences
        move = not self.use_world_origin if prefs.insert_modifier_after_active else self.use_world_origin
        if self.after_active: # Option to override the preference
            move = True

        if move:
            if init_active_mod_index != max_active_mod_index:
                bpy.ops.object.modifier_move_to_index(modifier=mod.name,
                                                      index=init_active_mod_index + 1)
            if init_active_mod_index < max_active_mod_index - 1:
                ob.ml_modifier_active_index = init_active_mod_index + 1

        return {'FINISHED'}

    def invoke(self, context, event):
        self.use_world_origin = event.ctrl
        self.add_gizmo = event.shift
        self.alt = event.alt # NOTE: never used?

        return self.execute(context)

    def set_modifier_default_settings(self):
        mod = get_ml_active_object().modifiers[-1]

        #need to take into account if the object has a pinned modifier
        index = -1
        while mod.use_pin_to_last:
            index -= 1
            mod = get_ml_active_object().modifiers[index]

        mod_type = mod.type         

        prefs = bpy.context.preferences.addons[base_package].preferences
        defaults_group = getattr(prefs.modifier_defaults, mod.type)
        defaults = [(attr, getattr(defaults_group, attr))
                    for attr in defaults_group.__annotations__] 

        for setting, value in defaults:
            # Some setting are synched, so the other one would override
            # the first one. So, only the other should be set, according
            # to the setting that determines which one is used.

            #need to set Geomtry Node Modifier to show_group, since otherwise the New and list UI will not show up
            if mod_type == 'NODES':
                mod.show_group_selector = True

            if mod_type == 'BEVEL':
                offset_type = defaults_group.offset_type

                if setting == "width" and offset_type == 'PERCENT':
                    continue

                if setting == "width_pct" and offset_type != 'PERCENT':
                    continue

            elif mod_type == 'SIMPLE_DEFORM':
                deform_method = defaults_group.deform_method

                if setting == "angle" and deform_method not in {'TWIST', 'BEND'}:
                    continue

                if setting == "factor" and deform_method not in {'TAPER', 'STRETCH'}:
                    continue
        
            setattr(mod, setting, value)
