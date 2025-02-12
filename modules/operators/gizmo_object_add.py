from bpy.props import *
from bpy.types import Operator

from ..utils import assign_gizmo_object_to_modifier


class OBJECT_OT_ml_gizmo_object_add(Operator):
    bl_idname = "object.ml_gizmo_object_add"
    bl_label = "Add Gizmo"
    bl_description = ("Add a gizmo object to the modifier.\n"
                      "\n"
                      "Placement:\n"
                      "Shift: 3D Cursor.\n"
                      "Ctrl: world origin.\n"
                      "If in Edit Mode and there is a selection: the average location of "
                      "the selected elements.\n"
                      "Else: active object's origin")
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    modifier: StringProperty()
    placement: EnumProperty(default='NONE', items=(
        ('NONE', 'None', ''),
        ('CURSOR', '3D Cursor', ''),
        ('WORLD_ORIGIN', 'World Origin', ''),
        ('OBJECT', 'Object Origin', ''),
    ),
    options={'HIDDEN', 'SKIP_SAVE'})

    def execute(self, context):
        self.placement = "OBJECT" if self.placement == 'NONE' else self.placement
        assign_gizmo_object_to_modifier(self, context, self.modifier, placement=self.placement)

        return {'FINISHED'}

    def invoke(self, context, event):
        if self.placement == 'NONE':
            if event.shift:
                self.placement = 'CURSOR'
            elif event.ctrl:
                self.placement = 'WORLD_ORIGIN'
            else:
                self.placement = 'OBJECT'

        return self.execute(context)
