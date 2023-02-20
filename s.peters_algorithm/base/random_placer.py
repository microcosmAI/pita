from abc import ABC, abstractmethod
from typing import Callable
from dm_control import mjcf
from peters_algorithm.utils.validator import Validator
from peters_algorithm.base.site import Site
import numpy as np
import copy

class GlobalNamespace:
    """Placeholder until we know how to name objects, before attaching them"""
    
    counter = 0
    
    @staticmethod
    def get():
        GlobalNamespace.counter += 1
        return str(GlobalNamespace.counter)
    
class MujocoObject:
    """placeholder until the real thing is implemented"""
    
    def __init__(self, name, mjcf_object):
        self.name = name
        self.mjcf_object = mjcf_object
        
class PlacerDistribution:
    '''Class for holing Distribution with specific parameterizations'''
    
    def __init__(self, distribution: Callable, *args):
        """
        Initialize a distribution for use in the RandomPlacer. The distribution 
        object will be called with *args as paramters. 
        Write for instance:
        `PlacerDistribution(np.random.default_rng().normal, 2, 1)` if you intend
        to sample from a normal distribution with loc=2 and scale = 1
        The samples will be drawn independently, which results in square like shapes.

        Parameters:
            distribution (Callable): distribution(*args) will be used for sampling values
            *args (sequence of floats): parameters for the random distribution
        """
        self.distribution = distribution
        self.parameters = args
        
    def __call__(self):
        """Returns two random samples, for the x and y axis respectively"""
        return self.distribution(*self.parameters), self.distribution(*self.parameters)
        
class Placer2DDistribution(PlacerDistribution):
    """Class for two dimensional distributions, otherwise equivalent to its parent class"""
    
    def __call__(self):
        """Returns a two dimensional random sample, for the x and y coordinates respectively"""
        
        x,y = self.distribution(*self.parameters)
        return (x, y)
        
class CircularUniformDistribution(PlacerDistribution):
    '''Class for holing Distribution with specific parameterizations'''
    
    def __init__(self, loc: float = 0, scale: float = 1.0):
        """
        Distribution for uniformly drawing samples from a circle

        Parameters:
            loc (float): minimal euclidean distance from the center
            scale (float): maximal euclidean distance from the center
        """
        self.loc = loc
        self.scale = scale
        
    def __call__(self):
        """Returns a two dimensional random sample, for the x and y coordinates respectively"""
        length = np.sqrt(np.random.uniform(self.loc, self.scale))
        angle = np.pi * np.random.uniform(0, 2)

        x = length * np.cos(angle)
        y = length * np.sin(angle)
        return x, y
    
    
    
class RandomPlacer:
    """A placer that is meant for procedural and random map generation"""
    
    '''The validator does not check, if the addition of an item is possible. Instead, after placement
    has failed for MAX_TRIES times, an error gets thrown. MAX_TRIES could alternatively be implemented
    dynamically, as a field of any Placer instantiation'''
    MAX_TRIES = 10000
    
    def __init__(self, distribution: PlacerDistribution = Placer2DDistribution(
        np.random.default_rng().multivariate_normal, (0,0), np.array([[0.5,0],[0,0.5]]))):
        """
        Initializes the Placer class. From the distribution a translation on the x and y axis will be
        respectively sampled. So the distribution of the to be placed objects is actually centered at
        the position of the original object plus a loc parameter of the distribution (if it has one).
        Note, that this will result in square shaped distributions, unless an explicitly circular
        distribution is used.
        
        Parameters:
            distribution (PlacerDistribution): distribution from which placement randomness will be sampled
        """
        self.distribution = distribution

    def add(self, site: Site, mujoco_object_blueprint: mjcf.RootElement, validator: list[Validator]):
        """
        Adds a mujoco object to a site by calling the sites add method.
        Possibly checks placement via the vlaidator.

        Parameters:
            site (Site): Site class instance where the object is added to
            mujoco_object_blueprint (mjcf.RootElement): To-be-placed mujoco object
            validator (Validator): Validator class instance used to check object placement
        """
        count = 0
        
        new_mjcf = copy.deepcopy(mujoco_object_blueprint)
        oldpos = new_mjcf.find("body", "object").geom[0].pos
        new_mjcf.find("body", "object").geom[0].pos = [*self.distribution(), oldpos[2]]
        new_object = MujocoObject(GlobalNamespace.get(), new_mjcf)
        
        while not all([val.validate(new_object) for val in validator]):
            count+=1
            if count >= RandomPlacer.MAX_TRIES:
                raise RuntimeError("Placement has failed {} times, please check your config.yaml".format(RandomPlacer.MAX_TRIES))
            new_mjcf.find("body", "object").geom[0].pos = [*self.distribution(), oldpos[2]]
            new_object = MujocoObject(new_object.name, new_mjcf)
        
        site.add(new_mjcf)

    def remove(self, site: Site, mujoco_object: mjcf.RootElement):
        """
        Removes a mujoco object from a site by calling the sites remove method.
        Possibly checks placement via the vlaidator.

        Parameters:
            site (Site): Site class instance where the object is removed from
            mujoco_object (mjcf.RootElement): To-be-removed mujoco object
        """
        site.remove(mujoco_object)
