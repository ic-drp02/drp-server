

def error(code: int, message: str = None, type: str = None):
    return {"type": type, "message": message}, code, \
        {"Content-Type": "application/json"}
