from typing import Any
import os
from .db import update_role_info_to_db, find_star_role_name_list, find_star_role_name_list, find_star_role_name_list


class Config:
    def __new__(cls) -> Any:
        if not hasattr(Config, "_instance"):
            Config._instance = super().__new__(cls)
        return Config._instance

    def __init__(self) -> None:
        update_role_info_to_db()
        Config.star_3_roles = find_star_role_name_list("3")
        Config.star_4_roles = find_star_role_name_list("4")
        Config.star_5_roles = find_star_role_name_list("5")
