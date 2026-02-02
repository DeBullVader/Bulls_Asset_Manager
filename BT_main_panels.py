import bpy
import os
from bpy.types import Context
import textwrap
from .utils import addon_info
from . import addon_updater_ops
from . import icons
from . import bl_info
      

class BU_PT_AddonSettings(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BU_ADDON_SETTINGS"
    bl_label = 'Addon Settings'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_BBPS_MAIN_ADDON_PANEL"
    bl_options = {'DEFAULT_CLOSED'}


    def draw(self,context):  
        self.open_addon_prefs(context)
       
            
    
    def open_addon_prefs(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text="Use the settings in the below panel or in the addon preferences")
        row = layout.row()
        row.operator("bu.open_addon_prefs", text="Addon preferences", icon='PREFERENCES')  

def validate_library_dir(addon_prefs,lib_name):
    if lib_name in bpy.context.preferences.filepaths.asset_libraries:
        lib = bpy.context.preferences.filepaths.asset_libraries[lib_name]
        if lib is not None:
            dir_path,lib_name = os.path.split(lib.path)
            if addon_prefs.lib_path.endswith(os.sep):
                dir_path = dir_path+os.sep
            if not os.path.exists(lib.path):
                return False
            if addon_prefs.lib_path != dir_path:
                return False
            return True
    return False

def validate_bu_library_names(addon_prefs,lib_name):
    if lib_name not in bpy.context.preferences.filepaths.asset_libraries:
        return False
    return True

class Addon_Updater_Panel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_UPDATER"
    bl_label = 'Bullltools Asset Manager Updater'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_BBPS_MAIN_ADDON_PANEL"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw (self, context):
        addon_updater_ops.update_settings_ui(self, context)

    
class BBPS_Info_Panel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BBPS_INFO_PANEL"
    bl_label = 'Bullltools Asset Manager Info'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_BBPS_MAIN_ADDON_PANEL"
    bl_options = {'DEFAULT_CLOSED'}
    

    def draw(self, context):
        addon_prefs = addon_info.get_addon_name().preferences
 
        layout = self.layout
        i = icons.get_icons()
        box = layout.box()
        row = box.row(align = True)
        row.alignment = 'EXPAND'
        version =bl_info['version']
        version_string = '.'.join(map(str, version))
        # print(addon_info.get_addon_name().bl_rna.__dir__())
        row.label(text=f'The Bulltools Asset Manager BETA - Version {version_string}')
        split = box.split(factor=0.66, align=True)
        col = split.column(align=False)
        col.alignment = 'LEFT'
        wrapp = textwrap.TextWrapper(width=int(context.region.width/10))
        bu_info_text = wrapp.wrap(text='This add-on is underconstruction')
        for text_line in bu_info_text:
            col.label(text=text_line)
        col.separator(factor=2)
        

        col = box.column(align=True)
        col.alignment = 'LEFT'
        # youtube = col.operator('wm.url_open',text='Youtube',icon_value=i["youtube"].icon_id)
        discord = col.operator('wm.url_open',text='Discord',icon_value=i["discord"].icon_id)
        twitter_bull = col.operator('wm.url_open',text='DeBullVader',icon_value=i["X_logo_black"].icon_id)
        twitter_pav = col.operator('wm.url_open',text='PolyAssetVault',icon_value=i["X_logo_black"].icon_id)
        # reddit = col.operator('wm.url_open',text='Reddit',icon_value=i["reddit"].icon_id)
        # medium = col.operator('wm.url_open',text='Medium',icon_value=i["medium"].icon_id)     

        discord.url = 'https://discord.gg/SNRnw2VrhR'
        twitter_pav.url = 'https://x.com/PolyAssetVault'
        twitter_bull.url = 'https://x.com/DeBullVader'
        # youtube.url = 'https://www.youtube.com/@blender-universe'
        # reddit.url = 'https://www.reddit.com/user/BakedUniverse/'
        # medium.url = 'https://medium.com/@bakeduniverse'
        

def draw_bu_logo():
    addon_path = addon_info.get_addon_path()
    path = os.path.join(addon_path, 'bull_plugin_assets','images','BT_icon.png')
    img = bpy.data.images.load(path,check_existing=True)
    texture = bpy.data.textures.new(name="BT_Logo", type="IMAGE")
    texture.image = img
    
    return img

class BU_OT_OpenAddonPrefs(bpy.types.Operator):
    """ Open BullTools asset manager Addon Preferences """
    bl_idname = "bu.open_addon_prefs"
    bl_label = "Open Addon Preferences"
    bl_description = "Open Addon Preferences"

    def execute(self, context):
        addon_name = __name__.split('.')[0]
        preferences = bpy.context.preferences
        addon_prefs = preferences.addons[addon_name].preferences

        bpy.ops.screen.userpref_show("INVOKE_DEFAULT")
        addon_prefs.active_section = 'ADDONS'
        bpy.ops.preferences.addon_expand(module = addon_name)
        bpy.ops.preferences.addon_show(module = addon_name)
        return {'FINISHED'}

class BU_OT_Open_N_Panel(bpy.types.Operator):
    """ Open UniBlend Addon Preferences """
    bl_idname = "bu.open_n_panel"
    bl_label = "Opens the N panel"
    bl_description = "Opens the N panel in the 3D View"

    def execute(self, context):
        
        for window in context.window_manager.windows:
            screen = window.screen
            for area in screen.areas:
                if area.type == 'VIEW_3D':
                    with context.temp_override(window=window, area=area):
                        bpy.ops.wm.context_toggle(data_path="space_data.show_region_ui")
        return {'FINISHED'}

class BBPS_Main_Addon_Panel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BBPS_MAIN_ADDON_PANEL"
    bl_label = 'BoolTools'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BullTools'


    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.alignment = 'EXPAND' 
        box = row.box()
        row = box.row(align = True)
        i = icons.get_icons()
        box.template_icon(icon_value=i["BT_Icon"].icon_id, scale=4)
        website =box.operator('wm.url_open',text='PolyAssetVault',icon='URL')
        website.url = 'https://polyassetvault.com/user/69600205099091fe0e3c4dbc'


        wrapp = textwrap.TextWrapper(width=int(context.region.width/6.5))
        box = layout.box()
        row = box.row(align = True)
        row.alignment = 'EXPAND'
        col = row.column(align=True)
        bu_info_text = wrapp.wrap(text='BullTools a collection of tools creators')
        for text_line in bu_info_text:
            col.label(text=text_line)
        
class BU_PT_Docs_Panel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BU_DOCS"
    bl_label = 'Documentation & Getting Started'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_BBPS_MAIN_ADDON_PANEL"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        i = icons.get_icons()
        box = layout.box()        
        # box.label(text='Getting Started',icon='INFO')
        box.label(text='More information will be available soon',icon='INFO')
        # row = box.row(align=True)
        # row.alignment = 'LEFT'
        # row.label(text='Help icon example: ')
        # row.label(text='', icon='HELP')
        # col = box.column(align=True)
        # wrapp = textwrap.TextWrapper(width=int(context.region.width/6))
        # help_icon_text = wrapp.wrap(text='Links to specific add-on functionality pages on gitbook, '
        #                             + 'can be found throughout the add-on with the help icon shown above. '
        #                             + 'More information about the UniBlend add-on can be found on our Gitbook'
        #                             )
        # for line in help_icon_text:
        #     col.label(text=line)
        
        # addon_info.gitbook_link_getting_started(box, 'add-on-settings-initial-setup','Getting Started')
        # addon_info.gitbook_link_getting_started(box, 'copyright-and-asset-license','BU Assets Copyright & License')

        # box = layout.box()
        # box.label(text='Troubleshooting',icon='ERROR')
        # col = box.column(align=True)
        # troubleshoot_text = wrapp.wrap('As we are developing the add-on some scenarios might give errors. '
        #                                +'If this happens please open a ticket on our discord.')
        # for line in troubleshoot_text:
        #     col.label(text=line)
        
        # row = box.row()
        # row.alignment = 'LEFT'
        # discord = row.operator('wm.url_open',text='Discord',icon_value=i["discord"].icon_id)
        # discord.url = 'https://discord.gg/bakeduniverse'
        # col = box.column(align=True)
        # troubleshoot_second_text = wrapp.wrap('You can either open the console and send us a screenshot of the error'
        #                                       +' or send us the error_log.txt file that can be found in the error_logs folder.')
        # for line in troubleshoot_second_text:
        #     col.label(text=line)
        
        box.operator('wm.console_toggle',text='Toggle Console',icon='CONSOLE')
        box.operator('bu.open_error_logs_folder',text='Open Error Logs Folder',icon='TEXT')
        box.operator('bu.open_addon_location',text='Open Addon Install Location',icon='FILE_FOLDER')

class BU_OT_OpenAddonLocation(bpy.types.Operator):
    bl_idname = "bu.open_addon_location"
    bl_label = "Open Addon Location"

    def execute(self, context):
        addon_path = addon_info.get_addon_path()
        os.startfile(addon_path)
        return {'FINISHED'}
    
class BU_OT_OpenErrorLogFolder(bpy.types.Operator):
    bl_idname = "bu.open_error_logs_folder"
    bl_label = "Open error logs folder"

    def execute(self, context):
        addon_path = addon_info.get_addon_path()
        logs_folder = os.path.join(addon_path,'error_logs')
        if not os.path.isdir(logs_folder):
            os.mkdir(logs_folder)
        os.startfile(logs_folder)
        return {'FINISHED'}


classes = (
    BBPS_Main_Addon_Panel,
    BBPS_Info_Panel,
    Addon_Updater_Panel,
    BU_PT_AddonSettings,
    BU_PT_Docs_Panel,
    BU_OT_OpenAddonPrefs,
    BU_OT_Open_N_Panel,
    BU_OT_OpenAddonLocation,
    BU_OT_OpenErrorLogFolder,
)
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
