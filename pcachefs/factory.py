from pcachefsutil import debug

def create(t, *args):
    debug('create', str(t), str(args))
    return t(args)

