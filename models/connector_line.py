import numpy as np
from OpenGL.GL import *
from typing import List, Tuple
from models.scene_object import SceneObject
from tsp_solver.greedy import solve_tsp


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
        self.positions = positions
        self.order = self.solve_tsp()
        self.visible = True  # By default, the connector line is visible

    def toggle_visibility(self) -> None:
        """Toggle the visibility of the connector line."""
        self.visible = not self.visible

    def update_positions(self, positions):
        self.positions = positions

    def render_object(self) -> None:
        """Render the connector line if it's visible."""
        if not self.visible:
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
        distance_matrix = self.create_distance_matrix(self.positions/np.array((2.5,1.0,1.0)))

        # Solve the TSP using the greedy algorithm
        order = solve_tsp(distance_matrix)

        return order
