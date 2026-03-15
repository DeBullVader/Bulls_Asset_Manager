# Bulls Asset Manager — Project Summary

## Overview

**Bulls Asset Manager** is a Blender addon (4.2+) built by **DeBullVader** for professional asset management, preview rendering, and asset library organization. It integrates tightly with Blender's native Asset Browser and provides a complete workflow for marking, tagging, rendering previews, and exporting assets to a structured library.

- **Addon ID**: `bulltools_asset_manager`
- **Version**: 0.0.1
- **Minimum Blender**: 4.2.0
- **Location**: VIEW3D N-Panel
- **Category**: Tools
- **Issue Tracker**: https://github.com/DeBullVader/BU_Blender_AssetLibrary_Plugin/issues

---

## Project Structure

```
Bulls_Asset_Manager/
├── __init__.py                          # Addon entry point, registration, BUProperties
├── BT_main_panels.py                    # Top-level N-panel UI (branding, info, docs, updater)
├── lib_preferences.py                   # Addon preferences (library paths, author, toggles)
├── icons.py                             # Custom icon loading (PNG/SVG)
├── addon_updater.py                     # CGCookie auto-updater v1.1.1 (GitHub releases)
├── addon_updater_ops.py                 # Updater UI operators and panels
│
├── core_tools/
│   ├── __init__.py                      # Registers asset_manager + preview_render_scene
│   ├── preview_render_scene.py          # Append/remove/switch preview render scene
│   └── asset_manager/
│       ├── __init__.py                  # Registers all asset_manager submodules
│       ├── asset_manager_ui.py          # Main UI panel with tab switching
│       ├── asset_manager_render_previews.py   # Camera adjustment + render operators
│       ├── asset_manager_render_strategy.py   # Per-type render strategy classes
│       ├── asset_manager_asset_data.py        # Asset metadata/tagging operators
│       ├── asset_manager_hierarchy.py         # Asset hierarchy tree builder
│       ├── asset_manager_utils.py             # Core asset operations and filters
│       └── asset_manager_light_setups.py      # HDRI + light setup management
│
├── utils/
│   ├── __init__.py
│   ├── addon_info.py                    # Library management, asset lookup, type mappings
│   ├── addon_logger.py                  # Rotating file logger
│   ├── asset_bbox_logic.py              # Bounding box, scaling, camera look-at math
│   ├── version_handler.py               # Blender 4.0+ API compatibility layer
│   └── generate_blend_files.py          # Asset export, placeholder generation, ZIP
│
├── bulls_plugin_assets/
│   ├── HDRI/                            # 9 .hdr environment maps
│   ├── blend_files/                     # Preview_Rendering.blend + textures
│   ├── custom_icons/                    # PNG/SVG UI icons
│   ├── images/                          # Logos and promotional images
│   └── light_setups/                    # Lighting preset thumbnail images
│
└── error_logs/                          # Auto-generated rotating error log files
```

---

## Core Features

### 1. Asset Marking & Metadata
- Mark any Blender object, collection, material, or node group as an asset
- Set author, description, and tags per asset via a popup dialog
- Bulk mark/unmark or exclude all children in a hierarchy
- Supports global author name from addon preferences

### 2. Preview Rendering
- Dedicated preview render scene loaded from a `.blend` template
- Camera adjustment mode: enter local view, position camera interactively
- Per-type rendering strategies: objects get duplicated and scaled; materials are applied to preset objects (shaderball, cube, plane, cylinder, etc.); collections are instanced; node groups get a test material built around them
- Rendered thumbnails are automatically assigned back to the asset

### 3. Asset Library Integration
- Create and register Blender asset libraries from the addon preferences
- Validate library paths; switch between libraries
- Reads `.cats.txt` catalog files for asset organization
- Full compatibility with Blender's native Asset Browser

### 4. Lighting & HDRI
- 9 bundled HDRI environments: city, courtyard, forest, interior, night, studio, sunrise, sunset, and more
- 5 preset light setups (Cold/Warm/Retro 3-point lighting) with thumbnail previews
- Adjustable HDRI exposure and color temperature
- Configurable backdrop plane and floor material (color, metallic, roughness, emissive strength)

### 5. Asset Export / Upload Preparation
- Export assets to `.blend` files with JSON metadata sidecar
- Generate lightweight placeholder assets for slow-loading originals
- Copy metadata (tags, description, license) from original to placeholder
- Compress asset folders to ZIP for upload
- Load custom preview thumbnail images (PNG/JPG)

### 6. Auto-Updates
- Built-in GitHub-based updater (CGCookie addon_updater v1.1.1)
- Checks for new releases, downloads and installs with one click
- Configurable check interval

---

## UI Layout

### N-Panel → BullTools Tab

| Panel | Contents |
|---|---|
| **Main Panel** | BullTools branding icon, addon version |
| **Info Panel** | Discord, X (Twitter) links |
| **Addon Updater** | Check for updates / install |
| **Addon Settings** | Link to preferences |
| **Documentation** | Docs links, toggle console, open error log folder |

### N-Panel → Asset Manager Area

Three tabs driven by `E_AssetManagerSettings.active_tab`:

**Operators Tab**
- Adjust Preview Camera (toggle local view + camera lock)
- Mark / Unmark selected assets as assets
- Exclude / include assets from operations

**Render Settings Tab**
- HDRI selector (image enum with previews)
- Light setup picker (image enum with previews)
- Backdrop color and emissive strength
- Floor material: metallic, roughness, color
- Background transparency toggle
- Render resolution

**Tool Settings Tab**
- Preview rotation (X/Y/Z)
- Debug mode toggle
- Exclude extras toggle

**Upload Settings (bottom)**
- Author name field
- Library path validation

### Preview Render Scene Panel
- Append Preview Scene from template blend
- Remove Preview Scene
- Switch between main scene and preview scene

---

## Module Breakdown

### `__init__.py`
Entry point for Blender to detect the addon.

**Key classes:**
- `AllPrefs` — Combines `AddonUpdate` + `BUPrefLib` into a single preferences class
- `BUProperties` (PropertyGroup on `WindowManager`) — Tracks upload/download progress:
  - `progress_total`, `progress_percent`, `progress_word`, `progress_downloaded_text`
  - `assets_to_upload`, `new_assets`, `updated_assets`, `addon_name`

Registers all submodules in order: `utils` → `BT_main_panels` → `icons` → `core_tools`.

---

### `BT_main_panels.py`
Top-level N-panel UI.

| Class | Type | Purpose |
|---|---|---|
| `BBPS_Main_Addon_Panel` | Panel | Root panel with BullTools branding |
| `BBPS_Info_Panel` | Panel | Social links (Discord, X) |
| `Addon_Updater_Panel` | Panel | Updater UI integration |
| `BU_PT_AddonSettings` | Panel | Link to preferences page |
| `BU_PT_Docs_Panel` | Panel | Documentation, console toggle, error log |
| `BU_OT_OpenAddonPrefs` | Operator | Open addon preferences |
| `BU_OT_Open_N_Panel` | Operator | Toggle N-panel visibility |
| `BU_OT_OpenAddonLocation` | Operator | Open addon folder in file explorer |
| `BU_OT_OpenErrorLogFolder` | Operator | Open error_logs/ in file explorer |

---

### `lib_preferences.py`
Defines `BUPrefLib` — the addon preferences mixin.

**Properties:**
- `lib_path` — Asset library directory (default: `B:\BullTools\Asset_lib`)
- `new_lib_path` — Staging path for adding a new library
- `enable_custom_thumnail_path` — Toggle custom thumbnail directory
- `thumb_path` — Custom thumbnail directory path
- `author` — Default author name for asset metadata
- `show_info`, `show_docs`, `show_updater`, `show_settings` — Panel visibility toggles

---

### `icons.py`
Loads and manages custom icons for the UI.

- Scans `bulls_plugin_assets/custom_icons/` for PNG and SVG files
- Creates a Blender `preview_collections` entry
- Exposes `get_icons()` to retrieve the loaded collection
- Contains a stub `load_yt_thumb_as_icon()` for potential YouTube thumbnail loading via curl

---

### `addon_updater.py` / `addon_updater_ops.py`
Third-party CGCookie addon updater (v1.1.1). Not custom code — included as a dependency.

- `SingletonUpdater` — Checks GitHub releases, downloads and installs updates
- Supports version constraints, backup-before-update, async background checking
- `addon_updater_ops.py` provides the `AddonUpdaterInstallPopup` operator and UI draw helpers

---

### `core_tools/preview_render_scene.py`
Manages a dedicated render scene loaded from the bundled `.blend` template.

| Class | Type | Purpose |
|---|---|---|
| `UB_OT_Append_Preview_Render_Scene` | Operator | Appends `PreviewRenderScene` from template blend |
| `UB_OT_Remove_Preview_Render_Scene` | Operator | Deletes scene + orphan purge |
| `UB_OT_Switch_To_Preview_Render_Scene` | Operator | Toggle between main and preview scene |
| `UB_PT_PreviewRenderScene` | Panel | Append/remove/switch buttons + scene selector |

---

### `core_tools/asset_manager/asset_manager_ui.py`
Drives the main Asset Manager panel and its three tabs.

| Class | Purpose |
|---|---|
| `UB_PT_AssetManager` | Root panel (empty draw, children handle content) |
| `E_AssetManagerSettings` | PropertyGroup: `active_tab` enum (operators/render_settings/tool_settings) |
| `AssetManager_settings` | Static draw helpers: `draw_tool_operators()`, `draw_tool_settings()`, `draw_render_settings()` |

`draw_render_settings()` renders the full HDRI picker, light setup picker, backdrop color, floor material properties, and resolution fields.

`upload_settings()` draws the author name field and library path validation.

---

### `core_tools/asset_manager/asset_manager_render_previews.py`
The main rendering workflow operators.

| Class | Purpose |
|---|---|
| `UB_Preview_Defaults` | Base class with `get_or_create()` helpers for camera/collection |
| `UB_OT_Pivot_Bottom_Center` | Moves object origin to bottom-center of bounding box |
| `UB_OT_AdjustPreviewCamera` | Modal operator: enter/exit local view, lock/unlock camera |
| `UB_OT_RenderPreviews` | Main render operator: loops through selected assets and renders each |

**Camera Adjustment Flow:**
1. Creates preview collection if not present
2. Adds camera if not present
3. Enters local view (isolates the asset)
4. Sets render resolution
5. Locks camera to current view
6. On exit: unlocks camera, exits local view

**Render Flow (per asset):**
1. Select asset
2. Look up render strategy by asset type
3. Call `strategy.setup()` — positions asset in scene
4. `align_camera_to_selected_asset()` — frames the camera
5. `bpy.ops.render.render()` — renders the image
6. Assigns rendered image as asset preview

---

### `core_tools/asset_manager/asset_manager_render_strategy.py`
Implements the **Strategy Pattern** — each asset type has its own rendering approach.

| Class | Asset Type | What it does |
|---|---|---|
| `ObjectRenderStrategy` | Object | Duplicates object, applies rotation/scale, aligns camera |
| `MaterialRenderStrategy` | Material | Applies material to a preset render object (shaderball, cube, plane, etc.) |
| `CollectionRenderStrategy` | Collection | Creates a COLLECTION instance, scales it, positions it |
| `MaterialNodeRenderStrategy` | Material Node Group | Builds a test material: UV Coords → Node Group → BSDF → Output |
| `GeometryNodeRenderStrategy` | Geometry Node Group | Creates object with modifier using the node group |

**Helper functions:**
- `create_collection_instance()` — Creates an EMPTY object set to COLLECTION instance type
- `scale_asset_to_render()` — Calculates and applies scale so asset fits `max_scale` bounds
- `align_camera_to_selected_asset()` — Runs camera-to-view then applies offset translation
- `set_asset_and_cam_rotation()` — Applies stored X/Y/Z rotation from scene properties
- `get_render_object()` — Returns the appropriate preview object by type name

---

### `core_tools/asset_manager/asset_manager_asset_data.py`
Operators for editing asset metadata.

| Class | Purpose |
|---|---|
| `UB_OT_AssetMetadata` | Popup dialog: set author, description, tags (add/remove/update) |
| `UB_OT_ExcludeAllChildren` | Bulk exclude or include all child assets |
| `UB_OT_MarkAllChildren` | Bulk mark or unmark all child assets |
| `UB_OT_MarkOrClearAsset` | Toggle asset marked state on one asset |
| `UB_OT_MarkAssets` | Mark all selected objects/materials/collections as assets |

`UB_OT_AssetMetadata` supports:
- Global author from preferences or per-asset author
- Comma-separated tag input that gets split and applied individually
- Add, remove, and update individual tags

---

### `core_tools/asset_manager/asset_manager_hierarchy.py`
Builds a tree structure representing the parent-child relationships of assets.

**`AssetHierarchy` class:**
- `name`, `asset_type`, `blender_object` — Identity
- `children: list[AssetHierarchy]` — Recursive children
- `minimized: bool` — UI collapse state

**`build_hierarchy(selected_assets, asset_type)` function:**
- **Objects**: Links children by Blender parent-child relationships
- **Materials**: Groups by object → material slot → material
- **Material Nodes**: Object → material → node groups of type SHADER/COMPOSITING
- **Geometry Nodes**: Object → modifiers → node groups of type GEOMETRY
- **Collections**: Lists unique collections from selected objects

---

### `core_tools/asset_manager/asset_manager_utils.py`
Core asset operations and filtering utilities.

**`AssetOperations` static class:**
- `op_exclude_asset(asset)` — Toggle asset in exclude list
- `op_exclude_all(assets)` — Bulk add/remove all from exclude list
- `op_mark_clear_children(parent, mark)` — Recursively mark/clear child assets
- `op_minimize_asset_details(asset)` — Toggle minimized state in UI
- `get_child_assets(asset, asset_type)` — Return children filtered by type

**Filter functions:**
- `get_filter_asset_type(asset_type)` — Returns `AssetType` enum filtered by category
- `get_selected_assets(asset_type)` — Selected objects filtered by type
- `get_icon_for_asset_type(asset_type)` — Maps type to Blender icon string
- `filter_objects()` — Only mesh/armature/curve/etc objects (excludes lights, cameras, probes)
- `filter_materials()` — All materials on selected objects
- `filter_geometry_nodes()` — Geometry node groups from modifiers
- `filter_material_nodes()` — Shader/compositor node groups from materials

---

### `core_tools/asset_manager/asset_manager_light_setups.py`
Manages HDRI world settings and light preset switching.

**Key functions:**
- `gen_preview_collection(image_dir)` — Generates enum items `(id, name, description, icon_id, index)` from image files in a directory
- `scene_world_settings(scene, hdri_path)` — Creates/updates world shader tree with HDRI node + exposure + color temperature
- `set_light_settings(scene)` — Reads scene properties and applies floor/backdrop visibility, colors, metallic, roughness
- `add_preview_collections(image_path)` — Creates a Blender `preview_collections` entry from a directory
- `register()` — Sets up two Scene `EnumProperty` fields:
  - `light_setup` — Enum of PNG thumbnails from `light_setups/` folder
  - `hdri` — Enum of HDR files from `HDRI/` folder

---

### `utils/addon_info.py`
Central hub for addon-level utilities (~490 lines).

**Library management:**
- `get_addon_path()` — Finds addon directory by matching `bl_info["name"]`
- `get_addon_prefs()` — Returns addon preferences object
- `get_asset_library(lib_name)` — Finds a registered Blender asset library by name
- `add_library_to_blender(name, path)` — Creates and registers a new asset library

**Asset lookup:**
- `find_asset_by_name(name, asset_type)` — Searches `bpy.data` for a named asset across objects/materials/collections/node groups
- `get_local_selected_assets()` — Returns assets selected in the file browser
- `get_asset_browser_window_area()` — Locates the asset browser area in open windows

**Type helpers:**
- `type_mapping()` — Dict: asset type string → `bpy.data` attribute name
- `get_types()` — List of `(id, label, description, icon, index)` for all supported asset types
- `get_object_type()` — Full list of all Blender object type identifiers

**Operators:**
- `WM_OT_RedrawArea` — Forces a UI area redraw
- `BU_OT_url_open` — Opens a URL in the system browser (with GitBook description)
- `INFO_OT_custom_dialog` — Multiline info dialog popup

---

### `utils/addon_logger.py`
Simple rotating file logger (~50 lines).

- Log file: `error_logs/error_log.txt`
- Max file size: 1 MB, keeps 5 backups
- Log format: `YYYY-MM-DD HH:MM:SS - LEVEL - message`
- Exports `addon_logger` — use with `addon_logger.error()`, `addon_logger.info()`, `addon_logger.exception()`

---

### `utils/asset_bbox_logic.py`
All bounding box and transform math for the render pipeline.

**Object bounding box:**
- `get_obj_world_bbox_corners(obj)` — 8 corners in world space
- `get_obj_world_bbox_size(obj)` — `(width, height, depth)` tuple
- `scale_object_for_render(obj, scale_factor)` — Applies uniform scale
- `get_bottom_center_extent(obj)` — Lowest Y point at object center
- `get_obj_center_pivot_point(obj)` — 3D center of bounding box
- `set_bottom_center(obj)` — Moves object origin to bottom-center

**Camera math:**
- `look_at(camera, target, up)` — Points camera at a 3D location with specified up vector
- `set_camera_look_at_vector(camera, target)` — Convenience wrapper

**Collection bounding box:**
- `get_collection_bounding_box(collection)` — Union bbox of all objects in collection
- `calc_col_scale_factor(collection, max_scale)` — Scale factor to fit within max bounds
- `scale_collection_for_render(collection, max_scale)` — Applies calculated scale

**Combined pipeline:**
- `scale_asset_for_render(asset, asset_type, max_scale)` — Full scaling pipeline dispatched by type

---

### `utils/version_handler.py`
Blender API compatibility for pre/post 4.0 changes (~60 lines).

- `latest_version()` — Returns `True` if Blender >= 4.0.0
- `get_asset_library_reference(area)` — Gets current asset library reference (handles renamed API)
- `set_asset_library_reference(area, lib)` — Sets library reference with version handling
- `get_selected_assets(context)` — Gets selected assets with version compatibility

---

### `utils/generate_blend_files.py`
Asset export and upload preparation (~337 lines).

**Export pipeline:**
- `write_original_file(asset, path)` — Exports asset to `.blend` with JSON sidecar
- `create_asset_json_file(asset, path)` — Creates `BU_Asset_Info.json` with name, type, Blender version, creation timestamp

**Placeholder generation:**
- `create_placeholder(asset)` — Makes lightweight copy from original
- `generate_placeholder_file(asset, asset_type)` — Creates empty objects/collections/materials/node groups
- `write_placeholder_file(asset, path)` — Saves placeholder `.blend`
- `copy_metadata_to_placeholder(original, placeholder)` — Copies tags, description, license

**Helpers:**
- `add_asset_tags(asset)` — Adds standard tags: 'Original', 'Premium', version string
- `get_asset_thumb_paths(asset, directory)` — Finds PNG/JPG thumbnail file
- `zip_directory(source_dir, output_path)` — Compresses asset folder for upload
- `lib_id_load_custom_preview(asset, image_path)` — Assigns custom preview image
- `new_GeometryNodes_group()` — Creates an empty geometry node group

---

## Render Pipeline (Step by Step)

```
User clicks "Render Previews"
    │
    ▼
UB_OT_RenderPreviews.execute()
    │
    ├── get_selected_assets(asset_type)          ← filter selection by type
    │
    ├── For each asset:
    │       │
    │       ├── Look up strategy by asset_type
    │       │   (Object / Material / Collection / MaterialNode / GeometryNode)
    │       │
    │       ├── strategy.setup(asset, scene)
    │       │   ├── ObjectRenderStrategy:     duplicate → scale → position
    │       │   ├── MaterialRenderStrategy:   apply to render object (shaderball etc.)
    │       │   ├── CollectionRenderStrategy: create instance → scale → position
    │       │   └── NodeRenderStrategy:       build test material → link nodes
    │       │
    │       ├── set_asset_and_cam_rotation()     ← apply stored X/Y/Z rotation
    │       │
    │       ├── align_camera_to_selected_asset() ← camera-to-view + translation offset
    │       │
    │       ├── scene_world_settings()           ← apply HDRI + exposure
    │       │
    │       ├── set_light_settings()             ← apply backdrop + floor settings
    │       │
    │       ├── bpy.ops.render.render()          ← actual render
    │       │
    │       └── asset.preview = rendered image   ← assign thumbnail
    │
    └── Restore scene state
```

---

## Asset Types Supported

| Type | bpy.data | Subtypes / Notes |
|---|---|---|
| Object | `bpy.data.objects` | Mesh, Armature, Curve, Surface, Meta, Font, Volume, Lattice, Empty, Grease Pencil, Point Cloud, Light (excluded from filter), Camera (excluded) |
| Collection | `bpy.data.collections` | All collections; instanced for rendering |
| Material | `bpy.data.materials` | All materials on selected objects |
| Material Node Group | `bpy.data.node_groups` | Type: SHADER or COMPOSITING |
| Geometry Node Group | `bpy.data.node_groups` | Type: GEOMETRY |

**Excluded from asset operations by default:** Camera, Light, Light Probe, Point Cloud, Speaker, Volume

---

## Data Structures

### `BUProperties` (WindowManager PropertyGroup)
Tracks progress for async upload/download operations:
```python
progress_total: IntProperty
progress_percent: IntProperty
progress_word: StringProperty        # e.g. "Uploading..."
progress_downloaded_text: StringProperty
assets_to_upload: IntProperty
new_assets: IntProperty
updated_assets: IntProperty
addon_name: StringProperty
```

### `E_AssetManagerSettings` (Scene PropertyGroup)
Controls which tab is active in the asset manager panel:
```python
active_tab: EnumProperty  # 'operators' | 'render_settings' | 'tool_settings'
```

### `AssetHierarchy`
Recursive tree node for representing asset parent-child relationships:
```python
name: str
asset_type: str
blender_object: bpy.types.ID
children: list[AssetHierarchy]
minimized: bool
```

### `AssetOperations` (static state)
Holds runtime state for the UI:
```python
exclude_list: list      # Assets excluded from batch operations
minimized_list: list    # Assets collapsed in hierarchy UI
```

---

## External Assets (bundled)

### HDRI Files (`bulls_plugin_assets/HDRI/`)
9 environment maps for preview rendering:
`city`, `courtyard`, `forest`, `interior`, `night`, `studio`, `sunrise`, `sunset`, and one more.

### Blend Template (`bulls_plugin_assets/blend_files/`)
- `Preview_Rendering.blend` — Pre-configured render scene with camera, lights, backdrop plane, floor, preset render objects (shaderball, cube, plane, cylinder, etc.)
- Associated texture files

### Light Setup Thumbnails (`bulls_plugin_assets/light_setups/`)
Thumbnail images representing 5 lighting presets (Cold/Warm/Retro 3-point lighting configurations).

### Custom Icons (`bulls_plugin_assets/custom_icons/`)
PNG and SVG files loaded at addon registration as Blender preview icons for UI use.

---

## Configuration Reference

### Addon Preferences (`lib_preferences.py`)
| Property | Default | Description |
|---|---|---|
| `lib_path` | `B:\BullTools\Asset_lib` | Asset library root directory |
| `new_lib_path` | — | Staging path when adding new library |
| `enable_custom_thumnail_path` | False | Use separate thumbnail directory |
| `thumb_path` | — | Custom thumbnail directory |
| `author` | — | Default author for asset metadata |

### Scene Render Properties (set by `asset_manager_render_strategy.py`)
| Property | Description |
|---|---|
| `light_setup` | Active light setup (enum from thumbnails) |
| `hdri` | Active HDRI file (enum from HDRI folder) |
| `backdrop_color` | RGBA color of backdrop plane |
| `backdrop_strength` | Emissive strength of backdrop |
| `floor_metallic` | Floor material metallic value |
| `floor_roughness` | Floor material roughness value |
| `floor_color` | Floor material base color |
| `preview_rotation_x/y/z` | Asset rotation during render |
| `render_resolution` | Output resolution in pixels |
| `transparent_background` | Render with alpha channel |

---

## Architecture Patterns

| Pattern | Where Used | Purpose |
|---|---|---|
| **Strategy** | `asset_manager_render_strategy.py` | Swap rendering behavior per asset type without conditionals |
| **Singleton** | `addon_updater.py` (`SingletonUpdater`) | Single updater instance across the addon lifecycle |
| **PropertyGroup** | `BUProperties`, `E_AssetManagerSettings` | Blender-native way to attach custom data to scenes/window managers |
| **Module Registry** | All `__init__.py` files | Each package registers/unregisters its own classes |
| **Mixin** | `AllPrefs(AddonUpdate, BUPrefLib)` | Combine updater + library preferences into one class |
| **Static Class** | `AssetOperations` | Shared mutable state (exclude list, minimized list) across operators |

---

## Logging

Errors and events are logged to `error_logs/error_log.txt` using Python's `RotatingFileHandler`.

```python
from utils.addon_logger import addon_logger

addon_logger.info("Asset marked successfully")
addon_logger.error("Failed to find library path")
addon_logger.exception("Unexpected error during render")  # includes traceback
```

Max log size: 1 MB · Backups kept: 5
