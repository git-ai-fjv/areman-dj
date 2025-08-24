# lädt alle Module in diesem Ordner, damit Django getrennte Model-Dateien findet
from importlib import import_module
from pathlib import Path
import pkgutil

_pkg = __package__
_pkg_path = Path(__file__).parent

for _, module_name, is_pkg in pkgutil.iter_modules([str(_pkg_path)]):
    if not is_pkg and module_name != "__init__":
        import_module(f"{_pkg}.{module_name}")
