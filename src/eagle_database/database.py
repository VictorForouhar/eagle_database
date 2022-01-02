import h5py
from .subgroup import Subgroup

class Database():

    def __init__(self, path):
        """
        Creates an EAGLE database object.

        Parameters
        ----------
        database_path : str
            Path to where the database is located.

        Returns
        --------
        None
        """
        
        # Path to database
        self._path = path

        # Open database file
        self.file = h5py.File(self._path, 'r') 
        
        # Dict where data is stored
        self.data = {}

        # Get properties of the simulation used to build dataset
        self.get_properties()

        # TODO: Generate sorter arrays 
    
    def load(self, group_name):
        """
        Helper function used to load data if it is not available yet.

        Parameters
        -----------
        group_name : str
            Name of the group we want to load data from

        Returns
        --------
        None
        """

        if group_name not in self.data:
            try: 
                self.data[group_name] = self.file[group_name][()]
            except:
                raise KeyError('No group with specified name is present in this file.')

    def __getitem__(self, group_name):
        self.load(group_name)
        return self.data[group_name]

    def get_properties(self):
        self.properties = {}
        for key, value in self.file['Header'].attrs.items():
            self.properties[key] = value 

    def track_subgroup(self, subgroup_number, snap_number):
        self.subgroup = Subgroup(self, subgroup_number, snap_number)
        return self.subgroup

    # Subgroup is a good choice for a property (perhaps not!)
    # @property
    # def subgroup(self):
    #     return self._subgroup

    # @subgroup.setter
    # def set_subgroup(self, subgroup_number, snap_number):
    #     self._subgroup = Subgroup(self, subgroup_number, snap_number)

    # @subgroup.deleter
    # def delete_subgroup(self):
    #     del self._subgroup