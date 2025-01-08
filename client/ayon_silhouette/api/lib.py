"""Library functions for Silhouette."""
import contextlib

from ayon_core.lib import NumberDef

import fx
import tools.window

AYON_CONTAINERS = "AYON_CONTAINERS"
JSON_PREFIX = "JSON::"


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


def imprint(node, data, group=None):
    """Write `data` to `node` as userDefined attributes

    Arguments:
        node (c4d.BaseObject): The selection object
        data (dict): Dictionary of key/value pairs
    """
    raise NotImplementedError("Not implemented yet")


def read(node) -> dict:
    """Return user-defined attributes from `node`"""

    raise NotImplementedError("Not implemented yet")


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