import unreal
import json
import os
import tkinter as tk
from tkinter import filedialog

# === TKINTER File Dialog ===
def choose_json_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Choose JSON File",
        filetypes=[("JSON Files", "*.json")],
        initialdir="H:/f/Fnaf_mod_tool/fnaf9/Content/json"
    )
    return file_path if file_path else None

# === Create or Load Map with JSON filename ===
def create_new_map_from_json(json_path, save_path="/Game/Maps/RecreatedMaps"):
    json_name = os.path.splitext(os.path.basename(json_path))[0]
    full_asset_path = f"{save_path}/{json_name}"

    if unreal.EditorAssetLibrary.does_asset_exist(full_asset_path):
        unreal.EditorLevelLibrary.load_level(full_asset_path)
        unreal.log_warning(f"⚠️ Level {full_asset_path} already exists. Loading it instead.")
        return full_asset_path

    if not unreal.EditorAssetLibrary.does_directory_exist(save_path):
        unreal.EditorAssetLibrary.make_directory(save_path)

    try:
        unreal.EditorLevelLibrary.new_level(full_asset_path)
        unreal.log(f"✅ Created new empty map at {full_asset_path}")
        return full_asset_path
    except Exception as e:
        unreal.log_error(f"❌ Failed to create the level: {e}")
        return None

# === Main ===
json_path = choose_json_file()
if not json_path:
    unreal.log_error("No JSON file selected. Aborting.")
    raise SystemExit()

with open(json_path, 'r') as f:
    data = json.load(f)

content_root = "/Game/"
content_dir = "H:/f/Fnaf_mod_tool/fnaf9/Content/"
GLOBAL_SCALE = unreal.Vector(1.0, 1.0, 1.0)
spawned_count = 0

created_map = create_new_map_from_json(json_path)
if not created_map:
    unreal.log_error("Could not create or load a map. Aborting.")
    raise SystemExit()

# === Helper functions ===

def safe_scale(vec):
    return unreal.Vector(
        max(min(vec.x, 100.0), 0.01),
        max(min(vec.y, 100.0), 0.01),
        max(min(vec.z, 100.0), 0.01)
    )

def create_convex_brush(convex_elem, location, rotation, scale, name):
    verts = convex_elem.get("VertexData", [])
    if not verts:
        return None
    brush = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.Brush, location, rotation)
    if not brush:
        return None
    converted = [unreal.Vector(v["X"] * scale.x, v["Y"] * scale.y, v["Z"] * scale.z) for v in verts]
    builder = unreal.BrushBuilder()
    builder.poly_flag = 0
    builder.vertices = converted
    brush.set_actor_label(name + "_Brush")
    print(f"🧱 Created convex brush for {name} with {len(converted)} verts")
    return brush

def spawn_light_actor(obj_type, props, name, rot, scl):
    loc_data = props.get("RelativeLocation", {"X": 0, "Y": 0, "Z": 0})
    loc = unreal.Vector(loc_data["X"], loc_data["Y"], loc_data["Z"])
    light_class_map = {
        "PointLightComponent": unreal.PointLight,
        "SpotLightComponent": unreal.SpotLight,
        "RectLightComponent": unreal.RectLight
    }
    actor_class = light_class_map.get(obj_type)
    if not actor_class:
        return
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(actor_class, loc, rot)
    if not actor:
        return
    actor.set_actor_scale3d(scl)
    actor.set_actor_label(name)
    components = actor.get_components_by_class(unreal.LightComponentBase)
    light_component = components[0] if components else None
    if not light_component:
        return
    if props.get("Intensity") is not None:
        light_component.set_editor_property("intensity", props["Intensity"])
    if props.get("CastShadows") is not None:
        light_component.set_editor_property("cast_shadows", props["CastShadows"])
    color_data = props.get("LightColor")
    if color_data:
        color = unreal.Color(
            r=int(color_data["R"]),
            g=int(color_data["G"]),
            b=int(color_data["B"]),
            a=int(color_data.get("A", 255))
        )
        light_component.set_editor_property("light_color", color)
    for prop_name in ["SourceRadius", "SoftSourceRadius", "SourceWidth", "SourceHeight"]:
        if props.get(prop_name) is not None:
            uprop = prop_name[0].lower() + prop_name[1:]
            try:
                light_component.set_editor_property(uprop, props[prop_name])
            except Exception as e:
                print(f"⚠️ Could not set property '{uprop}': {e}")
    print(f"💡 Spawned {obj_type}: {name} at {loc} with rotation {rot} and scale {scl}")

# === Main spawning loop ===

for obj in data:
    props = obj.get("Properties") or {}
    obj_type = obj.get("Type", "")
    name = obj.get("Name", "Unnamed")
    location = obj.get("RelativeLocation") or props.get("RelativeLocation", {"X": 0, "Y": 0, "Z": 0})
    rotation = obj.get("RelativeRotation") or props.get("RelativeRotation", {"Pitch": 0, "Yaw": 0, "Roll": 0})
    scale = props.get("RelativeScale3D", {"X": 1, "Y": 1, "Z": 1})
    loc = unreal.Vector(location["X"], location["Y"], location["Z"])
    rot = unreal.Rotator(rotation["Roll"], rotation["Pitch"], rotation["Yaw"])
    scl = unreal.Vector(scale["X"], scale["Y"], scale["Z"]) * GLOBAL_SCALE

    if obj_type in ["PointLightComponent", "SpotLightComponent", "RectLightComponent"]:
        spawn_light_actor(obj_type, props, name, rot, scl)
        spawned_count += 1
        continue

    if obj_type == "BlockingVolume" and "BodySetup" in props:
        convex_elems = props["BodySetup"].get("AggGeom", {}).get("ConvexElems", [])
        for i, convex in enumerate(convex_elems):
            create_convex_brush(convex, loc, rot, scl, f"{name}_Part{i}")
            spawned_count += 1
        continue

    elif "StaticMesh" in props and isinstance(props["StaticMesh"], dict):
        mesh_path_raw = props["StaticMesh"].get("ObjectPath", "")
        if mesh_path_raw:
            mesh_file = os.path.basename(mesh_path_raw).split(".")[0]
            print(f"🕵️‍♂️ Searching for mesh: {mesh_file}")
            found_path = None
            for root, _, files in os.walk(content_dir):
                for file in files:
                    if file.lower() == mesh_file.lower() + ".uasset":
                        relative = os.path.relpath(root, content_dir).replace("\\", "/")
                        found_path = content_root + relative + "/" + mesh_file
                        print(f"✅ Found asset: {found_path}")
                        break
                if found_path:
                    break
            if found_path:
                static_mesh = unreal.EditorAssetLibrary.load_asset(found_path)
                if static_mesh and isinstance(static_mesh, unreal.StaticMesh):
                    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, loc, rot)
                    if actor:
                        actor.set_actor_scale3d(scl)
                        actor.set_actor_label(name)
                        smc = actor.static_mesh_component
                        smc.set_static_mesh(static_mesh)
                        smc.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
                        print(f"🧱 Placed StaticMeshActor: {name} using mesh {found_path}")
                        spawned_count += 1
                    else:
                        print(f"❌ Failed to spawn actor for {name}")
                else:
                    print(f"⚠️ Asset found but not a valid StaticMesh: {found_path} for {name}")
            else:
                print(f"❌ Could not locate asset for mesh: {mesh_file} (original path: {mesh_path_raw})")
        continue

    actor_class = unreal.BlockingVolume if obj_type == "BlockingVolume" else unreal.Actor
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(actor_class, loc, rot)
    if actor:
        actor.set_actor_scale3d(scl)
        actor.set_actor_label(name)
        spawned_count += 1
        print(f"✅ Spawned {obj_type}: {name} at {loc} with rotation {rot} and scale {scl}")

print(f"🎉 Total objects placed: {spawned_count}")
