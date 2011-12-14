def path_to_object(path, root, path_sep="."):

    """ Given a path, return the object from the hierarchy """

    path = path.split(path_sep)
    
    if not len(path):
        return None
    
    obj = None
    parent = root
    
    for elt in path[:-1]:
        parent = parent.get(elt, None)
        if parent is None:
            break
        
    if parent is not None:
        obj = parent.get(path[-1], None)        

    return obj


def object_to_path(obj, path_sep="."):

    """ Give an object, return the path """

    path = [self._id]

    _root = self

    while getattr(_root, "__parent__", None) is not None:
        _root = _root.__parent__
        path.append(_root.id)

    path.reverse()
            
    return path_sep.join(path[1:])
