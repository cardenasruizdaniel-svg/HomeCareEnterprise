class InteroperabilityError(Exception):
    pass

class ValidationError(InteroperabilityError):
    pass

class SerializationError(InteroperabilityError):
    pass
