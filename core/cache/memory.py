_CACHE={}

def set_cache(clave,valor):
    _CACHE[clave]=valor

def get_cache(clave,default=None):
    return _CACHE.get(clave,default)

def clear_cache():
    _CACHE.clear()
