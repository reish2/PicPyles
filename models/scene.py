import threading
import queue

import numpy as np
from models.geometry import SceneObject


class Scene:
    def __init__(self):
        self.objects = []
        self.lock = threading.Lock()
        self.update_queue = queue.Queue()

    def add_object(self, obj):
        self.update_queue.put(('add', obj))

    def remove_object(self, obj):
        self.update_queue.put(('remove', obj))

    def process_updates(self):
        updated = False
        while True:
            try:
                action, obj = self.update_queue.get_nowait()
                with self.lock:
                    if action == 'add':
                        self.objects.append(obj)
                    elif action == 'remove':
                        self.objects.remove(obj)
                self.update_queue.task_done()  # Indicate that the task is done
                updated = True
            except queue.Empty:
                break
        return updated

    def query(self, cam_pos, click_pos_3d):
        # Calculate the ray direction
        ray_direction = (click_pos_3d - cam_pos) / np.linalg.norm(click_pos_3d - cam_pos)
        world_near = cam_pos

        # Check for intersection with each object
        for obj in self.objects:
            if isinstance(obj, SceneObject):
                if self.ray_intersects_object(world_near, ray_direction, obj):
                    return obj

        return None

    def ray_intersects_object(self, ray_origin, ray_direction, obj):
        # Ray-plane intersection (assuming the object lies in the X-Y plane)
        obj_normal = np.array([0.0, 0.0, 1.0])  # Assuming the object is aligned with the Z-axis
        plane_point = obj.position  # A point on the plane (e.g., center of the object)

        denom = np.dot(obj_normal, ray_direction)
        if abs(denom) > 1e-6:  # Ensure the ray is not parallel to the plane
            d = np.dot(plane_point - ray_origin, obj_normal) / denom
            if d >= 0:
                intersection_point = ray_origin + ray_direction * d
                # Check if the intersection point is within the object's bounds
                if (obj.position[0] - obj.size[0] / 2 <= intersection_point[0] <= obj.position[0] + obj.size[0] / 2 and
                    obj.position[1] - obj.size[1] / 2 <= intersection_point[1] <= obj.position[1] + obj.size[1] / 2):
                    return True
        return False

    def inside_rectangle(self, obj, start, end):
        if isinstance(obj.vertices, np.ndarray):
            verts = obj.vertices
        else:
            verts = np.array([v[0] for v in obj.vertices])
        minx = min(start[0], end[0])
        maxx = max(start[0], end[0])
        miny = min(start[1], end[1])
        maxy = max(start[1], end[1])
        if ((verts[:,0] >= minx) & (verts[:,0] <= maxx) &
            (verts[:,1] >= miny) & (verts[:,1] <= maxy)).any():
            return True
        return False

    def query_inside(self, cam_pos, click_start_3d, click_end_3d):
        # Calculate the ray direction
        start_ray_direction = (click_start_3d - cam_pos) / np.linalg.norm(click_start_3d - cam_pos)
        end_ray_direction = (click_end_3d - cam_pos) / np.linalg.norm(click_end_3d - cam_pos)
        object_plane_distance = -cam_pos[2] #objects are placed at z=0

        start = start_ray_direction * object_plane_distance / start_ray_direction[2]
        end = end_ray_direction * object_plane_distance / end_ray_direction[2]

        # Check for intersection with each object
        objs = []
        for obj in self.objects:
            if isinstance(obj, SceneObject):
                if self.inside_rectangle(obj, start, end):
                    objs.append(obj)
        return objs