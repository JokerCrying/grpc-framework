import importlib


def symbol_by_name(name, aliases=None, imp=None, package=None,
                   sep='.', default=None, **kwargs):
    """Dynamically import and return a symbol (class, function, etc.) by its name.
    
    Args:
        name (str or object): Name of the symbol to import, in format "module.path:object_name" or "module.path.object_name".
                             If not a string, it is returned as-is.
        aliases (dict, optional): Dictionary mapping aliases to actual symbol names.
        imp (callable, optional): Import function to use, defaults to importlib.import_module.
        package (str, optional): Parent package to use for relative imports.
        sep (str, optional): Separator to use when splitting module and object name, defaults to '.'.
        default (object, optional): Default value to return if import fails.
        **kwargs: Additional arguments to pass to the import function.
        
    Returns:
        The imported symbol (class, function, etc.) or the default value if import fails.
        
    Raises:
        ImportError: If the module or symbol cannot be found and no default is provided.
        AttributeError: If the symbol does not exist in the module and no default is provided.
    """
    aliases = {} if not aliases else aliases
    if imp is None:
        imp = importlib.import_module

    if not isinstance(name, str):
        return name  # already a class

    name = aliases.get(name) or name
    sep = ':' if ':' in name else sep
    module_name, _, cls_name = name.rpartition(sep)
    if not module_name:
        cls_name, module_name = None, package if package else cls_name
    try:
        try:
            module = imp(module_name, package=package, **kwargs)
        except ValueError as exc:
            raise exc
        return getattr(module, cls_name) if cls_name else module
    except (ImportError, AttributeError):
        if default is None:
            raise
    return default
