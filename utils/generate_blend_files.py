import bpy, os, zipfile
from . import addon_info
from .addon_logger import addon_logger


def add_asset_tags(asset):
    if bpy.app.version >= (4, 0, 0):
        asset_metadata = asset.metadata
    else:
        asset_metadata = asset.asset_data
    blender_version_tag = f'Blender_{bpy.app.version_string}'
    if 'Original' not in asset_metadata.tags:
        asset_metadata.tags.new(name='Original')
    if blender_version_tag not in asset_metadata.tags:
        asset_metadata.tags.new(name=blender_version_tag)


def new_GeometryNodes_group():
    '''Create a new empty node group that can be used in a GeometryNodes modifier.'''
    node_group = bpy.data.node_groups.new('GeometryNode_Placeholder', 'GeometryNodeTree')
    group_input = node_group.nodes.new('NodeGroupInput')
    group_input.location = (0, 0)
    group_output = node_group.nodes.new('NodeGroupOutput')
    group_output.location = (300, 0)
    if bpy.app.version < (4, 0, 0):
        node_group.outputs.new('NodeSocketGeometry', 'Geometry')
        node_group.inputs.new('NodeSocketGeometry', 'Geometry')
    else:
        node_group.interface.new_socket(name="Geometry", description="geometry_input", in_out="INPUT", socket_type="NodeSocketGeometry")
        node_group.interface.new_socket(name="Geometry", description="geometry_output", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    node_group.links.new(group_input.outputs['Geometry'], group_output.inputs['Geometry'])
    return node_group


def new_node_group_empty(original_name, nodetype):
    node_group = bpy.data.node_groups.new(original_name, nodetype)
    group_input = node_group.nodes.new('NodeGroupInput')
    group_input.location = (0, 0)
    group_output = node_group.nodes.new('NodeGroupOutput')
    group_output.location = (300, 0)
    node_group.links.new(group_input.outputs[0], group_output.inputs[0])
    return node_group


def generate_placeholder_file(asset, original_name):
    try:
        addon_logger.info('generating placeholder asset')
        ph_asset = None
        if asset.id_type == 'OBJECT':
            ph_asset = bpy.data.objects.new(original_name, None)
            return ph_asset
        elif asset.id_type == 'COLLECTION':
            ph_asset = bpy.data.collections.new(original_name)
            return ph_asset
        elif asset.id_type == 'MATERIAL':
            ph_asset = bpy.data.materials.new(original_name)
            return ph_asset
        elif asset.id_type == 'NODETREE':
            nodetype = asset.local_id.bl_idname
            if nodetype in ('ShaderNodeTree', 'CompositorNodeTree'):
                ph_asset = new_node_group_empty(original_name, nodetype)
                return ph_asset
            elif nodetype == 'GeometryNodeTree':
                ph_asset = new_GeometryNodes_group()
                if ph_asset:
                    ph_asset.name = original_name
                return ph_asset
            else:
                raise Exception('Node group asset_type not supported')
        else:
            return None
    except Exception as e:
        if ph_asset:
            remove_placeholder_asset(ph_asset)
        message = f"Error generating placeholder {e}"
        log_exception(message)
        raise Exception(message)


def copy_metadata_to_placeholder(asset, ph_asset):
    try:
        if bpy.app.version >= (4, 0, 0):
            ph_metadata = ph_asset.asset_data
            asset_metadata = asset.metadata
        else:
            ph_metadata = ph_asset.asset_data
            asset_metadata = asset.asset_data
        if 'Placeholder' not in ph_metadata.tags:
            ph_metadata.tags.new(name='Placeholder')
        attributes_to_copy = ['copyright', 'catalog_id', 'description', 'tags', 'license', 'author']
        for attr in attributes_to_copy:
            if hasattr(asset_metadata, attr) and getattr(asset_metadata, attr):
                if attr == 'tags':
                    for tag in getattr(asset_metadata, attr):
                        if tag.name not in ('Original', 'Premium'):
                            ph_metadata.tags.new(name=tag.name)
                else:
                    setattr(ph_metadata, attr, getattr(asset_metadata, attr))
    except Exception as e:
        message = f'error copying metadata: {e}'
        log_exception(message)
        raise Exception(message)


def zip_directory(folder_path):
    try:
        root_dir, asset_folder = os.path.split(folder_path)
        if root_dir.endswith(f'{os.sep}Placeholders'):
            zip_path = os.path.join(root_dir, f'PH_{asset_folder}.zip')
        else:
            zip_path = os.path.join(root_dir, f'{asset_folder}.zip')
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(folder_path):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, root_dir)
                    zipf.write(full_path, rel_path)
        return zip_path
    except Exception as e:
        message = f'error zipping directory: {e}'
        log_exception(message)
        raise Exception(message)


def remove_placeholder_asset(ph_asset):
    asset_types = addon_info.type_mapping()
    data_collection = getattr(bpy.data, asset_types[ph_asset.bl_rna.identifier])
    data_collection.remove(ph_asset)


def log_exception(message):
    print(message)
    addon_logger.error(message)
