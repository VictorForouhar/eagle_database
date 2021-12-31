import h5py

class database():

    def __init__(self, database_path):
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
        self.path = database_path

        # Open database file
        self.file = h5py.File(database_path, 'r') 
        
        # Dict where data is stored
        self.data = {}