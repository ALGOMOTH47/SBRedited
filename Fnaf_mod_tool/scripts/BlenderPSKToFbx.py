import os
import bpy
from io_import_scene_unreal_psa_psk_280 import pskimport
#Change Me
psk_folder = r"H:\f\Fnaf_mod_tool\assetspsk"
fbx_output_folder = r"H:\f\Fnaf_mod_tool\exports"
bReorientBones = False

# ✅ Make sure the export folder exists
os.makedirs(fbx_output_folder, exist_ok=True)

for filename in os.listdir(psk_folder):
    if filename.lower().endswith(".psk"):
        filepath = os.path.join(psk_folder, filename)
        print(f"\n📥 Importing: {filepath}")

        try:
            # 🧹 Clear scene
            bpy.ops.object.select_all(action='SELECT')
            bpy.ops.object.delete(use_global=False)
            bpy.ops.outliner.orphans_purge(do_recursive=True)

            # 🔍 Track objects before import
            before = set(bpy.context.scene.objects)

            # 🎮 Import PSK
            pskimport(filepath, bReorientBones=bReorientBones)

            # 🔍 Track after import
            after = set(bpy.context.scene.objects)
            new_objects = list(after - before)
            imported_meshes = [obj for obj in new_objects if obj.type == 'MESH']

            print(f"🔍 Imported objects: {[obj.name for obj in imported_meshes]}")

            if not imported_meshes:
                print("⚠️ No valid mesh objects found! Skipping.")
                continue

            # 🗂 Build FBX path
            export_path = os.path.join(fbx_output_folder, filename.replace(".psk", ".fbx"))

            # ✅ Select new mesh objects only
            bpy.ops.object.select_all(action='DESELECT')
            for obj in imported_meshes:
                obj.select_set(True)
                bpy.context.view_layer.objects.active = obj

            print(f"📤 FBX export starting... {export_path}")

            # 🚀 Export to FBX
            bpy.ops.export_scene.fbx(
                filepath=export_path,
                use_selection=True,
                apply_unit_scale=True,
                apply_scale_options='FBX_SCALE_ALL',
                bake_space_transform=True
            )

            print(f"✅ Exported to: {export_path}")

        except Exception as e:
            print(f"❌ Failed on {filename}: {e}")
