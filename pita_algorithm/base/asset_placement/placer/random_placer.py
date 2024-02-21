import logging
import random
from tqdm import tqdm
from typing import Union
from pita_algorithm.utils.general_utils import Utils
from pita_algorithm.base.world_sites.area import Area
from pita_algorithm.base.asset_placement.validator import Validator
from pita_algorithm.base.world_sites.abstract_site import AbstractSite
from pita_algorithm.base.asset_parsing.mujoco_object import MujocoObject
from pita_algorithm.base.asset_placement.placer.abstract_placer import AbstractPlacer
from pita_algorithm.utils.object_property_randomization import (
    ObjectPropertyRandomization,
)
from pita_algorithm.base.asset_placement.distributions.abstract_placer_distribution import (
    AbstractPlacerDistribution
)
from pita_algorithm.base.asset_placement.distributions.random_walk_distribution import RandomWalkDistribution
from pita_algorithm.base.asset_placement.distributions.circular_uniform_distribution import CircularUniformDistribution
from pita_algorithm.base.asset_placement.distributions.multivariate_normal_distribution import MultivariateNormalDistribution
from pita_algorithm.base.asset_placement.distributions.multivariate_uniform_distribution import MultivariateUniformDistribution


class RandomPlacer(AbstractPlacer):
    """Places objects in a random manner."""

    # The validator does not check, if the addition of an item is possible.
    # Instead, after placement has failed for MAX_TRIES times, an error is thrown.
    MAX_TRIES = 10000

    def __init__(self):
        """Constructor of the RandomPlacer class."""
        super().__init__()

    def add(
        self,
        site: AbstractSite,
        mujoco_object_blueprint: MujocoObject,
        validators: list[Validator],
        amount: tuple[int, int] = (1, 1),
        coordinates: None = None,
        distribution: AbstractPlacerDistribution = None,
        z_rotation_range: Union[tuple[int, int], None] = None,
        color_groups: Union[tuple[int, int], None] = None,
        size_groups: Union[tuple[int, int], None] = None,
        size_value_range: Union[tuple[int, int], None] = None,
        asset_pool: Union[list, None] = None,
        mujoco_objects_blueprints: Union[dict, None] = None,
    ) -> None:
        """Adds a mujoco object to a site by calling the sites add method
        after checking placement via the validator.

        Parameters:
            site (AbstractSite): Site class instance where the object is added to
            mujoco_object_blueprint (MujocoObject): To-be-placed mujoco object
            validators (list[Validator]): List of validators used to check object placement
            amount (tuple[int, int]): Range of possible amount of objects to be placed
            coordinates (None): Required signature of abstract parent class for fixed_placer
            distribution (Distribution): Distribution for object to sample from for random placement
            z_rotation_range (Union[tuple[int, int], None]): Range of degrees for z-axis rotation
            color_groups (Union[tuple[int, int], None]): Range of possible different colors for object
            size_groups (Union[tuple[int, int], None]): Range of possible different sizes for object
            size_value_range (Union[tuple[float, float], None]): Range of size values allowed in randomization
            asset_pool (Union[list, None]): List of xml-names of assets which should be sampled from
            mujoco_objects_blueprints (Union[dict, None]): Dictionary of all objects as mujoco-objects
        """
        logger = logging.getLogger()

        # Distribution mapping
        mapping_distribution_pyclass = {
            "RandomWalkDistribution": RandomWalkDistribution(parameters={
                "step_size_range": [2, 4],
                "bounds": [-site.size[0], site.size[0], -site.size[1], site.size[1]]
            }),
            "CircularUniformDistribution": CircularUniformDistribution(parameters={
                "loc": 0.0,
                "scale": min(site.size[0], site.size[1])
            }),
            "MultivariateNormalDistribution": MultivariateNormalDistribution(parameters={
                "mean": [0, 0],
                "cov": [[site.size[0], 0], [0, site.size[1]]]
            }),
            "MultivariateUniformDistribution": MultivariateUniformDistribution(parameters={
                "low": [-site.size[0], -site.size[1]],
                "high": [site.size[0], site.size[1]],
            })
        }

        # Sample from amount range
        amount: int = ObjectPropertyRandomization.sample_from_amount(amount=amount)

        # Check for mismatch of objects and color-/size-groups in configuration
        self._check_user_input(
            color_groups=color_groups, size_groups=size_groups, amount=amount
        )

        # Get colors rgba
        colors_for_placement = ObjectPropertyRandomization.get_random_colors(
            amount=amount, color_groups=color_groups
        )

        # Get object size
        sizes_for_placement = ObjectPropertyRandomization.get_random_sizes(
            amount=amount, size_groups=size_groups, size_value_range=size_value_range
        )

        # Get object z-axis rotation
        z_rotation_for_placement = ObjectPropertyRandomization.get_random_rotation(
            amount=amount, z_rotation_range=z_rotation_range
        )

        for i in tqdm(range(amount)):
            # Get new clean blueprint
            mutable_mujoco_object_blueprint = self._copy(mujoco_object_blueprint)

            # Sample from asset pool if asset_pool is given by user
            if asset_pool is not None:
                asset_name = random.choice(asset_pool).split(".xml")[0]
                mutable_mujoco_object_blueprint = self._copy(
                    mujoco_objects_blueprints[asset_name]
                )

            if colors_for_placement is not None:
                # Apply colors to objects
                mutable_mujoco_object_blueprint.color = colors_for_placement[i]

            if sizes_for_placement is not None:
                # Apply sizes to objects
                mutable_mujoco_object_blueprint.size = sizes_for_placement[i]

            if z_rotation_for_placement is not None:
                # Apply rotation to z-axis of object
                rotation = mutable_mujoco_object_blueprint.rotation
                if rotation is None:
                    rotation = [0, 0, z_rotation_for_placement[i]]
                else:
                    rotation[2] = z_rotation_for_placement[i]
                mutable_mujoco_object_blueprint.rotation = rotation

            # Save size of object for setting the z coordinate
            new_z_position = mutable_mujoco_object_blueprint.size[0]

            # Sample a new position
            mutable_mujoco_object_blueprint.position = (
                *mapping_distribution_pyclass[distribution](),
                new_z_position,
            )

            count = 0
            # Ask every validator for approval until all approve or MAX_TRIES is reached,
            # then throw error
            while not all(
                [
                    validator.validate(
                        mujoco_object=mutable_mujoco_object_blueprint, site=site
                    )
                    for validator in validators
                ]
            ):
                count += 1
                if count >= RandomPlacer.MAX_TRIES:
                    logger.error(
                        "Placement of object '{}' in site '{}' has failed '{}' times, please check your config.yaml".format(
                            mutable_mujoco_object_blueprint.name,
                            site.name,
                            RandomPlacer.MAX_TRIES,
                        )
                    )
                    raise RuntimeError(
                        "Placement of object '{}' in site '{}' has failed '{}' times, please check your config.yaml".format(
                            mutable_mujoco_object_blueprint.name,
                            site.name,
                            RandomPlacer.MAX_TRIES,
                        )
                    )
                # If placement is not possible, sample a new position
                mutable_mujoco_object_blueprint.position = (
                    *mapping_distribution_pyclass[distribution](),
                    new_z_position,
                )

            # If Site is area type, offset the coordinates to the boundaries
            if isinstance(site, Area):
                reference_boundaries = (
                    (-site.environment.size[0], -site.environment.size[0]),
                    (site.environment.size[1], site.environment.size[1]),
                )
                mutable_mujoco_object_blueprint.position = (
                    Utils.offset_coordinates_to_boundaries(
                        mutable_mujoco_object_blueprint.position,
                        site.boundary,
                        reference_boundaries=reference_boundaries,
                    )
                )

            # Keep track of the placement in the validators
            for validator in validators:
                validator.add(mutable_mujoco_object_blueprint)

            # Add the object to the site
            site.add(mujoco_object=mutable_mujoco_object_blueprint)

    def remove(self, site: AbstractSite, mujoco_object: MujocoObject) -> None:
        """Removes a mujoco object from a site by calling the sites remove method.

        Parameters:
            site (AbstractSite): Site class instance where the object is removed from
            mujoco_object (MujocoObject): To-be-removed mujoco object
        """
        site.remove(mujoco_object=mujoco_object)
