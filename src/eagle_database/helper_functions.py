import numpy as np

def quick_search(input_array, search_values, sorter_array=None):
    '''
    Performs a rapid search for specified values through an
    array sorted in ascending value order. Returns positional
    index used to retrieve said values.

    Paramters
    ----------
    input_array : ArrayType
        Array we want to search through
    search_values : ArrayType
        Values we want to find inside said array
    sorter_array : ArrayType, opt
        Array used to sort input_array, e.g. np.argsort(input_array). 
        This is used if input_array is not sorted.

    Returns
    ----------
    positional_index : ArrayType or None
        Array of indicies used to retrieve values that have been searched,
        i.e. search_values = input_array[positional_index].
        If no matches have been found, returns None
    '''

    # Search from the left and right sides
    left  = np.searchsorted(input_array,search_values,side='left' , sorter = sorter_array)
    right = np.searchsorted(input_array,search_values,side='right', sorter = sorter_array)

    # Matches  
    positional_index = left[left!= right]

    # Return array only if one or more matches have been found 
    if (len(positional_index) != 0):
        if sorter_array is not None:
            return sorter_array[positional_index]
        else:
            return positional_index