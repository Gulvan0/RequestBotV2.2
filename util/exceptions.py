class AlreadySatisfiesError(Exception):
    """
    An exception occurring when the intended action will have no effect due to the current state of the entity being modified
    """