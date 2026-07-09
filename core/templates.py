from fastapi.templating import Jinja2Templates

from core.permissions import tiene_permiso

templates = Jinja2Templates(directory="templates")

templates.env.globals["tiene_permiso"] = tiene_permiso