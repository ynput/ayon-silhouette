"""Host API required Work Files tool"""
import fx


def _get_project() -> "fx.Project":
    return fx.activeProject()


def file_extensions():
    return [".sfx"]


def has_unsaved_changes():
    project = _get_project()
    if not project:
        return False
    return project.is_modified


def save_file(filepath=None):
    project = _get_project()
    if not project:
        return

    # Consider `None` value to be saving into current project path
    args = (filepath,) if filepath else ()
    return project.save(*args)


def open_file(filepath):
    return fx.loadProject(filepath)


def current_file() -> str:
    project = _get_project()
    if not project:
        return
    return project.path
