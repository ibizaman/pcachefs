from pcachefsutil import debug

def create(t, *args, **kwargs):
    debug('create', str(t), str(args), str(kwargs))
    return t(*args, **kwargs)

