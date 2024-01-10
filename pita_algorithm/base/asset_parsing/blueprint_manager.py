import copy
from pita_algorithm.base.asset_parsing.mujoco_object import MujocoObject
from pita_algorithm.base.asset_parsing.mujoco_loader import MujocoLoader


class BlueprintManager:
    """Creates and manages the Mujoco objects blueprints."""

    def __init__(self, config: dict, xml_dir: str) -> None:
        """Constructor of the BlueprintManager class.

        Parameters:
            config (dict): Configuration dictionary
            xml_dir (str): Path to the xml files
        """
        self.config: dict = config
        self.xml_dir: str = xml_dir
        self.mujoco_objects_blueprints: dict[str, MujocoObject] = {}
        self.mujoco_objects_rule_blueprints: dict[str, MujocoObject] = {}

    def get_object_blueprints(self):
        """Creates and manipulates the mujoco objects blueprints."""
        mujoco_loader = MujocoLoader(config_file=self.config, xml_dir=self.xml_dir)
        self.mujoco_objects_blueprints = mujoco_loader.get_mujoco_objects()

        for name, mujoco_object in self.mujoco_objects_blueprints.items():
            mujoco_object_copy = self._create_rule_blueprint(mujoco_object)
            self.mujoco_objects_rule_blueprints[name] = mujoco_object_copy

    @staticmethod
    def _create_rule_blueprint(mujoco_object: MujocoObject) -> MujocoObject:
        """Creates rule blueprints for Mujoco objects.

        Parameters:
            mujoco_object (MujocoObject): Mujoco object to be manipulated
        """
        mujoco_object_copy = copy.deepcopy(mujoco_object)
        joint_list = mujoco_object_copy.mjcf_obj.worldbody.body[0].find_all(
            "joint", immediate_children_only=True
        )
        if joint_list:
            if joint_list[0].tag == "freejoint" or joint_list[0].type == "free":
                joint_list[0].remove()
                mujoco_object_copy.mjcf_obj.worldbody.body[0].add(
                    "joint", limited="false"
                )
        else:
            mujoco_object_copy.mjcf_obj.worldbody.body[0].add("joint")
        return mujoco_object_copy
