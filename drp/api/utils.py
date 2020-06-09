

def error(code: int, message: str = None):
    return {"message": message}, code, \
        {"Content-Type": "application/json"}
