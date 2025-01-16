"""Library functions for Silhouette."""
import contextlib
import json
import logging
from typing import Optional

from ayon_core.lib import NumberDef
from ayon_core.pipeline.context_tools import get_current_task_entity

import fx
import tools.window

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
def maintained_selection():
    """Maintain selection during context."""

    previous_selection = fx.selection()
    try:
        yield
    finally:
        fx.select(previous_selection)
        pass


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

    # Remove data
    if data is None:
        if isinstance(node, fx.Node):
            node.setState(key, None)
        else:
            node.removeProperty(key)
        return

    # Set data
    if isinstance(node, fx.Node):
        node.setState(key, data)
    elif isinstance(node, fx.Object):
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
    else:
        raise TypeError(f"Unsupported node type: {node} ({type(node)})")


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
        return node.getState(key)
    elif isinstance(node, fx.Object):
        # Project or source items do not have state
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
    else:
        raise TypeError(f"Unsupported node type: {node} ({type(node)})")


def set_new_node_position(node):
    """Position the node near the active node, or the top-right of the scene"""
    n = fx.activeNode()
    if n:
        pos = fx.trees.nextPos(n)
    else:
        bounds = fx.trees.bounds
        size = fx.trees.nodeSize(node)
        pos = fx.Point(bounds.right - size.x / 2,
                    bounds.top + size.y / 2)
    node.setState("graph.pos", pos)


def set_resolution_from_entity(session, task_entity):
    """Set resolution and pixel aspect from task entity attributes.

    Args:
        session (fx.Session): The Silhouette session.
        task_entity (dict): Task entity.

    """
    resolution_width = task_entity["attrib"]["resolutionWidth"]
    resolution_height = task_entity["attrib"]["resolutionHeight"]
    pixel_aspect = task_entity["attrib"]["pixelAspect"]

    fx.beginUndo("Set session resolution")
    session.width = resolution_width
    session.height = resolution_height
    session.pixelAspect = pixel_aspect
    fx.endUndo()


def set_frame_range_from_entity(session, task_entity):
    """Set frame range and FPS from task entity attributes.

    Args:
        session (fx.Session): The Silhouette session.
        task_entity (dict): Task entity.

    """
    frame_start = task_entity["attrib"]["frameStart"]
    frame_end = task_entity["attrib"]["frameEnd"]
    fps = task_entity["attrib"]["fps"]

    fx.beginUndo("Set session frame range")
    session.frameRate = fps
    session.startFrame = frame_start
    session.duration = frame_end - frame_start + 1
    fx.endUndo()


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