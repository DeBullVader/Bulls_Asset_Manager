# Bulls Asset Manager — Claude Context

## Project Goal
Blender 4.2+ addon for rendering asset previews and managing asset libraries, with marketplace integration for [PolyAssetVault](https://www.polyassetvault.com) (login, browse, download, upload).

## Development Workflow
- Blender is loaded via the **Blender Development** VSCode extension
- `Ctrl+Shift+P → Blender: Start` launches Blender with the addon loaded
- `Ctrl+Shift+P → Blender: Reload Addons` reloads after code changes
- Logs/errors appear directly in the **VSCode terminal**
- Always test changes by reloading in Blender before committing

## Git Branches
- `main` — stable, also synced to GitBook docs (`/docs` folder)
- `dev` — all active development happens here
- `backup/initial-state` — snapshot before cleanup began

**Always work on `dev`. Never commit directly to `main`.**

## Addon Identity
```python
bl_info["name"] = "bulltools_asset_manager"  # used for get_addon_prefs() lookup
__package__     = "Bulls_Asset_Manager"        # folder name / import root
```
The addon was forked from "UniBlend" — replace any remaining "UniBlend" references with "Bulls Asset Manager" or "BullTools".

## Naming Conventions
| Type | Prefix | Example |
|---|---|---|
| Operator | `UB_OT_` | `UB_OT_RenderPreviews` |
| Panel | `UB_PT_` | `UB_PT_AssetManager` |
| PropertyGroup | no prefix or `E_` for enums | `E_AssetManagerSettings` |
| Menu | `UB_MT_` | `UB_MT_AssetTypes` |
| bl_idname (operators) | `ub.` | `"ub.render_previews"` |
| bl_idname (panels) | `UB_PT_` | `"UB_PT_AssetManager"` |
| Internal data names | `UB_` | `"UB_Preview_Camera"` |

## File Structure
```
Bulls_Asset_Manager/
├── __init__.py                        # Entry point, AllPrefs, BUProperties
├── BT_main_panels.py                  # Top-level N-panel (BullTools tab)
├── lib_preferences.py                 # AddonPreferences mixin (BUPrefLib)
├── icons.py                           # Custom icon loader
├── addon_updater(_ops).py             # CGCookie auto-updater (third-party, don't modify)
├── core_tools/
│   ├── preview_render_scene.py        # Append/remove/switch PreviewRenderScene
│   └── asset_manager/
│       ├── asset_manager_ui.py        # Main panel + tab switching
│       ├── asset_manager_render_previews.py   # Camera adjust + modal render loop
│       ├── asset_manager_render_strategy.py   # Strategy classes per asset type
│       ├── asset_manager_asset_data.py        # Mark/tag/metadata operators
│       ├── asset_manager_hierarchy.py         # Asset tree builder
│       ├── asset_manager_utils.py             # Filters, exclude list, UI helpers
│       └── asset_manager_light_setups.py      # HDRI + light setup enums
├── utils/
│   ├── addon_info.py                  # get_addon_prefs(), library helpers, BU_OT_url_open
│   ├── addon_logger.py                # addon_logger (rotating file log)
│   ├── asset_bbox_logic.py            # Bounding box, scale, camera math
│   ├── version_handler.py             # Blender 4.0+ API compat
│   └── generate_blend_files.py        # Asset export helpers (partially dead)
└── docs/                              # GitBook documentation (synced to main)
```

## Registration Pattern
Every package has `register()` and `unregister()`. Classes use `register_classes_factory`:
```python
from bpy.utils import register_classes_factory

classes = (MyOperator, MyPanel)
register_classes, unregister_classes = register_classes_factory(classes)

def register():
    register_classes()
    bpy.types.Scene.my_prop = bpy.props.PointerProperty(type=MyPropertyGroup)

def unregister():
    unregister_classes()
    del bpy.types.Scene.my_prop
```

## Operator Boilerplate
```python
class UB_OT_MyOperator(bpy.types.Operator):
    bl_idname = "ub.my_operator"
    bl_label = "My Operator"
    bl_description = "What it does"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        # do work
        return {'FINISHED'}
```

## Panel Boilerplate
```python
class UB_PT_MyPanel(bpy.types.Panel):
    bl_idname = "UB_PT_MyPanel"
    bl_label = "My Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BullTools"
    bl_parent_id = "VIEW3D_PT_BBPS_MAIN_ADDON_PANEL"  # parent to main BullTools panel
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
```

## Key Scene Properties
```python
context.scene.asset_props          # AssetProperties (selected, adjust_camera, asset_types, etc.)
context.scene.render_settings      # RenderSettings (resolution, HDRI, floor, backdrop, etc.)
context.scene.light_setup          # EnumProperty — active light setup (image preview)
context.scene.hdri                 # EnumProperty — active HDRI file (image preview)
context.scene.asset_manager_settings_tabs  # E_AssetManagerSettings (switch_tabs enum)
```

## Key Utility Functions
```python
from utils import addon_info

addon_info.get_addon_prefs()           # Returns addon preferences object
addon_info.get_addon_path()            # Returns absolute path to addon folder
addon_info.get_asset_library()         # Gets registered Blender asset library
addon_info.BU_OT_url_open              # Operator to open URLs (use for GitBook links)
```

## Logging
```python
from utils.addon_logger import addon_logger

addon_logger.info("message")
addon_logger.error("message")
addon_logger.exception("message")  # includes traceback
```
Log file: `error_logs/error_log.txt` (rotating, 1MB max, 5 backups)

## Blender API Notes (4.2+)
- Use `bpy.props.PointerProperty` on `bpy.types.Scene` / `bpy.types.WindowManager` for custom data
- Asset marking: `obj.asset_mark()` / `obj.asset_clear()`
- Asset metadata: `obj.asset_data.description`, `obj.asset_data.author`, `obj.asset_data.tags`
- Register custom properties in `register()`, always `del` them in `unregister()`
- `bpy.utils.register_classes_factory` handles class registration order automatically

## GitBook Documentation
- Docs live in `/docs` on the `main` branch
- GitBook syncs automatically on push to `main`
- When adding a new feature panel, add a `?` help button using `BU_OT_url_open` pointing to the relevant GitBook page
- Keep `SUMMARY.md` updated when adding new doc pages

## What NOT to Do
- Do not modify `addon_updater.py` or `addon_updater_ops.py` (third-party)
- Do not hardcode "UniBlend" anywhere — use "Bulls Asset Manager" or "BullTools"
- Do not commit to `main` directly — use `dev` and push
- Do not leave `print()` debug statements in committed code — use `addon_logger` instead
