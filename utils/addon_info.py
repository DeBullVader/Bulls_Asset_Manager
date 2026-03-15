import bpy, os, addon_utils, textwrap
from . import version_handler
from .addon_logger import addon_logger


# flags_enum = iter(range(1, 100, 1))
asset_types = [
    ("Objects", "Objects", "Object", "OBJECT_DATA", 2 ** 1),
    ("Materials", "Materials", "Materials", "MATERIAL", 2 ** 2),
    ("Material Nodes", "Material Nodes", "Material Node Groups", "NODE", 2 ** 3),
    ("Geometry Nodes", "Geometry Nodes", "Node Groups", "NODETREE", 2 ** 4),
    ("Collections", "Collections", "Collections", "OUTLINER_COLLECTION", 2 ** 5),
    ]

previous_states = {}

def get_types(*args, **kwargs):
    return asset_types

def get_bpy_data_types():
    data_types = {
        'OBJECT': bpy.data.objects,
        'MATERIAL': bpy.data.materials,
        'NODETREE': bpy.data.node_groups,
        'MATERIAL_NODE': bpy.data.node_groups,
        'GEOMETRY_NODE': bpy.data.node_groups,
        'COLLECTION': bpy.data.collections,
        'WORLD': bpy.data.worlds,
        'CAMERA': bpy.data.cameras,
        }
    return data_types 

def type_mapping ():
    return {
    "OBJECT": "objects",
    "Objects": "objects",
    "Object": "objects",
    "MATERIAL": "materials",
    "Materials":"materials",
    "WORLD": "worlds",
    "NODETREE": "node_groups",
    "COLLECTION": "collections",
    "Collection": "collections",
    "Collections": "collections",
    "ShaderNodeTree": "node_groups",
    "Material Nodes": "node_groups",
    "GeometryNodeTree": "node_groups",
    "Geometry Nodes": "node_groups",
    }



def get_object_type():
    return[
        ("ARMATURE", "Armature", "Armature", "ARMATURE_DATA", 2 ** 1),
        ("CAMERA", "Camera", "Camera", "CAMERA_DATA", 2 ** 2),
        ("CURVE", "Curve", "Curve", "CURVE_DATA", 2 ** 3),
        ("EMPTY", "Empty", "Empty", "EMPTY_DATA", 2 ** 4),
        ("GPENCIL", "Grease Pencil", "Grease Pencil", "OUTLINER_DATA_GREASEPENCIL", 2 ** 5),
        ("LIGHT", "Light", "Light", "LIGHT", 2 ** 6),
        ("LIGHT_PROBE", "Light Probe", "Light Probe", "OUTLINER_DATA_LIGHTPROBE", 2 ** 7),
        ("LATTICE", "Lattice", "Lattice", "LATTICE_DATA", 2 ** 8),
        ("MESH", "Mesh", "Mesh", "MESH_DATA", 2 ** 9),
        ("META", "Metaball", "Metaball", "META_DATA", 2 ** 10),
        ("POINTCLOUD", "Point Cloud", "Point Cloud", "POINTCLOUD_DATA", 2 ** 11),
        ("SPEAKER", "Speaker", "Speaker", "OUTLINER_DATA_SPEAKER", 2 ** 12),
        ("SURFACE", "Surface", "Surface", "SURFACE_DATA", 2 ** 13),
        ("VOLUME", "Volume", "Volume", "VOLUME_DATA", 2 ** 14),
        ("FONT", "Text", "Text", "FONT_DATA", 2 ** 15),
    ]

class WM_OT_RedrawArea(bpy.types.Operator):
    bl_idname = "wm.redraw"
    bl_label = "Redraw"
    bl_description = "Refresh current area"
    bl_options = {"REGISTER"}

    def execute(self, context):
        context.area.tag_redraw()
        # redraw(self,context, context.area.type)
        return {'FINISHED'}

def redraw(self, context,area_type):
    if context.screen is not None:
        for a in context.screen.areas:
            if a.type == area_type:
                a.tag_redraw()

def get_addon_path():
    for mod in addon_utils.modules():
        if mod.bl_info['name'] == 'bulltools_asset_manager':
            filepath = mod.__file__
            return os.path.dirname(os.path.realpath(filepath))

def get_plugin_assets_dir():
    addon_path = get_addon_path()
    return os.path.join(addon_path, 'bulls_plugin_assets')

def get_path():
    return os.path.dirname(os.path.realpath(__file__))

def No_lib_path_warning():
       return print('Could not find Library path. Please add a library path in the addon preferences!')

def get_addon_name():
    package = __package__
    try:
        name = package.removesuffix('.utils')
        addon_name = bpy.context.preferences.addons[name]
        return addon_name
    except:
        raise ValueError("couldnt get Name of addon, might be a different problem check top error")

def get_addon_prefs():
    return get_addon_name().preferences

def find_asset_by_name(asset_name):
    try:
        datablock_types = [
            bpy.data.objects,
            bpy.data.materials,
            bpy.data.collections,
            bpy.data.node_groups,
        ]
        
        for datablock in datablock_types:
            if asset_name in datablock:
                # print(f'asset {asset_name} found in file')
                return (datablock[asset_name])
        return None
    except Exception as error_message:
        print(f"An error occurred finding asset by name: {error_message}")

def traverse_tree(t):
    yield t
    for child in t.children:
        yield from traverse_tree(child)

def parent_lookup(coll):
    parent_lookup = {}
    for coll in traverse_tree(coll):
        for c in coll.children.keys():
            parent_lookup.setdefault(c, coll.name)
    return parent_lookup

def find_parent_collection(collection):
    coll_scene = bpy.context.scene.collection
    coll_parent = parent_lookup(coll_scene)
    return bpy.data.collections.get(coll_parent.get(collection.name))


def get_layer_object(context,object):
    '''Returns the view layer LayerCollection for a specificied Collection'''
    def scan_children(lc, result=None):
        if object.name in context.view_layer.layer_collection.collection.objects:
            return context.view_layer.layer_collection.collection.objects.get(object.name)
        else:
            for c in lc.children:
                if object.name in c.collection.objects:
                    return c.collection.objects.get(object.name)
                result = scan_children(c, result)
            return result

    return scan_children(bpy.context.view_layer.layer_collection)
        
def get_layer_collection(collection):
    '''Returns the view layer LayerCollection for a specificied Collection'''
    def scan_children(lc, result=None):
        for c in lc.children:
            if c.collection == collection:
                return c
            result = scan_children(c, result)
        return result

    return scan_children(bpy.context.view_layer.layer_collection)

def get_local_selected_assets(context):
    scr = bpy.context.screen
    for area in scr.areas:
        if area.type == 'FILE_BROWSER':
            with bpy.context.temp_override(area=area):
                asset_lib_ref = version_handler.get_asset_library_reference(context)
                if asset_lib_ref == 'LOCAL':
                    selected_assets = version_handler.get_selected_assets(context)
                    return selected_assets
                return None

def get_asset_browser_window_area(context):
    for window in context.window_manager.windows:
        screen = window.screen
        if 'FILE_BROWSER' in [area.type for area in screen.areas]:
            for area in screen.areas:
                if area.type == 'FILE_BROWSER':
                    return window,area
        else:
            return None,None

def get_current_file_location():
    return bpy.data.filepath

def get_author():
    author = get_addon_name().preferences.author
    if author == '':
        author = 'Anonymous'
    return author



def get_or_create_lib_path_dir(dir_path,lib_name):
    lib_path = os.path.join(dir_path,lib_name)
    if not os.path.isdir(str(lib_path)):
        os.mkdir(str(lib_path))
        addon_logger.info(f'Created Library path because it did not exist: {lib_name}')
    return lib_path

def add_library_to_blender(dir_path,lib_name):
    if lib_name not in bpy.context.preferences.filepaths.asset_libraries:
        lib_path = get_or_create_lib_path_dir(dir_path,lib_name)
        bpy.ops.preferences.asset_library_add(directory = lib_path, check_existing = True)
        addon_logger.info(f'Added Library to blender because it did not exist: {lib_name}')
    lib =bpy.context.preferences.filepaths.asset_libraries.get(lib_name)
    if lib:
        if 'Premium' in lib_name:
            lib.import_method = 'APPEND'
    return lib


def get_asset_library(dir_path,lib_name):
    lib =bpy.context.preferences.filepaths.asset_libraries.get(lib_name)
    # check if the existing directory is the same as the directory set in addon_prefs.lib_path
    if lib:
        lib_dirpath,_ = os.path.split(lib.path)
        if lib_dirpath != dir_path:
            lib.path = os.path.join(dir_path,lib_name)
            lib.name = lib_name
            addon_logger.info(f'Library found but directory was different. Adjusted to the correct one for library: {lib_name}')
        # addon_logger.info(f'Library found: {lib_name}')   
    return lib

def try_switch_to_library(dir_path,lib_name,target_lib_name):
    
    lib =bpy.context.preferences.filepaths.asset_libraries.get(lib_name)
    if lib:
        #check if target lib path exists, if so we can switch to target lib
        lib_path = os.path.join(dir_path,target_lib_name)
        if os.path.exists(lib_path):
            lib.path = os.path.join(dir_path,target_lib_name)
            lib.name = target_lib_name
            
            # print(f'Library found and switched to {target_lib_name}')
            return True
        return False
            

def remove_library_from_blender(lib_name):
    if lib_name in bpy.context.preferences.filepaths.asset_libraries:
        lib =bpy.context.preferences.filepaths.asset_libraries.get(lib_name)
        lib_index = bpy.context.preferences.filepaths.asset_libraries.find(lib_name)
        if lib:
            if lib_index != -1:
                bpy.ops.preferences.asset_library_remove(index=lib_index)
                addon_logger.info(f'Removed library path from blender: {lib_name}')
                print(f'Removed library path from blender: {lib_name}')


def ensure_thumbnail_folder_exists(addon_prefs,upload_path):
    thumb_dir = os.path.join(upload_path,'thumbs')
    if not os.path.exists(thumb_dir):
        os.makedirs(thumb_dir)
    addon_prefs.thumb_path = thumb_dir

       

def get_asset_preview_path():
    addon_prefs = get_addon_name().preferences
    if os.path.exists(addon_prefs.thumb_path):
        return addon_prefs.thumb_path



def get_addon_blend_files_path():
    addon_path = get_addon_path()
    return os.path.join(addon_path,'bulls_plugin_assets','blend_files')

GITBOOKURL = 'https://bulltools.gitbook.io/bulltools-docs/'

class BU_OT_url_open(bpy.types.Operator):
    """More Information"""
    bl_idname = "bu.url_open"
    bl_label = "Documentation"
    bl_options = {'INTERNAL'}
    bl_description = "Open Documentation"
    url: bpy.props.StringProperty(
        name="URL",
        description="URL to open",
    )
    arg: bpy.props.StringProperty()
    @classmethod
    def description(cls, context, properties):
        if '#' in properties.url:
            base_url, anchor = properties.url.rsplit("#", 1)
        else:
            base_url, anchor = properties.url.rsplit("/", 1)
        
        return 'More Information: '+'\n'+ GITBOOKURL +'\n'+ anchor.upper()
    
    def execute(self, _context):
        import webbrowser
        if not self.url.startswith(("http://", "https://")):
            complete_url = "https://" + self.url
        else:
            complete_url = self.url
        webbrowser.open(complete_url)
        
        return {'FINISHED'}
    

def gitbook_link_getting_started(layout,anchor,text):
    gitbook = layout.operator('bu.url_open',text=text,icon='HELP')
    gitbook.url = GITBOOKURL+anchor


class INFO_OT_custom_dialog(bpy.types.Operator):
    bl_idname = "info.custom_dialog"
    bl_label = "Info Message Dialog"

    title: bpy.props.StringProperty()
    info_message: bpy.props.StringProperty()
    dont_show_again: bpy.props.BoolProperty()

        
    def _label_multiline(self,context, text, parent):
        panel_width = int(context.region.width)   # 7 pix on 1 character
        uifontscale = 9 * context.preferences.view.ui_scale
        max_label_width = int(panel_width // uifontscale)
        wrapper = textwrap.TextWrapper(width=50 )
        text_lines = wrapper.wrap(text=text)
        for text_line in text_lines:
            parent.label(text=text_line,)

    def draw(self, context):
        self.layout.label(text=self.title)
        
        intro_text = self.info_message
        self._label_multiline(
        context=context,
        text=intro_text,
        parent=self.layout
        )

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        if self.dont_show_again:
            pass
        else:
            return context.window_manager.invoke_props_dialog(self, width= 300)
        

    


classes =(
    INFO_OT_custom_dialog,
    WM_OT_RedrawArea,
    BU_OT_url_open,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    
