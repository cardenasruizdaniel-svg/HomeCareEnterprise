SESSION_TIMEOUT_MINUTES=30

def session_expired(last_activity_minutes:int)->bool:
    return last_activity_minutes>SESSION_TIMEOUT_MINUTES
