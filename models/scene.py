import queue
import threading
from typing import List, Optional, Tuple, Any
import numpy as np
from PyQt5.QtCore import QTimer

from models.connector_line import ConnectorLine
from models.image_object import ImageObject
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

        self.connector_line = None

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

    def add_connector_line_object(self, obj: ConnectorLine) -> None:
        """
        Add a connector line object to the scene.

        Args:
            obj (ConnectorLine): The connector line object to be added.
        """
        self.connector_line = obj
        self.add_object(self.connector_line)

    def remove_connector_line_object(self) -> None:
        """
        Remove the connector line object from the scene, if it exists.
        """
        if self.connector_line:
            self.remove_object(self.connector_line)
            self.connector_line = None

    def update_connector_line_positions(self, positions: np.ndarray) -> None:
        """
        Update the positions of the connector line.

        Args:
            positions (np.ndarray): A list of new positions for the connector line.
        """
        if self.connector_line:
            self.connector_line.update_positions(positions)


    def toggle_connector_line_visibility(self) -> None:
        """
        Toggle the visibility of the connector line.
        """
        if self.connector_line:
            self.connector_line.toggle_visibility()

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
        Check if an object is inside or overlaps with a specified rectangular region.

        Args:
            obj (SceneObject): The object to check.
            start (Vec3): The starting corner of the rectangle.
            end (Vec3): The opposite corner of the rectangle.

        Returns:
            bool: True if the object is inside or overlaps with the rectangle, False otherwise.
        """
        # Calculate the object's AABB
        verts = obj.vertices if isinstance(obj.vertices, np.ndarray) else np.array([v[0] for v in obj.vertices])
        obj_minx, obj_maxx = np.min(verts[:, 0]), np.max(verts[:, 0])
        obj_miny, obj_maxy = np.min(verts[:, 1]), np.max(verts[:, 1])

        # Calculate the rectangle's bounds
        rect_minx, rect_maxx = min(start[0], end[0]), max(start[0], end[0])
        rect_miny, rect_maxy = min(start[1], end[1]), max(start[1], end[1])

        # Check for AABB overlap (bounding box intersection)
        overlap_x = obj_maxx >= rect_minx and obj_minx <= rect_maxx
        overlap_y = obj_maxy >= rect_miny and obj_miny <= rect_maxy

        if overlap_x and overlap_y:
            return True

        # Optionally, check for edge intersection (this is more expensive but accurate)
        if self.edges_intersect(verts, start, end):
            return True

        # Finally, is start and end entirely contained inside the object
        if  (obj_minx < rect_minx < obj_maxx and obj_miny < rect_miny < obj_maxy) and (
                obj_minx < rect_maxx < obj_maxx and obj_miny < rect_maxy < obj_maxy):
           return True

        return False

    def edges_intersect(self, verts: np.ndarray, start: Vec3, end: Vec3) -> bool:
        """
        Check if any edge of the object intersects with the rectangle.

        Args:
            verts (np.ndarray): The vertices of the object.
            start (Vec3): The starting corner of the rectangle.
            end (Vec3): The opposite corner of the rectangle.

        Returns:
            bool: True if any edge intersects, False otherwise.
        """
        rect_edges = [
            (start, (end[0], start[1])),
            ((end[0], start[1]), end),
            (end, (start[0], end[1])),
            ((start[0], end[1]), start)
        ]

        # Loop over each edge of the object and the rectangle
        for i in range(len(verts)):
            obj_edge_start = verts[i]
            obj_edge_end = verts[(i + 1) % len(verts)]
            for rect_edge_start, rect_edge_end in rect_edges:
                if self.do_edges_intersect(obj_edge_start, obj_edge_end, rect_edge_start, rect_edge_end):
                    return True

        return False

    def do_edges_intersect(self, p1, q1, p2, q2) -> bool:
        """
        Helper function to check if two line segments (p1q1 and p2q2) intersect.

        Args:
            p1, q1: Start and end points of the first line segment.
            p2, q2: Start and end points of the second line segment.

        Returns:
            bool: True if the segments intersect, False otherwise.
        """

        def orientation(p, q, r):
            val = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
            if val == 0:
                return 0  # Collinear
            elif val > 0:
                return 1  # Clockwise
            else:
                return 2  # Counterclockwise

        o1 = orientation(p1, q1, p2)
        o2 = orientation(p1, q1, q2)
        o3 = orientation(p2, q2, p1)
        o4 = orientation(p2, q2, q1)

        # General case
        if o1 != o2 and o3 != o4:
            return True

        # Special cases (collinear points)
        return False

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
        return self.query_inside_rectangle(start,end)

    def query_inside_rectangle(self, start: Vec3, end: Vec3) -> List[SceneObject]:
        """
        Query the scene to find all objects inside a rectangular region defined by two click positions.

        Args:
            start (Vec3): The starting corner of the rectangle.
            end (Vec3): The opposite corner of the rectangle.

        Returns:
            List[SceneObject]: A list of objects inside the rectangular region.
        """

        # Check for intersection with each object
        return set(obj for obj in self.objects if isinstance(obj, SceneObject) and self.inside_rectangle(obj, start, end))


    def get_object_positions(self) -> np.ndarray:
        """
        Extracts the center coordinates from the objects in the scene.

        Returns:
            np.ndarray: An array of shape (n, 2) where n is the number of objects.
        """
        return np.array([obj.position for obj in self.objects if isinstance(obj,ImageObject) and obj.object_type=="image"])
