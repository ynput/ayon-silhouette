"""Library functions for Silhouette."""
import contextlib
import json
import logging
import os
import platform
import zipfile
from typing import Optional, Iterator, List, Tuple, Dict

from qtpy import QtCore, QtWidgets
import fx
import tools.window

from ayon_core.lib import NumberDef
from ayon_core.pipeline.context_tools import get_current_task_entity


AYON_CONTAINERS = "AYON_CONTAINERS"
JSON_PREFIX = "JSON::"

log = logging.getLogger(__name__)


def get_main_window():
    """Get the main Qt window of the application."""
    return tools.window.get_main_window()


def collect_animation_defs(create_context, fps=False):
    """Get the basic animation attribute definitions for the publisher.

    Arguments:
        create_context (CreateContext): The context of publisher will be
            used to define the defaults for the attributes to use the current
            context's entity frame range as default values.
        step (bool): Whether to include `step` attribute definition.
        fps (bool): Whether to include `fps` attribute definition.

    Returns:
        List[NumberDef]: List of number attribute definitions.

    """

    # use task entity attributes to set defaults based on current context
    task_entity = create_context.get_current_task_entity()
    attrib: dict = task_entity["attrib"]
    frame_start: int = attrib["frameStart"]
    frame_end: int = attrib["frameEnd"]
    handle_start: int = attrib["handleStart"]
    handle_end: int = attrib["handleEnd"]

    # build attributes
    defs = [
        NumberDef("frameStart",
                  label="Frame Start",
                  default=frame_start,
                  decimals=0),
        NumberDef("frameEnd",
                  label="Frame End",
                  default=frame_end,
                  decimals=0),
        NumberDef("handleStart",
                  label="Handle Start",
                  tooltip="Frames added before frame start to use as handles.",
                  default=handle_start,
                  decimals=0),
        NumberDef("handleEnd",
                  label="Handle End",
                  tooltip="Frames added after frame end to use as handles.",
                  default=handle_end,
                  decimals=0),
    ]

    # if fps:
    #     doc = active_document()
    #     current_fps = doc.GetFps()
    #     fps_def = NumberDef(
    #         "fps", label="FPS", default=current_fps, decimals=5
    #     )
    #     defs.append(fps_def)

    return defs


@contextlib.contextmanager
def maintained_selection(preserve_active_node=True):
    """Maintain selection during context."""

    previous_active_node = fx.activeNode()
    previous_selection = fx.selection()
    try:
        yield
    finally:
        fx.select(previous_selection)
        if preserve_active_node and previous_active_node:
            fx.activate(previous_active_node)


@contextlib.contextmanager
def undo_chunk(label=""):
    """Open undo chunk during context.

    In Silhouette, it's often necessary to group operations into an undo chunk
    to ensure the UI updates correctly on property and value changes.

    Note that `contextlib.contextmanager` can also be used as function
    decorators.

    """
    try:
        fx.beginUndo(label)
        yield
    finally:
        fx.endUndo()


def imprint(node, data: Optional[dict], key="AYON"):
    """Write `data` to `node` as userDefined attributes

    Arguments:
        node (fx.Object | fx.Node): The selection object
        data (dict): Dictionary of key/value pairs
    """
    if isinstance(node, fx.Node):
        return imprint_state(node, data, key)
    elif isinstance(node, fx.Object):
        return imprint_property(node, data, key)
    else:
        raise TypeError(f"Unsupported node type: {node} ({type(node)})")


def imprint_state(node, data, key):
    node.setState(key, data)


def imprint_property(node, data, key):
    if data is None:
        prop = node.property(key)
        if prop:
            node.removeProperty(prop)
        return

    # Serialize data
    value = json.dumps(data)
    prop = node.property(key)
    if not prop:
        # Create property
        # Arguments are `id`, `label` and `default_value`. By passing the
        # default value as empty string we make it a string attribute.
        prop = fx.Property(key, key, "")
        prop.hidden = True
        node.addProperty(prop)

    # Set value
    prop.value = value


def read(node, key="AYON") -> Optional[dict]:
    """Return user-defined attributes from `node`

    Arguments:
        node (fx.Object | fx.Node): Node or object to redad from.
        key (str): The key to read from.

    Returns:
        Optional[dict]: The data stored in the node.

    """
    if isinstance(node, fx.Node):
        # Use node state instead of property
        return read_state(node, key)
    elif isinstance(node, fx.Object):
        # Project or source items do not have state
        return read_property(node, key)
    else:
        raise TypeError(f"Unsupported node type: {node} ({type(node)})")


def read_state(node, key):
    return node.getState(key)


def read_property(node, key):
    prop = node.property(key)
    if not prop:
        return
    value = prop.value
    if not value:
        return

    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        log.error(
            f"Failed to read '{key}' from node {node}"
            f" with value {value}: {exc}")
        return


def set_new_node_position(node):
    """Position the node near the active node, or the top-right of the scene"""
    n = fx.activeNode()
    if n:
        pos = fx.trees.nextPos(n)
    else:
        bounds = fx.trees.bounds
        size = fx.trees.nodeSize(node)
        pos = fx.Point(
            bounds.right - size.x / 2,
            bounds.top + size.y / 2
        )
    node.setState("graph.pos", pos)


def set_resolution_from_entity(session, task_entity):
    """Set resolution and pixel aspect from task entity attributes.

    Args:
        session (fx.Session): The Silhouette session.
        task_entity (dict): Task entity.

    """
    task_attrib = task_entity["attrib"]
    with undo_chunk("Set session resolution"):
        session.width = task_attrib["resolutionWidth"]
        session.height = task_attrib["resolutionHeight"]
        session.pixelAspect = task_attrib["pixelAspect"]


def set_frame_range_from_entity(session, task_entity):
    """Set frame range and FPS from task entity attributes.

    Args:
        session (fx.Session): The Silhouette session.
        task_entity (dict): Task entity.

    """
    frame_start = task_entity["attrib"]["frameStart"]
    frame_end = task_entity["attrib"]["frameEnd"]
    fps = task_entity["attrib"]["fps"]

    with undo_chunk("Set session frame range"):
        session.frameRate = fps
        session.startFrame = frame_start
        session.duration = (frame_end - frame_start) + 1


def reset_session_settings(session=None, task_entity=None):
    """Reset the session settings to the task context defaults."""
    if session is None:
        session = fx.activeSession()
        assert session

    if task_entity is None:
        task_entity = get_current_task_entity()

    with undo_chunk("Reset session settings"):
        set_resolution_from_entity(session, task_entity)
        set_frame_range_from_entity(session, task_entity)


@contextlib.contextmanager
def capture_messageboxes(callback):
    """Capture messageboxes and call a callback with them.

    This is a workaround for Silhouette not allowing the Python code to
    suppress messageboxes and supply default answers to them. So instead we
    capture the messageboxes and respond to them through a rapid QTimer.
    """
    processed = set()
    timer = QtCore.QTimer()

    def on_timeout():
        # Check for dialogs
        widgets = QtWidgets.QApplication.instance().topLevelWidgets()
        has_boxes = False
        for widget in widgets:
            if isinstance(widget, QtWidgets.QMessageBox):
                has_boxes = True
                if widget in processed:
                    continue
                processed.add(widget)
                callback(widget)

        # Stop as soon as possible with our detections. Even with the
        # QTimer repeating at interval of 0 we should have been able to
        # capture all the UI events as they happen in the main thread for
        # each dialog.
        # Note: Technically this would mean that as soon as there is no
        # active messagebox we directly stop the timer, and hence would stop
        # finding messageboxes after. However, with the export methods in
        # Silhouette this has not been a problem and all boxes were detected
        # accordingly.
        if not has_boxes:
            timer.stop()

    timer.setSingleShot(False)  # Allow to capture multiple boxes
    timer.timeout.connect(on_timeout)
    timer.start()
    try:
        yield
    finally:
        timer.stop()


def iter_children(
        node: fx.Node,
        prefix: Optional[str] = None
) -> Iterator[Tuple[fx.Node, str]]:
    """Iterate over all children of a node recursively.

    This yields the node together with a label that indicates the full path
    from the root node passed to the function.
    """
    children = node.children
    if not children:
        return
    for child in reversed(children):
        # Yield with a nested label so we can easily display it nicely
        label = child.label
        if prefix:
            label = f"{prefix} > {label}"
        yield child, label
        yield from iter_children(child, prefix=label)


class _ZipFile(zipfile.ZipFile):
    """Extended check for windows invalid characters."""

    # this is extending default zipfile table for few invalid characters
    # that can come from Mac
    _windows_illegal_characters = ":<>|\"?*\r\n\x00"
    _windows_illegal_name_trans_table = str.maketrans(
        _windows_illegal_characters,
        "_" * len(_windows_illegal_characters)
    )
    _is_windows = platform.system().lower() == "windows"

    def _extract_member(self, member, tpath, pwd):
        """Allows longer paths in zip files.

        Regular DOS paths are limited to MAX_PATH (260) characters, including
        the string's terminating NUL character.
        That limit can be exceeded by using an extended-length path that
        starts with the '\\?\' prefix.
        """
        if self._is_windows:
            tpath = os.path.abspath(tpath)
            if tpath.startswith("\\\\"):
                tpath = "\\\\?\\UNC\\" + tpath[2:]
            else:
                tpath = "\\\\?\\" + tpath

        return super()._extract_member(member, tpath, pwd)


def zip_folder(source, destination):
    """Zip a directory and move to `destination`.

    This zips the contents of the source directory into the zip file. The
    source directory itself is not included in the zip file.

    Args:
        source (str): Directory to zip and move to destination.
        destination (str): Destination file path to zip file.

    """
    def _iter_zip_files_mapping(start):
        for root, dirs, files in os.walk(start):
            for folder in dirs:
                path = os.path.join(root, folder)
                yield path, os.path.relpath(path, start)
            for file in files:
                path = os.path.join(root, file)
                yield path, os.path.relpath(path, start)

    if not os.path.isdir(source):
        raise ValueError(f"Source is not a directory: {source}")

    if os.path.exists(destination):
        os.remove(destination)

    with _ZipFile(
        destination, "w", zipfile.ZIP_DEFLATED
    ) as zr:
        for path, relpath in _iter_zip_files_mapping(source):
            zr.write(path, relpath)


def unzip(source, destination):
    """Unzip a zip file to destination.

    Args:
        source (str): Zip file to extract.
        destination (str): Destination directory to extract to.

    """
    with _ZipFile(source) as zr:
        zr.extractall(destination)
    log.debug(f"Extracted '{source}' to '{destination}'")


def get_connections(
    node: fx.Node,
    inputs=True,
    outputs=True) -> Dict[fx.Port, fx.Port]:
    """Return connections from destination ports to their source ports."""
    connections: Dict[fx.Port, fx.Port] = {}
    if inputs:
        for input_destination in node.connectedInputs:
            connections[input_destination] = input_destination.source
    if outputs:
        for output_source in node.connectedOutputs:
            for target_destination in output_source.targets:
                connections[target_destination] = output_source
    return connections


def get_input_port_by_name(node: fx.Node, port_name: str) -> Optional[fx.Port]:
    """Return the input port with the given name."""
    return next(
        (port for port in node.inputs if port.name == port_name),
        None
    )


def get_output_port_by_name(
        node: fx.Node, port_name: str) -> Optional[fx.Port]:
    """Return the output port with the given name."""
    return next(
        (port for port in node.outputs if port.name == port_name),
        None
    )


@undo_chunk("Transfer connections")
def transfer_connections(
    source: fx.Node,
    destination: fx.Node,
    inputs: bool = True,
    outputs: bool = True):
    """Transfer connections from one node to another."""
    # TODO: Match port by something else than name? (e.g. idx?)
    # Transfer connections from inputs
    if inputs:
        for _input in source.connectedInputs:
            name = _input.name
            destination_input = get_input_port_by_name(destination, name)
            if destination_input:
                destination_input.disconnect()
                _input.source.connect(destination_input)

    # Transfer connections from outputs
    if outputs:
        for output in source.connectedOutputs:
            name = output.name
            destination_output = get_output_port_by_name(destination, name)
            if destination_output:
                for target in output.targets:
                    target.disconnect()
                    destination_output.connect(target)


def copy_session_nodes(
        source_session: fx.Session,
        destination_session: fx.Session) -> List[fx.Node]:
    """Merge all nodes from source session into destination session.

    Arguments:
        source_session (fx.Session): The source session to clone nodes from.
        destination_session (fx.Session): The destination session to merge
            into.

    Returns:
        List[fx.Node]: The cloned nodes in the destination session.
    """
    connections = {}
    for node in source_session.nodes:
        # We skip outputs because we are iterating all nodes
        # so we could automatically also collect the outputs if we
        # collect all their inputs
        connections.update(get_connections(node, outputs=False))

    # Create clones of the nodes from the source session
    source_node_to_clone_node: Dict[fx.Node, fx.Node] = {
        node: node.clone() for node in source_session.nodes
    }

    # Add all clones to the destination session
    for node in source_node_to_clone_node.values():
        destination_session.addNode(node)

    # Re-apply all their connections
    for destination, source in connections.items():
        source_node = source_node_to_clone_node[source.node]
        destination_node = source_node_to_clone_node[destination.node]
        source_port = get_output_port_by_name(source_node,
                                              source.name)
        destination_port = get_input_port_by_name(destination_node,
                                                  destination.name)
        source_port.connect(destination_port)

    return list(source_node_to_clone_node.values())


@undo_chunk("Import project")
def import_project(
    path,
    merge_sessions=True):
    """Import Silhouette project into current project.

    Silhouette can't 'import' projects natively, so instead we will use our
    own logic to load the content from a project file into the currently
    active project.

    Arguments:
        path (str): The project path to import. Since Silhouette projects
            are folders this should be the path to the project folder.
        merge_sessions (bool): When enabled, sessions with the same label
            will be 'merged' by adding all nodes of the imported session to
            the existing session.

    """
    original_project = fx.activeProject()
    if not original_project:
        # Open a project
        original_project = fx.Project()
        fx.setActiveProject(original_project)

    merge_project = fx.loadProject(path)

    # Revert to original project
    fx.setActiveProject(original_project)

    # Add sources from the other project
    for source in merge_project.sources:
        original_project.addItem(source)

    # Merge sessions by label if there's a matching one
    sessions_by_label = {
        session.label: session for session in original_project.sessions
    }
    for merge_session in merge_project.sessions:
        if merge_sessions and merge_session.label in sessions_by_label:
            original_session = sessions_by_label[merge_session.label]
            copy_session_nodes(merge_session, original_session)
        else:
            # Add the session
            original_project.addItem(merge_session.clone())

            # For niceness - set it as active session if current project has
            # no active session
            if not fx.activeSession():
                fx.setActiveSession(merge_session)
