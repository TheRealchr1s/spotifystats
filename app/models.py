"""Response models for various API endpoints"""

from lib2to3.pytree import Base

from pydantic import BaseModel


class SpotifyNotAuthorizedError(Exception):
    """Raised when the user is not yet authorized to access the Spotify API"""

    pass
