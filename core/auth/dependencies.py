def require_login(session:dict)->bool:
    return bool(session.get("usuario"))
