import os.path

from pita_algorithm.base.asset_parsing.parser import Parser
from pita_algorithm.base.asset_parsing.mujoco_object import MujocoObject


class MujocoLoader:
    """Loads mujoco objects as dictionary."""

    def __init__(self, *, config_file: dict, xml_dir: str):
        """Constructor of MujocoLoader class.

        Parameters:
            config_file (dict): Dictionary of user defined configurations
            xml_dir (str): Path to directory containing xml-file of objects
        """
        self.config_file = config_file
        self.xml_dir = xml_dir

    def get_mujoco_objects(self) -> dict:
        """Loads all objects defined in config file as mujoco-objects.

        Returns:
            mujoco_dict (dict): World objects defined in config are loaded and wrapped in mujoco-object
        """
        obj_dict = self._get_object_infos()
        mujoco_dict = self._get_mujoco_dict(obj_dict)

        return mujoco_dict

    def _get_object_infos(self) -> dict:
        """Reads config file and returns dictionary of all objects

        Returns:
            obj_dict (dict): Contains information about all objects
        """
        obj_dict = {}

        for name, params in self.config_file["Environment"].items():
            if name == "Borders":
                name = "Border"
                obj_dict[name] = params

        for name, params in self.config_file["Environment"]["Objects"].items():
            obj_dict[name] = params

        for area, obj_in_area in self.config_file["Areas"].items():
            for name, params in self.config_file["Areas"][area]["Objects"].items():
                obj_dict[name] = params

        return obj_dict

    def _get_mujoco_dict(self, obj_dict: dict) -> dict:
        """Loads and parses xml to mjcf and combines all information to mujoco-objects.

        Parameters:
            obj_dict (dict): Contains information about all objects

        Returns:
            mujoco_dict (dict): Dictionary of all objects as mujoco-objects
        """
        mujoco_dict = {}

        for obj, params in obj_dict.items():
            obj_xml_path = os.path.join(self.xml_dir, obj + ".xml")
            mjcf = Parser.get_mjcf(xml_path=obj_xml_path)
            obj_type, attachable, tags = self._read_params(params)

            mujoco_obj = MujocoObject(
                name=obj,
                xml_id="",
                mjcf_obj=mjcf,
                obj_type=obj_type,
                attachable=attachable,
                color=None,
                size=None,
                tags=tags,
            )

            mujoco_dict[obj] = mujoco_obj

        return mujoco_dict

    @staticmethod
    def _read_params(params: list[dict]) -> tuple:
        """Reads object specific parameters from config file.

        Parameters:
            params (list[dict]): List of object specific parameters given as dictionary

        Returns:
            obj_type (str): Type of object
            attachable (bool): True if object can be attached to a container-type object
            tags (list): List of user specified tags for the object
        """
        obj_type = None
        attachable = None
        tags = None

        if not params == None:
            for dict_ in params:
                if "type" in dict_.keys():
                    obj_type = dict_["type"]
                if "attachable" in dict_.keys():
                    attachable = dict_["attachable"]
                if "tags" in dict_.keys():
                    tags = dict_["tags"]

        return obj_type, attachable, tags