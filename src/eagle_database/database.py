import h5py
import numpy as np
from numpy import argsort
from .subgroup import Subgroup
from .helper_functions import quick_search
from astropy.cosmology import FlatLambdaCDM

class Database:

    def __init__(self, path):
        '''
        Creates an EAGLE database object.

        Parameters
        ----------
        database_path : str
            Path to where the database is located.

        Returns
        --------
        None
        '''
        
        # Path to database
        self._path = path

        # Open database file
        self.file = h5py.File(self._path, 'r') 
        
        # Dict where data is stored
        self.data = {}

        # Get properties and info of the simulation used to build dataset
        self.get_properties()
        self.get_scale_factors()
        self.get_redshifts()
        self.number_snapshots = len(self.aExp)

        # Specify cosmology and get age of the universe at output snapshots
        self.set_cosmology()
        self.get_tUniverse()

        # Generate sorter array for GalaxyID to speed up array search further
        # down the line 
        self.get_galaxyID_sorter()
    
    def load(self, group_name):
        '''
        Helper function used to load data if it is not available yet.

        Parameters
        -----------
        group_name : str
            Name of the group we want to load data from

        Returns
        --------
        None
        '''

        if group_name not in self.data:
            try: 
                self.data[group_name] = self.file[group_name][()]
            except:
                raise KeyError('No group with specified name is present in this file.')

    def __getitem__(self, group_name):
        self.load(group_name)
        return self.data[group_name]

    def get_properties(self):
        '''
        Creates dictionary containing information about the simulation.        
        '''
        self.properties = {}
        for key, value in self.file['Header'].attrs.items():
            self.properties[key] = value 

    def get_scale_factors(self):
        '''
        Retrieves expansion factors of each simulation snapshot.        
        '''
        self.aExp = self.file['FileInfo/ExpansionFactorAtSnap'][()]

    def get_redshifts(self):
        '''
        Retrieves redshifts of each simulation snapshot.        
        '''
        self.redshifts = 1 / self.aExp - 1

    def get_galaxyID_sorter(self):
        '''
        Creates a sorter array to sort galaxyID values in ascending order.
        Used for searching more quickly further down the line. 
        '''
        self._galaxyID_sorter = argsort(self['MergerTree/GalaxyID'])

    def set_cosmology(self):
        self.cosmology = FlatLambdaCDM(H0=self.properties['HubbleParam'] * 100, Om0=self.properties['Omega0'])

    def get_tUniverse(self):
        # Given in Gyrs
        self.tUniverse = self.cosmology.age(self.redshifts).value

    def get_all_nodeIndex(self):
        '''
        Returns a list of lists, each holding the nodeIndex for a given snapshot number. 
        Useful for converting between nodeIndex and subgroup number + snapshot_number
        '''

        self._all_nodeIndex = []
        for snap in range(self.number_snapshots):
            self._all_nodeIndex.append(self['MergerTree/nodeIndex'][self['MergerTree/nodeIndex'] // 1e12 == snap])

    def track_subgroup(self, subgroup_number, snap_number):
        '''
        Creates a Subgroup class.

        Parameters
        ----------
        subgroup_number : int
            Absolute position of the subgroup in the subfind catalogue.
        snap_number : int
            Number of the snapshot where this subgroup is located.
        '''
        self.subgroup = Subgroup(self, subgroup_number, snap_number)
        return self.subgroup

    #===========================================================
    # Methods to convert among nodeIndex,
    # snapshot_number + subgroup, galaxyID
    #===========================================================

    def galaxyID_to_nodeIndex(self, galaxyID):
        '''
        Returns the nodeIndex corresponding to this galaxyID. 

        Parameters
        -----------
        galaxyID : int
            The galaxyID of a given object.

        Returns 
        -----------
        int
            The correspoding nodeIndex
        '''
        return self['MergerTree/nodeIndex'][quick_search(self['MergerTree/GalaxyID'], galaxyID, self._galaxyID_sorter)]

    def nodeIndex_to_galaxyID(self, nodeIndex):
        '''
        Returns the galaxyID corresponding to this nodeIndex. 

        Parameters
        -----------
        nodeIndex : int
            The nodeIndex of a given object.

        Returns 
        -----------
        int
            The correspoding galaxyID
        '''
        return self['MergerTree/GalaxyID'][quick_search(self['MergerTree/nodeIndex'], nodeIndex)]

    def nodeIndex_to_subgroup(self, nodeIndex):
        '''
        Parameters
        -----------
        nodeIndex : int
            The nodeIndex of a given object. 

        Returns
        ------------
        tuple
            A tupple containing two integers, corresponding to the subgroup number and the snapshot
            number of the object, respectively.
        '''     
        try: self._all_nodeIndex
        except: self.get_all_nodeIndex()
        
        if isinstance(nodeIndex,np.ndarray):
            subgroup_list = []
            for i in range(len(nodeIndex)):
                subgroup_list.append(self.nodeIndex_to_subgroup(nodeIndex[i])) 
            return subgroup_list
        else: 
            snapshot_number = int(nodeIndex // 1e12)
            subgroup_number = quick_search(self._all_nodeIndex[snapshot_number], nodeIndex )[0]
            return subgroup_number, snapshot_number
    
    def subgroup_to_nodeIndex(self, subgroup_number, snapshot_number):
        '''
        Returns the nodeIndex corresponding to the specified combination of subgroup + snapshot
        number.

        Parameters
        -----------
        subgroup_number : int 
            The positional index of this group in the corresponding SUBFIND catalogue.
        snapshot_number : int
            The snapshot where this object exists.

        Returns
        -----------
        int 
            The nodeIndex of the specified group.
            
        '''
        try: self._all_nodeIndex
        except: self.get_all_nodeIndex()
        
        return self._all_nodeIndex[snapshot_number][subgroup_number]