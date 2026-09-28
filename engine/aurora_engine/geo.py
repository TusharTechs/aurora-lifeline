"""Small geodesy helpers on a spherical Earth."""

import numpy as np
from numpy.typing import ArrayLike, NDArray

EARTH_RADIUS_KM = 6371.0088  # IUGG mean radius


def haversine_km(
    lat1: ArrayLike, lon1: ArrayLike, lat2: ArrayLike, lon2: ArrayLike
) -> NDArray[np.float64]:
    """Great-circle distance in km between points given in degrees. Broadcasts like numpy."""
    p1, l1, p2, l2 = (np.radians(np.asarray(x, dtype=np.float64)) for x in (lat1, lon1, lat2, lon2))
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin((l2 - l1) / 2) ** 2
    return np.asarray(
        2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0))), dtype=np.float64
    )
