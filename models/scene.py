import queue
import threading
from typing import List, Optional, Tuple, Any
import numpy as np
from PyQt5.QtCore import QTimer
from models.scene_object import SceneObject
from models.types import *

class Scene:
    """
    Manages the collection of objects in the scene and coordinates updates,
    queries, and interactions with those objects.
    """

    def __init__(self):
        """
        Initialize the Scene object, setting up the object list, a thread lock,
        an update queue, and a timer for processing updates.
        """
        self.objects: List[SceneObject] = []
        self.lock = threading.Lock()
        self.update_queue = queue.Queue()

        # Initialize the timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.run_process_updates)

    def start_update_timer(self, interval: int = 100) -> None:
        """
        Start the update timer with a specified interval in milliseconds.

        Args:
            interval (int): The interval at which to process updates, in milliseconds. Defaults to 100 ms.
        """
        self.update_timer.start(interval)

    def stop_update_timer(self) -> None:
        """Stop the update timer."""
        self.update_timer.stop()

    def sync_objects(self, obj_list: List[SceneObject]) -> None:
        """
        Synchronize the objects in the scene with a given list, adding new objects and removing missing ones.

        Args:
            obj_list (List[SceneObject]): The list of objects to synchronize with the scene.
        """
        for obj in obj_list:
            if obj not in self.objects:
                self.add_object(obj)
        for obj in self.objects:
            if obj not in obj_list:
                self.remove_object(obj)

    def run_process_updates(self) -> None:
        """Process updates when the timer fires, handling up to a specified maximum number of iterations."""
        self.process_updates(max_iterations=50)

    def add_object(self, obj: SceneObject) -> None:
        """
        Add an object to the scene.

        Args:
            obj (SceneObject): The object to add to the scene.
        """
        with self.lock:
            if obj not in self.objects:
                self.update_queue.put(('add', obj))

    def remove_object(self, obj: SceneObject) -> None:
        """
        Remove an object from the scene.

        Args:
            obj (SceneObject): The object to remove from the scene.
        """
        with self.lock:
            if obj in self.objects:
                self.update_queue.put(('remove', obj))

    def remove_all_objects(self) -> None:
        """Remove all objects from the scene."""
        with self.lock:
            for obj in self.objects:
                self.update_queue.put(('remove', obj))

    def process_updates(self, max_iterations: int = 10) -> bool:
        """
        Process pending updates to the scene, handling a specified maximum number of iterations.

        Args:
            max_iterations (int): The maximum number of updates to process. Defaults to 10.

        Returns:
            bool: True if updates were processed, False otherwise.
        """
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

    def query(self, cam_pos: Vec3, click_pos_3d: Vec3) -> Optional[SceneObject]:
        """
        Query the scene to find the object that intersects with a ray originating from the camera.

        Args:
            cam_pos (Vec3): The camera's position in 3D space.
            click_pos_3d (Vec3): The 3D position of the click in camera space.

        Returns:
            Optional[SceneObject]: The closest intersecting object, or None if no intersection occurs.
        """
        # Calculate the ray direction
        ray_direction = click_pos_3d / np.linalg.norm(click_pos_3d)
        world_near = cam_pos

        # Check for intersection with each object
        best_obj_candidate: Optional[SceneObject] = None
        for obj in self.objects:
            if isinstance(obj, SceneObject):
                if self.ray_intersects_object(world_near, ray_direction, obj):
                    if not best_obj_candidate or obj.position[2] > best_obj_candidate.position[2]:
                        best_obj_candidate = obj

        return best_obj_candidate

    def ray_intersects_object(self, ray_origin: Vec3, ray_direction: Vec3, obj: SceneObject) -> bool:
        """
        Determine if a ray intersects with a given object in the scene.

        Args:
            ray_origin (Vec3): The origin of the ray.
            ray_direction (Vec3): The direction of the ray.
            obj (SceneObject): The object to check for intersection.

        Returns:
            bool: True if the ray intersects the object, False otherwise.
        """
        object_plane_distance = -ray_origin[2]  # objects are placed at z=0
        intersection_point = ray_direction * object_plane_distance / ray_direction[2] - ray_origin

        # Check if the intersection point is within the object's bounds
        return (obj.position[0] - obj.size[0] / 2 <= intersection_point[0] <= obj.position[0] + obj.size[0] / 2 and
                obj.position[1] - obj.size[1] / 2 <= intersection_point[1] <= obj.position[1] + obj.size[1] / 2)


    def inside_rectangle(self, obj: SceneObject, start: Vec3, end: Vec3) -> bool:
        """
        Check if an object is inside a specified rectangular region.

        Args:
            obj (SceneObject): The object to check.
            start (Vec3): The starting corner of the rectangle.
            end (Vec3): The opposite corner of the rectangle.

        Returns:
            bool: True if the object is inside the rectangle, False otherwise.
        """
        verts = obj.vertices if isinstance(obj.vertices, np.ndarray) else np.array([v[0] for v in obj.vertices])
        minx, maxx = min(start[0], end[0]), max(start[0], end[0])
        miny, maxy = min(start[1], end[1]), max(start[1], end[1])
        return ((verts[:, 0] >= minx) & (verts[:, 0] <= maxx) &
                (verts[:, 1] >= miny) & (verts[:, 1] <= maxy)).any()

    def query_inside(self, cam_pos: Vec3, click_start_3d: Vec3, click_end_3d: Vec3) -> List[
        SceneObject]:
        """
        Query the scene to find all objects inside a rectangular region defined by two click positions.

        Args:
            cam_pos (Vec3): The camera's position in 3D space.
            click_start_3d (Vec3): The 3D position of the first corner of the rectangle.
            click_end_3d (Vec3): The 3D position of the opposite corner of the rectangle.

        Returns:
            List[SceneObject]: A list of objects inside the rectangular region.
        """
        # Calculate the ray direction
        start_ray_direction = click_start_3d / np.linalg.norm(click_start_3d)
        end_ray_direction = click_end_3d / np.linalg.norm(click_end_3d)
        object_plane_distance = -cam_pos[2]  # objects are placed at z=0

        start = start_ray_direction * object_plane_distance / start_ray_direction[2] - cam_pos
        end = end_ray_direction * object_plane_distance / end_ray_direction[2] - cam_pos

        # Check for intersection with each object
        return [obj for obj in self.objects if isinstance(obj, SceneObject) and self.inside_rectangle(obj, start, end)]
