def path_to_object(path, root, path_sep="/"):

    """ Given a path, return the object from the hierarchy """

    path = path.split(path_sep)[1:]
    path = [p for p in path if p]

    if not len(path):
        return root

    obj = None
    parent = root

    for elt in path[:-1]:
        parent = parent.get(elt, None)
        if parent is None:
            break

    if parent is not None:
        obj = parent.get(path[-1], None)

    return obj


def object_to_path(obj, path_sep="/", as_list=False):

    """ Give an object, return the path """

    path = [obj._id]

    _root = obj

    while getattr(_root, "__parent__", None) is not None:
        _root = _root.__parent__
        path.append(_root.id)

    path.reverse()

    if as_list:
        return path[1:]
    else:
        value = path_sep.join([''] + path[1:])
        if not value.startswith(path_sep):
            value = path_sep + value
        return value
