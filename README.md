# eagle_database

Package used to track the main branch evolution of objects of interest using Subfind databases like those provided in EAGLE's public data release. This is intended to be used directly with the hdf5 database file. If you would like any additions, please feel free to reach out.

# Setup

To install the latest version, simply run:
```python
pip install git+https://github.com/VictorForouhar/eagle_database.git
```
This will install this package and all required dependencies.

# Usage

Locate the database file (e.g. Subfind.0.hdf5) and create a Database object:
```python
from eagle_database.database import Database
db = Database(path_to_database_file)
```
This will automatically make available information regarding the simulation (e.g. cosmology, output times, etc).

We can then specify a subgroup we want to track. For example, for a simulation with the 127th snapshot corresponding to z = 0, the main subgroup of the most massive FoF at that time is:
```python
# This creates a Subgroup object, where we specify the number of the  
# subgroup of interest and the snapshot where it exists, respectively
object_of_interest = db.track_object(0, 127) 
```

It is then simple to track the evolution of a given property as a function of time, via:
```python
# Mass evolution
object_of_interest['Mass']
# Star formation rate evolution
object_of_interest['StarFormationRate']
```

You can also plot how quantities evolve to quickly inspect whether they look reasonable.
'''python
# First parameter should be time coordinate (Redshift, aExp or tUniverse);
# second should be quantity of interest.
object_of_interest.plot_evolution('tUniverse', 'Mass')
'''
