import os
import logging
import contextlib
from functools import partial

import pyblish.api
from qtpy import QtCore

from ayon_core.host import HostBase, IWorkfileHost, ILoadHost, IPublishHost
from ayon_core.tools.utils import host_tools
from ayon_core.pipeline import (
    register_loader_plugin_path,
    register_creator_plugin_path,
    # AYON_CONTAINER_ID,
    get_current_context,
)
from ayon_core.pipeline.context_tools import version_up_current_workfile
from ayon_core.settings import get_current_project_settings
from .workio import (
    open_file,
    save_file,
    file_extensions,
    has_unsaved_changes,
    current_file
)
from . import lib

log = logging.getLogger("ayon_silhouette")

HOST_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGINS_DIR = os.path.join(HOST_DIR, "plugins")
PUBLISH_PATH = os.path.join(PLUGINS_DIR, "publish")
LOAD_PATH = os.path.join(PLUGINS_DIR, "load")
CREATE_PATH = os.path.join(PLUGINS_DIR, "create")
INVENTORY_PATH = os.path.join(PLUGINS_DIR, "inventory")

AYON_CONTAINERS = lib.AYON_CONTAINERS
AYON_CONTEXT_CREATOR_IDENTIFIER = "io.ayon.create.context"


def defer(callable):
    """Defer a callable to the next event loop."""
    QtCore.QTimer.singleShot(0, callable)


class SilhouetteHost(HostBase, IWorkfileHost, ILoadHost, IPublishHost):
    name = "silhouette"

    def __init__(self):
        super(SilhouetteHost, self).__init__()

    def install(self):
        # process path mapping
        # dirmap_processor = SilhouetteDirmap("silhouette", project_settings)
        # dirmap_processor.process_dirmap()

        pyblish.api.register_plugin_path(PUBLISH_PATH)
        pyblish.api.register_host("silhouette")

        register_loader_plugin_path(LOAD_PATH)
        register_creator_plugin_path(CREATE_PATH)
        # TODO: Register only when any inventory actions are created
        # register_inventory_action_path(INVENTORY_PATH)

        defer(self._install_menu)

    def _install_menu(self):
        project_settings = get_current_project_settings()
        parent = lib.get_main_window()

        menu_label = os.environ.get("AYON_MENU_LABEL") or "AYON"
        menu = parent.menuBar().addMenu(menu_label)

        # Add current context label
        def _set_current_context_label(action):
            context = get_current_context()
            label = "{0[folder_path]}, {0[task_name]}".format(context)
            action.setText(label)

        action = menu.addAction("Current Context")
        action.setEnabled(False)

        # Update context label on menu show
        menu.aboutToShow.connect(partial(_set_current_context_label, action))

        menu.addSeparator()

        # Add Version Up Workfile menu entry
        try:
            if project_settings["core"]["tools"]["ayon_menu"].get(
                "version_up_current_workfile"):
                    action = menu.addAction("Version Up Workfile")
                    action.triggered.connect(version_up_current_workfile)
                    menu.addSeparator()
        except KeyError:
            print("Version Up Workfile setting not found in "
                  "Core Settings. Please update Core Addon")

        action = menu.addAction("Create...")
        action.triggered.connect(
            lambda: host_tools.show_publisher(parent=parent,
                                              tab="create")
        )

        action = menu.addAction("Load...")
        action.triggered.connect(
            lambda: host_tools.show_loader(parent=parent, use_context=True)
        )

        action = menu.addAction("Publish...")
        action.triggered.connect(
            lambda: host_tools.show_publisher(parent=parent,
                                              tab="publish")
        )

        action = menu.addAction("Manage...")
        action.triggered.connect(
            lambda: host_tools.show_scene_inventory(parent=parent)
        )

        action = menu.addAction("Library...")
        action.triggered.connect(
            lambda: host_tools.show_library_loader(parent=parent)
        )

        menu.addSeparator()
        action = menu.addAction("Work Files...")
        action.triggered.connect(
            lambda: host_tools.show_workfiles(parent=parent)
        )

    def open_workfile(self, filepath):
        return open_file(filepath)

    def save_workfile(self, filepath=None):
        return save_file(filepath)

    def get_current_workfile(self):
        return current_file()

    def workfile_has_unsaved_changes(self):
        return has_unsaved_changes()

    def get_workfile_extensions(self):
        return file_extensions()

    def get_containers(self):
        return iter_containers()

    @contextlib.contextmanager
    def maintained_selection(self):
        with lib.maintained_selection():
            yield

    def update_context_data(self, data, changes):
        if not data:
            return

        # TODO: Implement this

    def get_context_data(self):
        return {}


def parse_container(container):
    """Return the container node's full container data.

    Args:
        container (str): A container node name.

    Returns:
        dict[str, Any]: The container schema data for this container node.

    """
    data = lib.read(container)

    # Backwards compatibility pre-schemas for containers
    data["schema"] = data.get("schema", "ayon:container-3.0")

    # Append transient data
    data["objectName"] = container.GetName()
    data["node"] = container

    return data


def iter_containers(doc=None):
    """Yield all objects in the active document that have 'id' attribute set
    matching an AYON container ID"""
    if False:
        yield
    return
