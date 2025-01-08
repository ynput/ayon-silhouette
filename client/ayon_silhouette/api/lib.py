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

    if fps:
        doc = active_document()
        current_fps = doc.GetFps()
        fps_def = NumberDef(
            "fps", label="FPS", default=current_fps, decimals=5
        )
        defs.append(fps_def)

    return defs


@contextlib.contextmanager
def maintained_selection():
    """Maintain selection during context."""

    # previous_selection = doc.GetSelection()
    try:
        yield
    finally:
        # set_selection(doc, previous_selection)
        pass

@contextlib.contextmanager
def undo_chunk():
    """Open a undo chunk during context."""
    try:
        fx.startUndo()
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