"""A module containing generic loader actions that will display in the Loader.
"""

from ayon_core.pipeline import load

import fx


def _set_frame_range(frame_start: int, frame_end: int, fps: float):

    session = fx.activeSession()
    if not session:
        return

    session.startFrame = frame_start
    session.duration = frame_end - frame_start + 1
    session.frameRate = fps

    # TODO: The above does seem to set the values - however the UI does not
    #  directly update and refresh. Figure out how to force a UI redraw/refresh

    # TODO: Should we influence any of below? E.g. render range is not writable
    # session.renderRange = (frame_start, frame_end)
    # session.workRange = (frame_start, frame_end)
    # session.outputRange = (frame_start, frame_end)


class SetFrameRangeLoader(load.LoaderPlugin):
    """Set frame range excluding pre- and post-handles"""

    product_types = {
        "animation",
        "camera",
        "pointcache",
        "vdbcache",
        "usd",
        "render",
        "plate",
        "mayaScene",
        "review"
    }
    representations = {"*"}

    label = "Set frame range"
    order = 11
    icon = "clock-o"
    color = "white"

    def load(self, context, name=None, namespace=None, options=None):

        version_attributes = context["version"]["attrib"]

        frame_start = version_attributes.get("frameStart")
        frame_end = version_attributes.get("frameEnd")
        if frame_start is None or frame_end is None:
            print(
                "Skipping setting frame range because start or "
                "end frame data is missing.."
            )
            return

        fps = version_attributes["fps"]
        _set_frame_range(frame_start, frame_end, fps)


class SetFrameRangeWithHandlesLoader(load.LoaderPlugin):
    """Set frame range including pre- and post-handles"""

    product_types = {
        "animation",
        "camera",
        "pointcache",
        "vdbcache",
        "usd",
        "render",
        "plate",
        "mayaScene",
        "review"
    }
    representations = {"*"}

    label = "Set frame range (with handles)"
    order = 12
    icon = "clock-o"
    color = "white"

    def load(self, context, name=None, namespace=None, options=None):

        version_attributes = context["version"]["attrib"]

        frame_start = version_attributes.get("frameStart")
        frame_end = version_attributes.get("frameEnd")
        if frame_start is None or frame_end is None:
            print(
                "Skipping setting frame range because start or "
                "end frame data is missing.."
            )
            return

        # Include handles
        frame_start -= version_attributes.get("handleStart", 0)
        frame_end += version_attributes.get("handleEnd", 0)

        fps = version_attributes["fps"]
        _set_frame_range(frame_start, frame_end, fps)
