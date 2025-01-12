# module_loader.py
import bpy
import os
import inspect
import sys

def import_submodules(package):
    """Import all submodules of a module recursively."""
    submodules = {}
    package_path = os.path.dirname(os.path.abspath(package.__file__))
    for _, name, ispkg in os.walk(package_path):
         for module_name in name:
            if module_name.startswith('_'):
                continue
            
            if module_name.endswith(".py"):
                full_name = package.__name__ + "." + module_name[:-3]
                try:
                    imported_module = __import__(full_name, fromlist=[''])
                    submodules[full_name] = imported_module
                except Exception as e:
                    print(f"Error importing module {full_name}: {e}")
         break
    return submodules

def get_registrable_classes(modules, sub_class, required_vars = ()):
    """Get all classes from modules that inherit from a certain class."""
    classes = []
    for module in modules.values():
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and issubclass(obj, sub_class):
                 valid = True
                 for var in required_vars:
                    if not hasattr(obj, var):
                        valid = False
                        break
                 if valid:
                        classes.append(obj)
    return classes

def unload_uvpm3_modules(globals_dict):
  if "UVPM3_Preferences" in globals_dict:
      del globals_dict["UVPM3_Preferences"]

def register_all(bl_info):
    modules = import_submodules(sys.modules[bl_info["name"]])

    classes = get_registrable_classes(modules, bpy.types.AddonPreferences)
    for cls in classes:
         if hasattr(cls, "bl_idname"):
            bpy.utils.register_class(cls)
            
    classes = get_registrable_classes(modules, bpy.types.PropertyGroup)
    for cls in classes:
        if hasattr(cls, "bl_idname"):
            bpy.utils.register_class(cls)

    classes = get_registrable_classes(modules, bpy.types.Operator)
    for cls in classes:
        if hasattr(cls, "bl_idname"):
            bpy.utils.register_class(cls)

    classes = get_registrable_classes(modules, bpy.types.Panel)
    for cls in classes:
         if hasattr(cls, "bl_idname"):
            bpy.utils.register_class(cls)


    from .register_utils import register_specific
    register_specific(bl_info)

def unregister_all(bl_info):
    modules = import_submodules(sys.modules[bl_info["name"]])
    classes = get_registrable_classes(modules, bpy.types.AddonPreferences)
    for cls in reversed(classes):
         if hasattr(cls, "bl_idname"):
            bpy.utils.unregister_class(cls)

    classes = get_registrable_classes(modules, bpy.types.Panel)
    for cls in reversed(classes):
         if hasattr(cls, "bl_idname"):
            bpy.utils.unregister_class(cls)
    classes = get_registrable_classes(modules, bpy.types.Operator)
    for cls in reversed(classes):
        if hasattr(cls, "bl_idname"):
            bpy.utils.unregister_class(cls)
    classes = get_registrable_classes(modules, bpy.types.PropertyGroup)
    for cls in reversed(classes):
        if hasattr(cls, "bl_idname"):
            bpy.utils.unregister_class(cls)

    from .register_utils import unregister_specific
    unregister_specific(bl_info)