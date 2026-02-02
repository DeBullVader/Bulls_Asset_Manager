# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.




bl_info = {
    "name": "bulltools_asset_manager",
    "description": "asset manager",
    "author": "DeBullVader",
    "version": (0, 0, 1),
    "blender": (4, 2, 0),
    "location": "VIEW3D",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "https://github.com/DeBullVader/BU_Blender_AssetLibrary_Plugin/issues",
    "category": "Tools",
}

from importlib import reload
from . import addon_updater_ops
from bpy.types import AddonPreferences
from . import lib_preferences


import bpy
# from . import dependencies
from . import icons
from . import utils
from . import core_tools
from . import BT_main_panels
  
@addon_updater_ops.make_annotations

class AddonUpdate(AddonPreferences):
  bl_idname = __package__

  get_dev_updates= bpy.props.BoolProperty(
  name="Get development releases(USE AT OWN RISK!)",
  description="Only used to get development branches, wich are not production ready. USE AT OWN RISK!",
  default=False
      )

  auto_check_update= bpy.props.BoolProperty(
  name="Auto-check for Update",
  description="If enabled, auto-check for updates using an interval",
  default=False)

  updater_interval_months= bpy.props.IntProperty(
  name='Months',
  description="Number of months between checking for updates",
  default=0,
  min=0)

  updater_interval_days= bpy.props.IntProperty(
  name='Days',
  description="Number of days between checking for updates",
  default=7,
  min=0,
  max=31)

  updater_interval_hours= bpy.props.IntProperty(
  name='Hours',
  description="Number of hours between checking for updates",
  default=0,
  min=0,
  max=23)

  updater_interval_minutes= bpy.props.IntProperty(
  name='Minutes',
  description="Number of minutes between checking for updates",
  default=0,
  min=0,
  max=59)

class AllPrefs(
  lib_preferences.BUPrefLib,
  AddonUpdate,
  ):

  bl_idname = __package__

class BUProperties(bpy.types.PropertyGroup):
  progress_total: bpy.props.FloatProperty(default=0, options={"HIDDEN"})  
  progress_percent: bpy.props.IntProperty(
      default=0, min=0, max=100, step=1, subtype="PERCENTAGE", options={"HIDDEN"}
  )
  progress_word: bpy.props.StringProperty(options={"HIDDEN"})  
  progress_downloaded_text: bpy.props.StringProperty(options={"HIDDEN"})
  assets_to_upload: bpy.props.IntProperty(default = 0, options={"HIDDEN"})
  new_assets: bpy.props.IntProperty(default = 0, options={"HIDDEN"})
  updated_assets: bpy.props.IntProperty(default = 0, options={"HIDDEN"})
  addon_name: bpy.props.StringProperty(options={"HIDDEN"})

classes = (BUProperties,AllPrefs)


packages=[
    utils,
    BT_main_panels,
    icons,
    core_tools,

]

def register():
  addon_updater_ops.register(bl_info)
  addon_updater_ops.make_annotations(AddonUpdate)
  for cls in classes:
    bpy.utils.register_class(cls)



  for module in packages:
    module.register()
    
  bpy.types.WindowManager.bu_props = bpy.props.PointerProperty(type=BUProperties)
  bpy.context.preferences.use_preferences_save = True


  addon_prefs =  bpy.context.preferences.addons[__package__].preferences

    
def unregister():
  addon_updater_ops.unregister()
  for cls in classes:
    bpy.utils.unregister_class(cls)

  for module in reversed(packages):
    module.unregister()
  
  del bpy.types.WindowManager.bu_props

if __name__ == "__main__":
    register()

