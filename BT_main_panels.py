import bpy
import os
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

    def draw(self, context):
        self.open_addon_prefs(context)

    def open_addon_prefs(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text="Use the settings in the below panel or in the addon preferences")
        row = layout.row()
        row.operator("bu.open_addon_prefs", text="Addon preferences", icon='PREFERENCES')


class Addon_Updater_Panel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_UPDATER"
    bl_label = 'BullTools Asset Manager Updater'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_BBPS_MAIN_ADDON_PANEL"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        addon_updater_ops.update_settings_ui(self, context)


class BBPS_Info_Panel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_BBPS_INFO_PANEL"
    bl_label = 'BullTools Asset Manager Info'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_BBPS_MAIN_ADDON_PANEL"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        i = icons.get_icons()
        box = layout.box()
        row = box.row(align=True)
        row.alignment = 'EXPAND'
        version = bl_info['version']
        version_string = '.'.join(map(str, version))
        row.label(text=f'BullTools Asset Manager BETA - Version {version_string}')
        split = box.split(factor=0.66, align=True)
        col = split.column(align=False)
        col.alignment = 'LEFT'
        wrapp = textwrap.TextWrapper(width=int(context.region.width / 10))
        bu_info_text = wrapp.wrap(text='This add-on is under construction')
        for text_line in bu_info_text:
            col.label(text=text_line)
        col.separator(factor=2)

        col = box.column(align=True)
        col.alignment = 'LEFT'
        discord = col.operator('wm.url_open', text='Discord', icon_value=i["discord"].icon_id)
        twitter_bull = col.operator('wm.url_open', text='DeBullVader', icon_value=i["X_logo_black"].icon_id)
        twitter_pav = col.operator('wm.url_open', text='PolyAssetVault', icon_value=i["X_logo_black"].icon_id)

        discord.url = 'https://discord.gg/SNRnw2VrhR'
        twitter_pav.url = 'https://x.com/PolyAssetVault'
        twitter_bull.url = 'https://x.com/DeBullVader'


class BU_OT_OpenAddonPrefs(bpy.types.Operator):
    """ Open BullTools Asset Manager Addon Preferences """
    bl_idname = "bu.open_addon_prefs"
    bl_label = "Open Addon Preferences"
    bl_description = "Open Addon Preferences"

    def execute(self, context):
        addon_name = __name__.split('.')[0]
        preferences = bpy.context.preferences
        addon_prefs = preferences.addons[addon_name].preferences
        bpy.ops.screen.userpref_show("INVOKE_DEFAULT")
        addon_prefs.active_section = 'ADDONS'
        bpy.ops.preferences.addon_expand(module=addon_name)
        bpy.ops.preferences.addon_show(module=addon_name)
        return {'FINISHED'}


class BU_OT_Open_N_Panel(bpy.types.Operator):
    """ Toggle BullTools N Panel """
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
    bl_label = 'BullTools'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BullTools'

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        box = row.box()
        i = icons.get_icons()
        box.template_icon(icon_value=i["BT_Icon"].icon_id, scale=4)
        website = box.operator('wm.url_open', text='PolyAssetVault', icon='URL')
        website.url = 'https://polyassetvault.com'

        wrapp = textwrap.TextWrapper(width=int(context.region.width / 6.5))
        box = layout.box()
        row = box.row(align=True)
        row.alignment = 'EXPAND'
        col = row.column(align=True)
        bu_info_text = wrapp.wrap(text='BullTools — a collection of tools for creators')
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
        box = layout.box()
        box.label(text='Documentation', icon='INFO')
        doc = box.operator('bu.url_open', text='Getting Started', icon='HELP')
        doc.url = addon_info.GITBOOKURL
        box.separator()
        box.operator('wm.console_toggle', text='Toggle Console', icon='CONSOLE')
        box.operator('bu.open_error_logs_folder', text='Open Error Logs Folder', icon='TEXT')
        box.operator('bu.open_addon_location', text='Open Addon Install Location', icon='FILE_FOLDER')


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
        logs_folder = os.path.join(addon_path, 'error_logs')
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
