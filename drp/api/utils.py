

def error(code: int, message: str):
    return {"message": message}, code, \
        {"Content-Type": "application/json"}
