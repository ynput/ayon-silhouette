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
    AYON_INSTANCE_ID,
    get_current_context,
)
from ayon_core.pipeline.load import any_outdated_containers
from ayon_core.lib import emit_event, register_event_callback
from ayon_core.pipeline.context_tools import (
    version_up_current_workfile,
    get_current_task_entity
)
from ayon_core.settings import get_current_project_settings
from .workio import (
    open_file,
    save_file,
    file_extensions,
    has_unsaved_changes,
    current_file
)
from . import lib

import fx
import hook

log = logging.getLogger("ayon_silhouette")

HOST_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGINS_DIR = os.path.join(HOST_DIR, "plugins")
PUBLISH_PATH = os.path.join(PLUGINS_DIR, "publish")
LOAD_PATH = os.path.join(PLUGINS_DIR, "load")
CREATE_PATH = os.path.join(PLUGINS_DIR, "create")
INVENTORY_PATH = os.path.join(PLUGINS_DIR, "inventory")

AYON_CONTAINERS = lib.AYON_CONTAINERS
AYON_CONTEXT_CREATOR_IDENTIFIER = "io.ayon.create.context"


def defer(callable, timeout=0):
    """Defer a callable to the next event loop."""
    QtCore.QTimer.singleShot(timeout, callable)


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
        self._install_hooks()

        register_event_callback("open", on_open)
        register_event_callback("init", on_init)

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

        action = menu.addAction("Set Frame Range")
        action.setToolTip("Set active session frame range")
        action.triggered.connect(_on_set_frame_range)

        action = menu.addAction("Set Resolution")
        action.setToolTip("Set active session resolution")
        action.triggered.connect(_on_set_resolution)

        menu.addSeparator()
        action = menu.addAction("Experimental Tools...")
        action.triggered.connect(
            lambda: host_tools.show_experimental_tools_dialog(parent=parent)
        )

    def _install_hooks(self):
        # Connect events
        hook.add("startupComplete", partial(emit_event, "init"))
        hook.add("pre_save", partial(emit_event, "before.save"))

        # Note that save and load we respond to a 'project' whereas for new
        # we respond to a new 'session'.
        hook.add("post_save", partial(emit_event, "save"))
        hook.add("post_load", partial(emit_event, "open"))
        hook.add("session_created", partial(emit_event, "new"))
        # TODO: Detect a "save into another context" similar to Maya

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


def parse_container(source, project=None):
    """Return the container node's full container data.

    Args:
        source (fx.Source): A Silhouette source.
        project (Optional[fx.Project]): Project related to the source
            item or node so that we can track it back to the project.

    Returns:
        dict[str, Any]: The container schema data for this container node.

    """
    data = lib.read(source)
    if not data:
        return

    # TODO: ensure object is actually a container by `id` value

    # Backwards compatibility pre-schemas for containers
    data["schema"] = data.get("schema", "ayon:container-3.0")
    data["objectName"] = source.label  # required for container data model

    # Append transient data
    data["_item"] = source
    if project is not None:
        data["_project"] = project

    return data


def iter_containers(project=None):
    """Yield all source objects in the active project with AYON property
     AYON container ID"""

    if project is None:
        project = fx.activeProject()

    if not project:
        return

    # List all sources with `AYON` property
    for source in project.sources:
        data = parse_container(source, project=project)
        if data:
            yield data


def iter_instances(session=None):
    """Yield all objects in the active session that have 'id' attribute set
    matching an AYON container ID"""

    if session is None:
        session = fx.activeSession()
    if not session:
        return

    for node in session.nodes:
        data = lib.read(node)
        if data and data.get("id") == AYON_INSTANCE_ID:
            data["_node"] = node
            yield data


def on_open():

    def _process():
        from ayon_core.tools.utils import SimplePopup

        if any_outdated_containers():
            log.warning("Project has outdated content.")

            # Find maya main window
            parent = lib.get_main_window()
            if parent is None:
                log.info("Skipping outdated content pop-up "
                         "because Silhouette window can't be found.")
            else:

                # Show outdated pop-up
                def _on_show_inventory():
                    host_tools.show_scene_inventory(parent=parent)

                dialog = SimplePopup(parent=parent)
                dialog.setWindowTitle(
                    "Silhouette project has outdated content")
                dialog.set_message("There are outdated containers in "
                                  "your Silhouette project.")
                dialog.on_clicked.connect(_on_show_inventory)
                dialog.show()

    # Even though the hook is 'post_load' it seems the project isn't actually
    # active directly, so we defer the actual callback here for now to ensure
    # we act upon the new project? We may need to rely on the
    # `project_selected` hook instead
    defer(_process)


def on_init():
    # The deferred timeout is to ensure if Silhouette was launched with a
    # startup file through AYON that Silhouette runs that first before this
    # gets called. The timeout is arbitrary. It may potentially mean that
    # a slow loading Silhouette project may not have initialized yet.
    # Unfortunately this running on the `startupComplete` hook doesn't seem to
    # mean it runs after the startup project has been loaded.
    # TODO: Investigate whether we can make this more reliable without a needed
    #  defer with timeout
    defer(_generate_default_session, timeout=500)


def _on_set_resolution():
    """Set active session resolution based on current task attributes."""
    session = fx.activeSession()
    if not session:
        return
    task_entity = get_current_task_entity()
    lib.set_resolution_from_entity(session, task_entity)


def _on_set_frame_range():
    """Set active session frame range based on current task attributes."""
    session = fx.activeSession()
    if not session:
        return
    task_entity = get_current_task_entity()
    lib.set_frame_range_from_entity(session, task_entity)


def _generate_default_session():
    """Create a project and session using the current context task attributes.

    This is called on startup to ensure a session is available for the user
    that matches the expected frame range and resolution.

    """
    if fx.activeProject():
        # An existing project is already open, so we do not initialize
        return

    entity = get_current_task_entity()
    attrib = entity["attrib"]
    frame_start = attrib["frameStart"]
    frame_end = attrib["frameEnd"]
    fps = attrib["fps"]
    resolution_width = attrib["resolutionWidth"]
    resolution_height = attrib["resolutionHeight"]
    pixel_aspect = attrib["pixelAspect"]

    with lib.undo_chunk("Creating initial session"):
        project = fx.activeProject()
        if not project:
            project = fx.Project()
            fx.setActiveProject(project)

        session = fx.Session(
            width=resolution_width,
            height=resolution_height,
            pixelAspect=pixel_aspect,
            # TODO: Define a better default name? Or make customizable?
            label="Main"
        )
        session.frameRate = fps
        session.startFrame = frame_start
        session.duration = frame_end - frame_start + 1

        # TODO: Generate session from one of the available templates
        #   so that e.g. default paint or roto nodes are available
        #   using maybe AYON setting profiles
        project.addItem(session)
        fx.setActiveSession(session)
