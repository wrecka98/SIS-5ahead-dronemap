import numpy as np
import open3d as o3d
import json
from datetime import datetime

# Load mesh and compute metrics
mesh = o3d.io.read_triangle_mesh("input files/point_cloud_clean.ply")
points = np.asarray(mesh.vertices)
min_z, max_z = np.min(points[:, 2]), np.max(points[:, 2])
bbox = mesh.get_axis_aligned_bounding_box().get_extent()

# Twin data (values only)
twin_data = {
    "height": float(max_z - min_z),
    "boundingBox": {
        "width": float(bbox[0]),
        "length": float(bbox[1]),
        "height": float(bbox[2])
    },
    "timestamp": datetime.utcnow().isoformat() + "Z"
}




with open("DTDL models/mesh_metrics_values.json", "w") as f:
    json.dump(twin_data, f, indent=2)

print("Twin data saved: mesh_metrics_values.json")