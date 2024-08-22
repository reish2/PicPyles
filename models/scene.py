import queue
import threading

import numpy as np
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

from models.scene_objects import SceneObject


class Scene:
    def __init__(self):
        self.objects = []
        self.lock = threading.Lock()
        self.update_queue = queue.Queue()

        # Initialize the timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.run_process_updates)
        self.update_timer.start(500)  # 500 milliseconds

    def run_process_updates(self):
        # Process updates when the timer fires
        self.process_updates(max_iterations=10)

    def add_object(self, obj):
        with self.lock:
            if obj not in self.objects:
                self.update_queue.put(('add', obj))

    def remove_object(self, obj):
        with self.lock:
            if obj in self.objects:
                self.update_queue.put(('remove', obj))

    def remove_all_objects(self):
        with self.lock:
            for obj in self.objects:
                self.update_queue.put(('remove', obj))

    def process_updates(self, max_iterations=10):
        updated = False
        iterations = 0

        while iterations < max_iterations:
            try:
                with self.lock:
                    action, obj = self.update_queue.get_nowait()
                    if action == 'add':
                        self.objects.append(obj)
                    elif action == 'remove':
                        if obj in self.objects:
                            self.objects.remove(obj)
                self.update_queue.task_done()
                updated = True
                iterations += 1
            except queue.Empty:
                break

        return updated

    def query(self, cam_pos, click_pos_3d):
        # Calculate the ray direction
        ray_direction = click_pos_3d / np.linalg.norm(click_pos_3d)
        world_near = cam_pos

        # Check for intersection with each object
        best_obj_candidate = None
        for obj in self.objects:
            if isinstance(obj, SceneObject):
                if self.ray_intersects_object(world_near, ray_direction, obj):
                    if not best_obj_candidate:
                        best_obj_candidate = obj
                    elif obj.position[2] > best_obj_candidate.position[2]:
                        best_obj_candidate = obj

        return best_obj_candidate

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
