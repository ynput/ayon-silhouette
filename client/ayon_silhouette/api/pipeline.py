import os
import logging
import contextlib
from pathlib import Path
from functools import partial

import pyblish.api
from qtpy import QtCore

from ayon_core.host import HostBase, IWorkfileHost, ILoadHost, IPublishHost
from ayon_core.tools.utils import host_tools
from ayon_core.pipeline import (
    register_loader_plugin_path,
    register_creator_plugin_path,
    register_workfile_build_plugin_path,
    # AYON_CONTAINER_ID,
    AYON_INSTANCE_ID,
    get_current_context,
    registered_host
)
from ayon_core.pipeline.load import any_outdated_containers
from ayon_core.lib import emit_event, register_event_callback
from ayon_core.pipeline.context_tools import get_current_task_entity
from ayon_core.settings import get_current_project_settings
from ayon_core.tools.workfile_template_build import open_template_ui
from . import lib
from .workfile_template_builder import (
    SilhouetteTemplateBuilder,
    create_placeholder,
    update_placeholder,
    build_workfile_template,
)

# Function 'save_next_version' was introduced in ayon-core 1.5.0
try:
    from ayon_core.pipeline.workfile import save_next_version
except ImportError:
    from ayon_core.pipeline.context_tools import (
        version_up_current_workfile as save_next_version
    )

import fx
import hook

log = logging.getLogger("ayon_silhouette")

HOST_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGINS_DIR = os.path.join(HOST_DIR, "plugins")
PUBLISH_PATH = os.path.join(PLUGINS_DIR, "publish")
LOAD_PATH = os.path.join(PLUGINS_DIR, "load")
CREATE_PATH = os.path.join(PLUGINS_DIR, "create")
INVENTORY_PATH = os.path.join(PLUGINS_DIR, "inventory")
WORKFILE_BUILD_PATH = os.path.join(PLUGINS_DIR, "workfile_build")

AYON_CONTAINERS = lib.AYON_CONTAINERS
AYON_CONTEXT_CREATOR_IDENTIFIER = "io.ayon.create.context"


def defer(callable, timeout=0):
    """Defer a callable to the next event loop."""
    QtCore.QTimer.singleShot(timeout, callable)


def _get_project() -> "fx.Project":
    return fx.activeProject()


class SilhouetteHost(HostBase, IWorkfileHost, ILoadHost, IPublishHost):
    name = "silhouette"

    context_data_key = "AYON_context"

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
        register_workfile_build_plugin_path(WORKFILE_BUILD_PATH)

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
                    action.triggered.connect(save_next_version)
        except KeyError:
            print("Version Up Workfile setting not found in "
                  "Core Settings. Please update Core Addon")

        action = menu.addAction("Work Files...")
        action.triggered.connect(
            lambda: host_tools.show_workfiles(parent=parent)
        )
        menu.addSeparator()

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

        action = menu.addAction("Set Frame Range")
        action.setToolTip("Set active session frame range")
        action.triggered.connect(_on_set_frame_range)

        action = menu.addAction("Set Resolution")
        action.setToolTip("Set active session resolution")
        action.triggered.connect(_on_set_resolution)

        menu.addSeparator()

        # region Workfile templates
        menu_template = menu.addMenu("Template Builder")

        action = menu_template.addAction("Build Workfile from template")
        action.triggered.connect(lambda: build_workfile_template())

        menu_template.addSeparator()

        action = menu_template.addAction("Open template")

        def _open_template_ui():
            open_template_ui(
                SilhouetteTemplateBuilder(
                    registered_host()),
                    lib.get_main_window()
            )

        action.triggered.connect(_open_template_ui)

        action = menu_template.addAction("Create Place Holder")
        action.triggered.connect(create_placeholder)

        action = menu_template.addAction("Update Place Holder")
        action.triggered.connect(update_placeholder)
        # endregion

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
        # Support .zip (zipped project workfiles)
        zipped_filepath = None
        if filepath.endswith(".zip"):
            # Unzip the file
            zipped_filepath = filepath
            unzipped_filepath = filepath[:-4] + ".sfx"
            lib.unzip(filepath, unzipped_filepath)
            filepath = unzipped_filepath

        fx.loadProject(filepath)

        # Check for successful project open.
        # Note: `fx.loadProject` does return the loaded project - however it
        # also returns one if the file actually failed to load
        project = fx.activeProject()
        if not project or not project.path:
            self.log.error("Failed to open project at: %s", filepath)
            return

        # If we opened a .zip and the project loaded succesfully, then remove
        # the file if it is in AYON_WORKDIR (because those .zip should only
        # live there temporarily on "Copy & Open" from published workfiles
        # in the workfiles tool)
        def is_in_workdir():
            return (
                Path(os.environ["AYON_WORKDIR"]) ==
                Path(zipped_filepath).parent
            )
        if zipped_filepath and is_in_workdir():
            os.remove(zipped_filepath)

    def save_workfile(self, filepath=None):
        project = _get_project()
        if not project:
            return

        # Silhouette host integration has `.zip` as supported extension
        # solely so that it can open the published zipped project workfiles.
        if filepath and filepath.endswith(".zip"):
            self.log.warning(
                "Silhouette does not support saving as .zip. "
                "Only opening the published .zip project workfiles. "
                "Saving as .sfx instead.")
            filepath = filepath[:-4]  # Remove .zip extension
            filepath += ".sfx"        # Add .sfx extension

        # Consider `None` value to be saving into current project path
        args = (filepath,) if filepath else ()
        project.save(*args)

    def get_current_workfile(self):
        project = _get_project()
        if not project:
            return

        # Silhouette workfiles are projects that are actually a folder
        # of files, instead of a single file. Inside the folder, is a
        # `project.sfx` file that is the main project file. We want to return
        # the folder's project bundle path instead of the `project.sfx` file.
        project_path = project.path
        if project_path:
            return os.path.dirname(project_path)

    def workfile_has_unsaved_changes(self):
        project = _get_project()
        if not project:
            return False
        return project.is_modified

    def get_workfile_extensions(self):
        return [
            ".sfx",
            # Silhouette doesn't natively support .zip but since the .sfx
            # projects are folders, we use zipped
            ".zip"
        ]

    def get_containers(self):
        return iter_containers()

    @contextlib.contextmanager
    def maintained_selection(self):
        with lib.maintained_selection():
            yield

    def update_context_data(self, data, changes):
        if not data:
            return

        project = _get_project()
        if not project:
            self.log.warning(
                "Unable to save context data because"
                " there is no active project.")
            return

        lib.imprint(project, data, key=self.context_data_key)

    def get_context_data(self):
        project = _get_project()
        if not project:
            return {}
        return lib.read(project, key=self.context_data_key) or {}


def parse_container(source, project=None, session=None):
    """Return the container node's full container data.

    Args:
        source (fx.Source | fx.Node): A Silhouette source or node.
        project (Optional[fx.Project]): Project related to the source
            item or node so that we can track it back to the project.
        session (Optional[fx.Session]): Session related to the source
            item or node so that we can track it back to the session.

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
    if session is not None:
        data["_session"] = session

    return data


def iter_containers(project=None, session=None):
    """Yield all source objects in the active project with AYON property
     AYON container ID"""

    if project is None:
        project = fx.activeProject()

    if not project:
        return

    # List all sources in project with `AYON` property
    for source in project.sources:
        data = parse_container(source, project=project)
        if data:
            yield data

    if session is None:
        session = fx.activeSession()

    if not session:
        return

    # List all nodes in session with `AYON` property
    for node in session.nodes:
        data = parse_container(node, project=project, session=session)
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

        if not any_outdated_containers():
            return

        log.warning("Project has outdated content.")

        # Find maya main window
        parent = lib.get_main_window()
        if parent is None:
            log.info(
                "Skipping outdated content pop-up"
                " because Silhouette window can't be found.")
            return

        # Show outdated pop-up
        def _on_show_inventory():
            host_tools.show_scene_inventory(parent=parent)

        dialog = SimplePopup(parent=parent)
        dialog.setWindowTitle(
            "Silhouette project has outdated content")
        dialog.set_message(
            "There are outdated containers in"
            " your Silhouette project.")
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
    #  See: https://forum.borisfx.com/t/19547
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
    project = fx.activeProject()
    if project and project.sessions:
        # An existing project is already open, so we do not initialize
        print("Skipping default session creation, "
              "project with sessions already active.")
        return

    with lib.undo_chunk("Creating initial session"):
        if not project:
            project = fx.Project()
            fx.setActiveProject(project)

        session = fx.Session(
            # TODO: Define a better default name? Or make customizable?
            label="Main"
        )
        lib.reset_session_settings(session)

        # TODO: Generate session from one of the available templates
        #   so that e.g. default paint or roto nodes are available
        #   using maybe AYON setting profiles
        #   All templates are available in `fx.templates`
        project.addItem(session)
        fx.setActiveSession(session)
