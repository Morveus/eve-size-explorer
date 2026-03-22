#!/usr/bin/env python3
"""Render a side-view profile of an EVE ship model on transparent background."""

import os
import sys
import numpy as np
import trimesh
from PIL import Image

# Use EGL for headless GPU rendering (NVIDIA)
os.environ["PYOPENGL_PLATFORM"] = "egl"
import pyrender


def render_side_view(mesh_path, output_path, width=1024, height=1024):
    """Render a side-view (profile) of a 3D model.

    Tries all 6 camera directions and picks the one showing the widest silhouette.
    """
    # Load mesh
    mesh = trimesh.load(mesh_path)
    if isinstance(mesh, trimesh.Scene):
        mesh = mesh.dump(concatenate=True)

    # Center the mesh at origin
    mesh.vertices -= mesh.centroid
    bounds = mesh.bounds
    extents = bounds[1] - bounds[0]
    max_extent = max(extents)
    print(f"  Extents: X={extents[0]:.2f} Y={extents[1]:.2f} Z={extents[2]:.2f}")

    # Try 6 views, pick the one with the best side-view (widest + tallest)
    views = [
        ("X+", [1, 0, 0], [0, 1, 0]),   # look along +X
        ("X-", [-1, 0, 0], [0, 1, 0]),  # look along -X
        ("Y+", [0, 1, 0], [0, 0, -1]),  # look along +Y
        ("Y-", [0, -1, 0], [0, 0, 1]),  # look along -Y
        ("Z+", [0, 0, 1], [0, 1, 0]),   # look along +Z
        ("Z-", [0, 0, -1], [0, 1, 0]),  # look along -Z
    ]

    best_img = None
    best_pixels = 0
    best_name = ""

    for name, direction, up in views:
        img = render_from_direction(mesh, direction, up, max_extent, width, height)
        if img is None:
            continue

        # Count non-transparent pixels
        alpha = np.array(img)[:, :, 3]
        pixel_count = np.count_nonzero(alpha > 10)

        print(f"  View {name}: {pixel_count} visible pixels")
        if pixel_count > best_pixels:
            best_pixels = pixel_count
            best_img = img
            best_name = name

    if best_img is None:
        print("  ERROR: No view produced any output!")
        return False

    print(f"  Best view: {best_name} ({best_pixels} pixels)")

    # Crop to content with padding
    bbox = best_img.getbbox()
    if bbox:
        pad = 20
        bbox = (
            max(0, bbox[0] - pad),
            max(0, bbox[1] - pad),
            min(width, bbox[2] + pad),
            min(height, bbox[3] + pad),
        )
        best_img = best_img.crop(bbox)

    best_img.save(output_path)
    print(f"  Saved: {output_path} ({best_img.size[0]}x{best_img.size[1]})")
    return True


def render_from_direction(mesh, direction, up, max_extent, width, height):
    """Render mesh from a given camera direction."""
    scene = pyrender.Scene(bg_color=[0, 0, 0, 0], ambient_light=[0.4, 0.4, 0.4])

    material = pyrender.MetallicRoughnessMaterial(
        baseColorFactor=[0.6, 0.65, 0.7, 1.0],
        metallicFactor=0.4,
        roughnessFactor=0.6,
    )

    mesh_pr = pyrender.Mesh.from_trimesh(mesh, material=material)
    scene.add(mesh_pr)

    # Key light
    light1 = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=4.0)
    lp1 = look_at([max_extent, max_extent * 0.5, max_extent * 0.3], [0, 0, 0], [0, 1, 0])
    scene.add(light1, pose=lp1)

    # Fill light
    light2 = pyrender.DirectionalLight(color=[0.6, 0.7, 0.9], intensity=2.0)
    lp2 = look_at([-max_extent, -max_extent * 0.3, max_extent], [0, 0, 0], [0, 1, 0])
    scene.add(light2, pose=lp2)

    # Camera
    dist = max_extent * 2.0
    eye = np.array(direction, dtype=float) * dist
    cam_pose = look_at(eye, [0, 0, 0], up)

    ortho_mag = max_extent * 0.55
    camera = pyrender.OrthographicCamera(xmag=ortho_mag, ymag=ortho_mag)
    scene.add(camera, pose=cam_pose)

    try:
        renderer = pyrender.OffscreenRenderer(width, height)
        color, _ = renderer.render(scene, flags=pyrender.RenderFlags.RGBA)
        renderer.delete()
        return Image.fromarray(color)
    except Exception as e:
        print(f"  Render error: {e}")
        return None


def look_at(eye, target, up):
    """Create a 4x4 look-at camera matrix (OpenGL convention)."""
    eye = np.array(eye, dtype=float)
    target = np.array(target, dtype=float)
    up = np.array(up, dtype=float)

    forward = target - eye
    forward = forward / np.linalg.norm(forward)

    right = np.cross(forward, up)
    if np.linalg.norm(right) < 1e-6:
        # up and forward are parallel, pick different up
        up = np.array([1, 0, 0])
        right = np.cross(forward, up)
    right = right / np.linalg.norm(right)

    true_up = np.cross(right, forward)
    true_up = true_up / np.linalg.norm(true_up)

    mat = np.eye(4)
    mat[:3, 0] = right
    mat[:3, 1] = true_up
    mat[:3, 2] = -forward
    mat[:3, 3] = eye
    return mat


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <model.stl> <output.png>")
        sys.exit(1)

    render_side_view(sys.argv[1], sys.argv[2])
