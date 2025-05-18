import unreal
import json
import os

# Texture suffix mapping to material properties and sampler types
TEXTURE_USAGE_MAP = {
    'bsm':  {'input': unreal.MaterialProperty.MP_BASE_COLOR, 'sampler_type': unreal.MaterialSamplerType.SAMPLERTYPE_COLOR},
    'Base':  {'input': unreal.MaterialProperty.MP_BASE_COLOR, 'sampler_type': unreal.MaterialSamplerType.SAMPLERTYPE_COLOR},
    'Norm':  {'input': unreal.MaterialProperty.MP_NORMAL, 'sampler_type': unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL},
    'nrm':  {'input': unreal.MaterialProperty.MP_NORMAL, 'sampler_type': unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL},
    'rough':{'input': unreal.MaterialProperty.MP_ROUGHNESS, 'sampler_type': unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR},
    'metal':{'input': unreal.MaterialProperty.MP_METALLIC, 'sampler_type': unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR},
    'ao':   {'input': unreal.MaterialProperty.MP_AMBIENT_OCCLUSION, 'sampler_type': unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR},
}

def create_material_with_textures(material_name, texture_names, material_path='/Game/Materials'):
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.MaterialFactoryNew()
    material_asset_path = f"{material_path}/{material_name}"

    if unreal.EditorAssetLibrary.does_asset_exist(material_asset_path):
        material = unreal.EditorAssetLibrary.load_asset(material_asset_path)
        print(f"✏️ Editing existing material: {material_name}")
    else:
        material = asset_tools.create_asset(material_name, material_path, unreal.Material, factory)
        print(f"✨ Created new material: {material_name}")

    # Create nodes from textures
    for tex_name in texture_names:
        try:
            texture_asset_path = f"/Game/ShadingAssets/Textures/{tex_name}"
            texture = unreal.load_asset(texture_asset_path)
            if not texture:
                print(f"❌ Texture not found: {texture_asset_path}")
                continue

            texture_sample = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionTextureSample)
            texture_sample.texture = texture

            # Guess the suffix
            suffix = tex_name.split('_')[-1].lower()
            usage = TEXTURE_USAGE_MAP.get(suffix)
            if not usage:
                print(f"⚠️ Could not determine material input for {tex_name}")
                unreal.MaterialEditingLibrary.delete_material_expression(material, texture_sample)
                continue

            texture_sample.sampler_type = usage['sampler_type']
            try:
                unreal.MaterialEditingLibrary.connect_material_property(texture_sample, '', usage['input'])
                print(f"🔗 Connected '{tex_name}' to {usage['input'].name} with sampler {usage['sampler_type'].name}")
            except Exception as e:
                print(f"🚫 Failed to connect '{tex_name}': {e}")
                unreal.MaterialEditingLibrary.delete_material_expression(material, texture_sample)

        except Exception as e:
            print(f"❌ Error processing texture {tex_name}: {e}")

    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    print("📂 Material saved.")

def find_referenced_textures(json_file):
    with open(json_file, 'r') as file:
        data = json.load(file)

        def search_for_textures(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key == 'ReferencedTextures' and isinstance(value, list):
                        print(f"🔍 Found 'ReferencedTextures' ({len(value)} textures):")
                        textures = []
                        for texture in value:
                            path = texture.get('ObjectPath', '')
                            base_name = os.path.splitext(os.path.basename(path))[0]
                            print(f"  - {texture.get('ObjectName', 'Unknown')} | {path}")
                            textures.append(base_name)
                        return textures
                    result = search_for_textures(value)
                    if result:
                        return result
            elif isinstance(obj, list):
                for item in obj:
                    result = search_for_textures(item)
                    if result:
                        return result
            return []

        return search_for_textures(data)

# Change this path to your actual JSON file
json_path = r"H:\f\Fnaf_mod_tool\json\Maps\_cable_color_tiling.json"
material_name = "M_Cable_Color_Tiling"

print(f"📄 Checking: {os.path.basename(json_path)}")
textures = find_referenced_textures(json_path)
if textures:
    create_material_with_textures(material_name, textures)
else:
    print("⚠️ No textures found in JSON.")
