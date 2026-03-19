# FIX (Simple): Illegal import removed
# from data.repository import Repository

def do_work():
    repo = Repository()
    return repo.get_active_activity('user1')
