import h5py

class database():

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