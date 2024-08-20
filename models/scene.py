import queue
import threading

import numpy as np

from models.scene_objects import SceneObject


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
        ray_direction = click_pos_3d / np.linalg.norm(click_pos_3d)
        world_near = cam_pos

        # Check for intersection with each object
        for obj in self.objects:
            if isinstance(obj, SceneObject):
                if self.ray_intersects_object(world_near, ray_direction, obj):
                    return obj

        return None

    def ray_intersects_object(self, ray_origin, ray_direction, obj):
        object_plane_distance = -ray_origin[2]  # objects are placed at z=0
        intersection_point = ray_direction * object_plane_distance / ray_direction[2] - ray_origin
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
        if ((verts[:, 0] >= minx) & (verts[:, 0] <= maxx) &
            (verts[:, 1] >= miny) & (verts[:, 1] <= maxy)).any():
            return True
        return False

    def query_inside(self, cam_pos, click_start_3d, click_end_3d):
        # Calculate the ray direction
        start_ray_direction = click_start_3d / np.linalg.norm(click_start_3d)
        end_ray_direction = click_end_3d / np.linalg.norm(click_end_3d)
        object_plane_distance = -cam_pos[2]  # objects are placed at z=0

        start = start_ray_direction * object_plane_distance / start_ray_direction[2] - cam_pos
        end = end_ray_direction * object_plane_distance / end_ray_direction[2] - cam_pos

        # Check for intersection with each object
        objs = []
        for obj in self.objects:
            if isinstance(obj, SceneObject):
                if self.inside_rectangle(obj, start, end):
                    objs.append(obj)
        return objs
