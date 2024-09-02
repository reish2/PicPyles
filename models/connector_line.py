import numpy as np
from OpenGL.GL import *
from typing import List, Tuple
from models.scene_object import SceneObject
import pyqtree


def calculate_total_distance(order, points):
    return sum(np.linalg.norm(points[order[i]] - points[order[i - 1]]) for i in range(len(order)))


def find_outlier_edges(points: np.ndarray, order: list) -> list:
    """
    Identify the outlier edges in the current TSP order based on the given threshold.

    Args:
        points (np.ndarray): An array of shape (n, 3) representing the points in 3D space.
        order (list): The current order of points in the TSP solution.
        threshold (float): The distance threshold to consider an edge as an outlier.

    Returns:
        list: A list of tuples representing the indices of outlier edges.
    """
    # Calculate the differences between consecutive points in the order
    ordered_points = points[order]
    diffs = np.diff(ordered_points, axis=0)

    # Calculate the Euclidean distance for each edge
    distances = np.linalg.norm(diffs, axis=1)

    # Find the indices where the distance exceeds the threshold
    thresh = np.percentile(distances,0.5) * 2
    outlier_indices = np.where(distances > thresh)[0]

    # Create a list of outlier edge indices
    outliers = [(i, i + 1) for i in outlier_indices]

    return outliers


def two_opt(points, order):
    improved = True
    best_order = order
    best_distance = calculate_total_distance(best_order, points)

    # Identify outlier edges
    outliers = find_outlier_edges(points, best_order)

    iters = 0
    while improved and iters<32:
        improved = False
        for i in range(1, len(order) - 1):
            if any(i in outlier for outlier in outliers):
                continue  # Skip outlier edges initially

            for j in range(i + 1, len(order)):
                if j - i == 1:
                    continue  # adjacent edges, no swap needed
                new_order = best_order[:i] + best_order[i:j][::-1] + best_order[j:]
                new_distance = calculate_total_distance(new_order, points)
                if new_distance < best_distance:
                    best_order = new_order
                    best_distance = new_distance
                    improved = True
        iters +=1

        # Reintroduce outlier edges
        outliers = []  # Now allow all edges to be considered

    return best_order


def build_quadtree(points: np.ndarray, boundary: Tuple[float, float, float, float]) -> pyqtree.Index:
    """
    Build a quadtree from the given points using pyqtree.

    Args:
        points (np.ndarray): An array of shape (n, 3) with the positions of the objects.
        boundary (Tuple[float, float, float, float]): The boundary of the quadtree.

    Returns:
        pyqtree.Index: The built quadtree.
    """
    qt = pyqtree.Index(bbox=boundary)
    for i, point in enumerate(points):
        x, y = point[:2]
        qt.insert(i, (x, y, x, y))
    return qt


def tsp_nearest_neighbor(points: np.ndarray, quadtree: pyqtree.Index) -> List[int]:
    """
    Solve the TSP problem using a nearest neighbor heuristic with a quadtree.

    Args:
        points (np.ndarray): An array of shape (n, 3) representing the points in 3D space.
        quadtree (pyqtree.Index): A quadtree containing the points.

    Returns:
        List[int]: The order of points for the TSP solution.
    """
    num_points = len(points)
    unvisited = set(range(num_points))
    current = 0
    order = [current]
    unvisited.remove(current)

    while unvisited:
        # Define a slightly larger bounding box to find close neighbors
        bbox = (points[current][0] - 2, points[current][1] - 2,
                points[current][0] + 2, points[current][1] + 2)

        # Find all neighbors within this bounding box
        neighbors = quadtree.intersect(bbox)

        # Filter out already visited points
        neighbors = [idx for idx in neighbors if idx in unvisited]

        if not neighbors:
            # If no neighbors are found in the small box, expand the search area
            neighbors = list(unvisited)

        # Find the nearest unvisited neighbor
        nearest_point = min(neighbors, key=lambda idx: np.linalg.norm(points[current] - points[idx]))
        current = nearest_point
        order.append(current)
        unvisited.remove(current)

    return order


class ConnectorLine(SceneObject):
    def __init__(self, positions: np.ndarray, color: Tuple[float, float, float] = (1.0, 0.0, 0.0)) -> None:
        """
        Initialize the ConnectorLine with the given positions and order.

        Args:
            positions (np.ndarray): An array of shape (n, 2) with the positions of the objects.
            order (List[int]): A list of indices representing the order of the objects.
            color (Tuple[float, float, float]): The color of the connector line. Defaults to red.
        """
        super().__init__(position=(0.0, 0.0, 0.0), size=(0.0, 0.0, 0.0), color=color)
        self.has_thumbnail = True # Hack to ignore the thumbnail check
        self.positions = positions.copy()
        self.order = self.solve_tsp()
        self.visible = True  # By default, the connector line is visible

    def toggle_visibility(self) -> None:
        """Toggle the visibility of the connector line."""
        self.visible = not self.visible

    def update_positions(self, positions):
        self.positions = positions.copy()

    def render_object(self) -> None:
        """Render the connector line if it's visible."""
        if not self.visible or np.max(self.order) > len(self.positions):
            return

        glColor3f(*self.color)  # Use the color specified in the initialization
        glLineWidth(2.0)  # Set the line width

        glBegin(GL_LINE_STRIP)
        for index in self.order:
            x, y, z = self.positions[index]
            glVertex3f(x, y, z+0.01)
        glEnd()

    def create_distance_matrix(self, positions: np.ndarray) -> np.ndarray:
        """
        Creates a distance matrix for the given positions.

        Args:
            positions (np.ndarray): An array of shape (n, 2) containing the positions.

        Returns:
            np.ndarray: An array of shape (n, n) containing the pairwise distances.
        """
        distances = np.linalg.norm(positions[:, None] - positions, axis=-1)
        return distances

    def solve_tsp(self) -> List[int]:
        """
        Solves the Traveling Salesman Problem for the image center coordinates.

        Returns:
            List[int]: A list of indices representing the order of objects.
        """
        # distance_matrix = self.create_distance_matrix(self.positions/np.array((2.5,1.0,1.0)))
        #
        # # Solve the TSP using the greedy algorithm
        # order = solve_tsp(distance_matrix)
        points = self.positions/np.array((2.5,1.0,1.0))
        boundary = np.concatenate((np.min(points[:,:2],axis=0),np.max(points[:,:2],axis=0)))
        quadtree = build_quadtree(points, boundary)
        order = tsp_nearest_neighbor(points, quadtree)
        # order = two_opt(points, order)

        return order
