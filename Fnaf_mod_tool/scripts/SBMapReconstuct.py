import unreal
import json
import os

json_path = r"H:/f/Fnaf_mod_tool/fnaf9/Content/json/MainLobby/NightLighting/MAP_MainLobby_LightsOff.json"
content_root = "/Game/"
content_dir = "H:/f/Fnaf_mod_tool/fnaf9/Content/"

with open(json_path, 'r') as f:
    data = json.load(f)

# === Global Configuration ===
GLOBAL_SCALE = unreal.Vector(100.0, 100.0, 100.0)

spawned_count = 0

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

for obj in data:
    props = obj.get("Properties") or {}
    obj_type = obj.get("Type", "")
    name = obj.get("Name", "Unnamed")

    location = props.get("RelativeLocation", {"X": 0, "Y": 0, "Z": 0})
    rotation = props.get("RelativeRotation", {"Pitch": 0, "Yaw": 0, "Roll": 0})
    scale = props.get("RelativeScale3D", {"X": 1, "Y": 1, "Z": 1})

    loc = unreal.Vector(location["X"], location["Y"], location["Z"])
    rot = unreal.Rotator(rotation["Roll"], rotation["Pitch"], rotation["Yaw"])  # Adjusted axes
    scl = GLOBAL_SCALE

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

            # Search entire content directory for matching .uasset
            found_path = None
            for root, _, files in os.walk(content_dir):
                for file in files:
                    if file.lower() == mesh_file.lower() + ".uasset":
                        relative = os.path.relpath(root, content_dir).replace("\\", "/")
                        found_path = content_root + relative + "/" + mesh_file
                        break
                if found_path:
                    break

            if found_path:
                static_mesh = unreal.EditorAssetLibrary.load_asset(found_path)
                if static_mesh:
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
                    print(f"⚠️ Asset found but failed to load: {found_path} for {name}")
            else:
                print(f"❌ Could not locate asset for mesh: {mesh_file} (original path: {mesh_path_raw})")
        continue

    if obj_type == "BlockingVolume":
        actor_class = unreal.BlockingVolume
    else:
        actor_class = unreal.Actor

    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(actor_class, loc, rot)
    if actor:
        actor.set_actor_scale3d(scl)
        actor.set_actor_label(name)
        spawned_count += 1
        print(f"✅ Spawned {obj_type}: {name} at {loc} with rotation {rot} and scale {scl}")

print(f"🎉 Total objects placed: {spawned_count}")
