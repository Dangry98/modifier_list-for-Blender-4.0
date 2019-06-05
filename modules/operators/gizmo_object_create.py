from bpy.props import *
from bpy.types import Operator

from ..utils import assign_gizmo_object_to_modifier


class OBJECT_OT_ml_gizmo_object_create(Operator):
    bl_idname = "object.ml_gizmo_object_create"
    bl_label = "Add Gizmo Object"
    bl_description = ("Add a gizmo object to the modifier.\n"
                      "\n"
                      "\u2022 When a single vertex is selected, it is placed at the vertex location.\n"
                      "\u2022 Otherwise it is placed at the origin of the active object")
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    modifier: StringProperty()

    def execute(self, context):
        assign_gizmo_object_to_modifier(self, context, self.modifier)

        return {'FINISHED'}