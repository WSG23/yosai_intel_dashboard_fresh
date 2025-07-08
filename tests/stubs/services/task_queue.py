def create_task(coro):
    if hasattr(coro, 'close'):
        coro.close()
    return 'tid'

def get_status(tid):
    return {'progress': 0}

def clear_task(tid):
    pass
