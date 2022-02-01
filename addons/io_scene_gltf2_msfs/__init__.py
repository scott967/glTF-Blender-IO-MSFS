# glTF-Blender-IO-MSFS
# Copyright (C) 2020-2021 The glTF-Blender-IO-MSFS authors

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import bpy
import inspect
import pkgutil
import importlib
from pathlib import Path

bl_info = {
    "name": "Microsoft Flight Simulator glTF Extension",
    "author": "Luca Pierabella, Wing42, pepperoni505, ronh991, tml1024, and others",
    "description": "This toolkit prepares your 3D assets to be used for Microsoft Flight Simulator",
    "blender": (3, 1, 0),
    "version": (0, 0, 1),
    "location": "File > Import-Export",
    "warning": "This version of the addon is work-in-progress. Don't use it in your active development cycle, as it adds variables and objects to the scene that may cause issues further down the line.",
    "category": "Import-Export",
    "tracker_url": "https://github.com/AsoboStudio/glTF-Blender-IO-MSFS"
}

class MSFS_ExporterProperties(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(
        name='Microsoft Flight Simulator Extensions',
        description='Enable MSFS glTF export extensions',
        default=True
    )

class GLTF_PT_MSFSExporterExtensionPanel(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = ""
    bl_parent_id = "GLTF_PT_export_user_extensions"
    bl_location = "File > Export > glTF 2.0"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        return operator.bl_idname == "EXPORT_SCENE_OT_gltf"

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="MSFS Extensions", icon='TOOL_SETTINGS')

    def draw(self, context):
        props = bpy.context.scene.msfs_exporter_properties

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        layout.prop(props, 'enabled', text="Enabled")


def recursive_module_search(path, root=""):
    for _, name, ispkg in pkgutil.iter_modules([str(path)]):
        if ispkg:
            yield from recursive_module_search(path / name, f"{root}.{name}")
        else:
            yield root, name


def modules():
    for root, name in recursive_module_search(Path(__file__).parent):
        if name in locals():
            yield importlib.reload(locals()[name])
        else:
            yield importlib.import_module(f".{name}", package=f"{__package__}{root}")


classes = []
extension_classes = [MSFS_ExporterProperties]
extension_panels = [GLTF_PT_MSFSExporterExtensionPanel]

# Refresh the list of classes
def update_class_list():
    global classes

    classes = []

    for module in modules():
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) \
                    and module.__name__ in str(obj) \
                    and "bpy" in str(inspect.getmro(obj)[1]):
                classes.append(obj)


def register():
    # Refresh the list of classes whenever the addon is reloaded so we can stay up to date with the files on disk.
    update_class_list()

    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError:
            pass

    for module in modules():
        if hasattr(module, "register"):
            module.register()

    for cls in extension_classes:
        try:
            bpy.utils.register_class(cls)
        except Exception:
            pass

    bpy.types.Scene.msfs_exporter_properties = bpy.props.PointerProperty(type=MSFS_ExporterProperties)


def register_panel():
    # Register the panel on demand, we need to be sure to only register it once
    # This is necessary because the panel is a child of the extensions panel,
    # which may not be registered when we try to register this extension
    for panel in extension_panels:
        try:
            bpy.utils.register_class(panel)
        except Exception:
            pass

    # If the glTF exporter is disabled, we need to unregister the extension panel
    # Just return a function to the exporter so it can unregister the panel
    return unregister_panel


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    for module in modules():
        if hasattr(module, "unregister"):
            module.unregister()

    for cls in extension_classes:
        bpy.utils.unregister_class(cls)


def unregister_panel():
    for panel in extension_panels:
        try:
            bpy.utils.unregister_class(panel)
        except Exception:
            pass

from .io.msfs_export import Export
class glTF2ExportUserExtension(Export):
    def __init__(self):
        # We need to wait until we create the gltf2UserExtension to import the gltf2 modules
        # Otherwise, it may fail because the gltf2 may not be loaded yet
        from io_scene_gltf2.io.com.gltf2_io_extensions import Extension
        self.Extension = Extension
        self.properties = bpy.context.scene.msfs_exporter_properties
