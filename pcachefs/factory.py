
def create(t, *args):
    print 'create', str(t), str(args)
    return t(args)

