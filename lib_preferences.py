from . import addon_updater_ops
import bpy
from bpy.types import AddonPreferences
from bpy.props import (
    BoolProperty,
    StringProperty
)

def save_prefs(self, context):
    bpy.ops.wm.save_userpref()

class BUPrefLib(AddonPreferences):
    bl_idname = __package__

    lib_path: StringProperty(
        name = "AssetLibrary directory",
        description = "Choose a directory to setup the Asset Library",
        maxlen = 1024,
        subtype = 'DIR_PATH',
        
        default="B:\\BullTools\\Asset_lib"


    )

    lock_path:BoolProperty(name="Lock", default=False)

    new_lib_path: StringProperty(
        name = "New AssetLibrary directory",
        description = "Choose a new directory for the asset library",
        maxlen = 1024,
        subtype = 'DIR_PATH',
        
    )

    enable_custom_thumnail_path: BoolProperty(
        name="Enable custom thumbnail path",
        description="Enable custom thumbnail path for assets to upload",
        default=False,
        
    )

    thumb_path: StringProperty(
        name = "Path to thumbs folder",
        description = "Choose a new directory for the asset library",
        maxlen = 1024,
        subtype = 'DIR_PATH',
        

    )


    author: StringProperty(
        name = "Author",
        description = "Author of the asset",
        maxlen = 1024,
        
    )
  
    toggle_info_panel: BoolProperty(
        name="Toggle Info Panel",
        description="Toggle Info Panel",
        default=False,
       
    )

    toggle_documentation_panel: BoolProperty(
        name="Toggle Documentation Panel",
        description="Toggle Documentation Panel",
        default=False,
        
    )

    toggle_addon_updater: BoolProperty(
        name="Toggle Addon Updater",
        description="Toggle Addon Updater",
        default=False,
        
    )


    toggle_all_addon_settings: BoolProperty(
        name="Toggle BU Asset Browser settings",
        description="Toggle BU Asset Browser settings",
        default=False,
        
    )

    def draw(self,context):
        layout = self.layout
        layout.label(text='Addon Settings')
        layout.separator(factor = 1)
        addon_updater_ops.update_settings_ui(self,context)