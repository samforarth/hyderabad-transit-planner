"""
Configuration settings for the Hyderabad Transit Planner.

This module uses the 12-Factor App methodology by loading configuration 
from the environment instead of hardcoding them. This makes it easier 
to change settings between development and production without touching code.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import quote_plus


class Settings(BaseSettings):
    # Database connection parameters
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "root"
    DB_NAME: str = "hyderabad_transit"

    # Nominatim API settings for geocoding
    NOMINATIM_USER_AGENT: str = "HyderabadTransitPlanner/1.0 (transit@example.com)"
    NOMINATIM_BASE_URL: str = "https://nominatim.openstreetmap.org"
    
    # Bounding box for Hyderabad (approximate bounds to restrict searches to relevant areas)
    HYDERABAD_VIEWBOX: str = "78.2376,17.5878,78.6224,17.2886"

    model_config = SettingsConfigDict(env_file=".env")

    @property
    def DATABASE_URL(self) -> str:
        # We use quote_plus to safely encode the password in case it contains special characters
        encoded_password = quote_plus(self.DB_PASSWORD)
        # Using PyMySQL driver as it's synchronous and straightforward for this use case
        return f"mysql+pymysql://{self.DB_USER}:{encoded_password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


settings = Settings()
