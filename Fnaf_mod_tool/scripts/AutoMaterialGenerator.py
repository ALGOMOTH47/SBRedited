import unreal
import re

TEXTURE_FOLDER = "/Game/Textures"
MATERIAL_FOLDER = "/Game/Materials"

asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
asset_registry.scan_paths_synchronous([TEXTURE_FOLDER], True)

def normalize_name(name):
    return re.sub(r'(basecolor|albedo|diffuse|normal|_n|nrm|norm|_orm|rough|roughness|_r|metal|metallic|_m)', '', name.lower())

def find_matching_texture(base_texture_name, all_assets, keywords):
    normalized_base = normalize_name(base_texture_name)
    for asset in all_assets:
        if asset.asset_class == "Texture2D":
            name = str(asset.asset_name)
            if any(k in name.lower() for k in keywords):
                if normalize_name(name) == normalized_base:
                    return asset.get_asset()
    return None

def create_material(texture_data, all_assets):
    texture = texture_data.get_asset()
    texture_name = texture.get_name()

    normal_texture = find_matching_texture(texture_name, all_assets, ["normal", "_n", "nrm", "norm", "_orm"])
    roughness_texture = find_matching_texture(texture_name, all_assets, ["rough", "roughness", "_r"])
    metallic_texture = find_matching_texture(texture_name, all_assets, ["metal", "metallic", "_m"])

    if not (normal_texture or roughness_texture or metallic_texture):
        print(f"⏭️ Skipping {texture_name}: No matching maps.")
        return

    material_name = f"{texture_name}_Material"
    material_path = f"{MATERIAL_FOLDER}/{material_name}"
    if unreal.EditorAssetLibrary.does_asset_exist(material_path):
        print(f"Material {material_name} already exists.")
        return

    material_factory = unreal.MaterialFactoryNew()
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        asset_name=material_name,
        package_path=MATERIAL_FOLDER,
        asset_class=unreal.Material,
        factory=material_factory
    )

    base_color_sample = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionTextureSample, -384, -200)
    base_color_sample.texture = texture
    unreal.MaterialEditingLibrary.connect_material_property(base_color_sample, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)

    if normal_texture:
        normal_sample = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionTextureSample, -384, 100)
        normal_sample.sampler_type = unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL
        normal_sample.texture = normal_texture
        unreal.MaterialEditingLibrary.connect_material_property(normal_sample, "RGB", unreal.MaterialProperty.MP_NORMAL)
        print(f"🔵 Added normal map: {normal_texture.get_name()}")

    if roughness_texture:
        rough_sample = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionTextureSample, -384, 300)
        rough_sample.texture = roughness_texture
        unreal.MaterialEditingLibrary.connect_material_property(rough_sample, "R", unreal.MaterialProperty.MP_ROUGHNESS)
        print(f"🟤 Added roughness map: {roughness_texture.get_name()}")

    if metallic_texture:
        metallic_sample = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionTextureSample, -384, 500)
        metallic_sample.texture = metallic_texture
        unreal.MaterialEditingLibrary.connect_material_property(metallic_sample, "R", unreal.MaterialProperty.MP_METALLIC)
        print(f"⚙️ Added metallic map: {metallic_texture.get_name()}")

    unreal.EditorAssetLibrary.save_asset(material.get_path_name())
    print(f"✅ Created material: {material.get_name()} from {texture_name}")

def main():
    all_assets = asset_registry.get_assets_by_path(TEXTURE_FOLDER, recursive=True)
    base_textures = []

    for a in all_assets:
        if a.asset_class == "Texture2D":
            name = str(a.asset_name).lower()
            if not any(x in name for x in ["normal", "_n", "nrm", "norm", "_orm", "rough", "roughness", "_r", "metal", "metallic", "_m"]):
                base_textures.append(a)

    print(f"🔍 Found {len(base_textures)} base textures.")
    for texture_data in base_textures:
        create_material(texture_data, all_assets)

main()
