import os
import logging
import contextlib

import pyblish.api

from ayon_core.host import HostBase, IWorkfileHost, ILoadHost, IPublishHost
from ayon_core.pipeline import (
    register_loader_plugin_path,
    register_creator_plugin_path,
    AYON_CONTAINER_ID,
)
from .workio import (
    open_file,
    save_file,
    file_extensions,
    has_unsaved_changes,
    current_file
)
import ayon_silhouette

from . import lib

log = logging.getLogger("ayon_silhouette")

HOST_DIR = os.path.dirname(os.path.abspath(ayon_silhouette.__file__))
PLUGINS_DIR = os.path.join(HOST_DIR, "plugins")
PUBLISH_PATH = os.path.join(PLUGINS_DIR, "publish")
LOAD_PATH = os.path.join(PLUGINS_DIR, "load")
CREATE_PATH = os.path.join(PLUGINS_DIR, "create")
INVENTORY_PATH = os.path.join(PLUGINS_DIR, "inventory")

AYON_CONTAINERS = lib.AYON_CONTAINERS
AYON_CONTEXT_CREATOR_IDENTIFIER = "io.ayon.create.context"


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
        self.log.info(PUBLISH_PATH)

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