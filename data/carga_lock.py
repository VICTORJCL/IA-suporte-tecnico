import threading
from functools import wraps

CARGA_LOCK = threading.Lock()


def carga_exclusiva(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if CARGA_LOCK.locked():
            print("[Carga] Outra carga em andamento. Aguardando terminar...")
        with CARGA_LOCK:
            print("[Carga] Iniciando carga (trava adquirida).")
            return func(*args, **kwargs)
    return wrapper
