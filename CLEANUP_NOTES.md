# Cleanup Notes

**Branch**: `dev`
**Commit**: `4f0c8bb`
**Date**: 2026-03-15
**Summary**: 560 lines removed, 113 added across 7 files. Fixed 3 critical runtime bugs, removed all leftover marketplace/upload code from the previous "UniBlend" addon, and replaced all old branding references.

---

## Critical Bug Fixes

These bugs would have prevented the addon from functioning at all.

### 1. `utils/addon_info.py` — `get_addon_path()` always returned `None`
**Problem**: The function searched for an addon named `'UniBlend'` — the old addon name. Since no such addon exists, it always returned `None`, breaking every feature that depends on finding the addon's folder (render scene loading, icon loading, error log path, etc.).
**Fix**: Changed the name check to `'bulltools_asset_manager'`.

### 2. `core_tools/preview_render_scene.py` — Missing imports + wrong asset path
**Problem**: The `UB_OT_Append_Preview_Render_Scene` operator used `addon_info.get_addon_path()` and `os.path.join()` but neither `addon_info` nor `os` were imported. The file would crash on any attempt to append the preview scene. Additionally the asset path was `BU_plugin_assets` instead of the correct `bulls_plugin_assets`.
**Fix**: Added `import os` and `from ..utils import addon_info`. Corrected the folder name.

### 3. `core_tools/asset_manager/asset_manager_utils.py` — Call to nonexistent function
**Problem**: `update_preview_path()` called `addon_info.get_upload_asset_library()` which does not exist anywhere in the codebase. This callback was attached to the `thumb_upload_path` property on `RenderSettings`, so accessing render settings would trigger the error.
**Fix**: Removed `update_preview_path()` entirely. Removed the `thumb_upload_path` property from `RenderSettings`.

---

## Dead Code Removed

### `__init__.py`
| Removed | Reason |
|---|---|
| `from importlib import reload` | Unused import |
| `BUProperties.progress_total` | Leftover marketplace upload progress tracking |
| `BUProperties.progress_percent` | Leftover marketplace upload progress tracking |
| `BUProperties.progress_word` | Leftover marketplace upload progress tracking |
| `BUProperties.progress_downloaded_text` | Leftover marketplace upload progress tracking |
| `BUProperties.assets_to_upload` | Leftover marketplace upload tracking |
| `BUProperties.new_assets` | Leftover marketplace upload tracking |
| `BUProperties.updated_assets` | Leftover marketplace upload tracking |
| Unused `addon_prefs` assignment in `register()` | Variable assigned but never used |

### `utils/addon_info.py`
| Removed | Reason |
|---|---|
| `from datetime import datetime, timezone` | Unused after removing `convert_to_UTC_datetime` |
| `get_data_types()` | Never called anywhere |
| `find_asset_by_name_placeholder()` | Duplicate of `find_asset_by_name()`, never called |
| `find_premium_asset_by_name()` | Duplicate of `find_asset_by_name()`, never called |
| `calculate_dynamic_chunk_size()` | Referenced undefined prefs (`max_chunk_size`, `chunk_size_percentage`), never called |
| `convert_to_UTC_datetime()` | Never called, leftover from download timestamp tracking |
| `get_catalog_trick_uuid()` | Never called, leftover from old catalog sync system |
| 14 commented-out asset type entries | Noise — unsupported types that will never be enabled |

### `utils/generate_blend_files.py`
The file was rebuilt from scratch — the old version had broken imports that would have crashed on load if the file were ever imported.

| Removed | Reason |
|---|---|
| `from . import catfile_handler` | Module does not exist — broken import |
| `from ..ui import generate_previews` | Module does not exist — broken import |
| `import datetime, json` | Unused after removing marketplace functions |
| `write_original_file()` | Marketplace upload only, called `get_asset_upload_folder()` which itself was broken |
| `get_asset_upload_folder()` | Called nonexistent `addon_info.get_upload_asset_library()` |
| `get_placeholder_upload_folder()` | Called nonexistent `addon_info.get_upload_asset_library()` |
| `copy_and_zip_catfile()` | Used broken `catfile_handler` import and nonexistent `get_upload_asset_library()` |
| `get_or_composite_placeholder_preview()` | Called `generate_previews.composite_placeholder_previews` from broken import |
| `find_asset_by_name()` | Exact duplicate of the version in `addon_info.py` |
| `create_asset_json_file()` | Marketplace metadata only, nothing calls it |
| `upload_target` check in `add_asset_tags()` | Referenced undefined `addon_prefs.upload_target` |
| `upload_target` check in `copy_metadata_to_placeholder()` | Referenced undefined `addon_prefs.upload_target` |
| `get_asset_thumb_paths()` | Referenced undefined `addon_prefs.thumb_upload_path` |
| `create_placeholder()` | Depended on all of the above broken functions |
| `write_placeholder_file()` | Called `get_placeholder_upload_folder()` which was broken |

**Kept**: `add_asset_tags`, `new_GeometryNodes_group`, `new_node_group_empty`, `generate_placeholder_file`, `copy_metadata_to_placeholder`, `zip_directory`, `remove_placeholder_asset`, `log_exception`

### `BT_main_panels.py`
| Removed | Reason |
|---|---|
| `from bpy.types import Context` | Unused import |
| `validate_library_dir()` | Never called anywhere in the codebase |
| `validate_bu_library_names()` | Never called anywhere in the codebase |
| `draw_bu_logo()` | Never called anywhere in the codebase |
| Commented-out YouTube/Reddit/Medium links | Old "UniBlend" social links, replaced by PolyAssetVault/BullTools links |
| Large commented-out block in `BU_PT_Docs_Panel` | Old UniBlend GitBook content, replaced with active docs button |

### `core_tools/asset_manager/asset_manager_ui.py`
| Removed | Reason |
|---|---|
| `mat_list()` method | Entirely commented out in the draw call, never used |
| `td, tt, ld, lt, thumbs_path` path variables | Computed but never used in the UI |

### `core_tools/asset_manager/asset_manager_utils.py`
| Removed | Reason |
|---|---|
| `from bpy.types import PropertyGroup` | Unused import |
| `from bpy.utils import register_class, unregister_class` | Unused imports |
| `from ...utils import asset_bbox_logic` | Unused import |
| `update_preview_path()` | Called nonexistent `get_upload_asset_library()` |
| `thumb_upload_path` property on `RenderSettings` | Used `update_preview_path` as callback |
| 14 commented-out asset type entries | Duplicate of the cleanup in `addon_info.py` |

---

## Branding Fixes (UniBlend → BullTools)

| File | Old | New |
|---|---|---|
| `utils/addon_info.py` | `bl_info['name'] == 'UniBlend'` | `bl_info['name'] == 'bulltools_asset_manager'` |
| `core_tools/preview_render_scene.py` | `bl_category = 'UniBlend'` | `bl_category = 'BullTools'` |
| `core_tools/asset_manager/asset_manager_ui.py` | `bl_category = 'UniBlend'` | `bl_category = 'BullTools'` |
| `core_tools/asset_manager/asset_manager_ui.py` | `"Render with UniBlend Logo"` | `"Render with BullTools Logo"` |
| `core_tools/asset_manager/asset_manager_utils.py` | `enable_ub_logo` / `"Enable UniBlend Logo"` | `enable_logo` / `"Enable BullTools Logo"` |
| `BT_main_panels.py` | `bl_label = 'BoolTools'` (also a typo) | `bl_label = 'BullTools'` |
| `BT_main_panels.py` | `""" Open UniBlend Addon Preferences """` | `""" Toggle BullTools N Panel """` |
| `BT_main_panels.py` | `'Bullltools Asset Manager Updater'` (triple-l typo) | `'BullTools Asset Manager Updater'` |
| `BT_main_panels.py` | `'Bullltools Asset Manager Info'` (triple-l typo) | `'BullTools Asset Manager Info'` |

---

## What Was NOT Removed

- `addon_updater.py` / `addon_updater_ops.py` — Third-party CGCookie updater, untouched
- `BU_OT_url_open` / `GITBOOKURL` / `gitbook_link_getting_started()` — Kept for future GitBook documentation buttons
- `get_object_type()` in `addon_info.py` — Kept, may be used for future object type filtering
- All render pipeline code — Core feature, untouched
- All asset marking/metadata operators — Core feature, untouched
- `zip_directory()`, `remove_placeholder_asset()` in `generate_blend_files.py` — Kept for future upload workflow
