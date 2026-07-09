from .resources import FHIR_RESOURCES

def paciente_a_json(p:dict)->dict:
    return {"resourceType":FHIR_RESOURCES["paciente"],"identifier":[{"value":p.get("documento","")}],"name":[{"text":p.get("nombre","")}]}