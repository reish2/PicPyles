from typing import Tuple
import numpy as np

# vectors
Vec3 = np.ndarray

# Type alias for a single vertex and texture coordinate pair
VertexWithTexCoord = Tuple[np.ndarray, Tuple[float, float]]