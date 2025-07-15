from __future__ import annotations
import os
from typing import Any, Optional

import fx
import clique

from ayon_silhouette.api import plugin, lib

from ayon_core.pipeline import Anatomy
from ayon_core.lib import BoolDef
from ayon_core.lib.transcoding import (
    VIDEO_EXTENSIONS, IMAGE_EXTENSIONS, get_oiio_info_for_input
)

# Extensions for subimages that can be loaded with multiple parts
SUBIMAGE_EXTENSIONS: set[str] = {".exr", ".sxr"}


class SourceLoader(plugin.SilhouetteLoader):
    """Load media source."""

    color = "orange"
    product_types = {"*"}
    icon = "code-fork"
    label = "Load Source"
    order = -10
    representations = {"*"}
    extensions = {
        ext.lstrip(".") for ext in VIDEO_EXTENSIONS.union(IMAGE_EXTENSIONS)
    }

    set_session_frame_range_on_load = False

    @classmethod
    def get_options(cls, contexts):
        return [
            BoolDef(
                "load_all_parts",
                label="Load All Parts",
                default=True,
                tooltip=(
                    "Load all subimages/parts of the media instead of only "
                    "the first subimage. This can be useful for e.g. "
                    "Stereo EXR files."
                ),
            ),
            BoolDef(
                "set_session_frame_range_on_load",
                label="Set Session Frame Range on Load",
                default=cls.set_session_frame_range_on_load
            ),
        ]

    @lib.undo_chunk("Load Source")
    def load(self, context, name=None, namespace=None, options=None):
        project = fx.activeProject()
        if not project:
            raise RuntimeError("No active project found.")

        filepath = self.filepath_from_context(context)

        if options.get(
            "set_session_frame_range_on_load",
            self.set_session_frame_range_on_load
        ):
            self._set_session_frame_range(context)

        # A source file may contain multiple parts, such as a left view
        # and a right view in a single EXR.
        options = options or {}
        load_all_parts = options.get("load_all_parts", True)

        # If the file is not an EXR or SXR, we can only load one part so force
        # disable loading multiple parts.
        if (
            load_all_parts
            and os.path.splitext(filepath)[-1].lower()
            not in SUBIMAGE_EXTENSIONS
        ):
            load_all_parts = False

        # If loading all parts, find the info for the subimages so we can label
        # them correctly.
        info: list[dict[str, Any]] = []
        parts = 1
        if load_all_parts:
            raw_filepath = super().filepath_from_context(context)
            info = get_oiio_info_for_input(raw_filepath, subimages=True)
            parts = len(info)

        for part in range(parts):
            source = fx.Source(filepath, part=part)
            part_name = None
            if parts > 1:
                # Use subimage name as part name
                part_attribs = info[part].get("attribs", {})
                part_name = part_attribs.get(
                    "name", part_attribs.get("oiio:subimage_name", "")
                )

            # Provide a nice label indicating the product
            source.label = self._get_label(context, part_name=part_name)
            project.addItem(source)

            # property.hidden = True  # hide the attribute
            lib.imprint(source, data={
                "name": str(name),
                "namespace": str(namespace),
                "loader": str(self.__class__.__name__),
                "representation": context["representation"]["id"],
            })

            self._set_source_frame_start_property(source, context)

    def filepath_from_context(self, context):
        # If the media is a sequence of files we need to load it with the
        # frames in the path as in file.[start-end].ext
        if context["representation"]["context"].get("frame"):
            anatomy = Anatomy(
                project_name=context["project"]["name"],
                project_entity=context["project"]
            )
            representation = context["representation"]
            files = [data["path"] for data in representation["files"]]
            files = [anatomy.fill_root(file) for file in files]

            collections, _remainder = clique.assemble(
                files, patterns=[clique.PATTERNS["frames"]]
            )
            collection = collections[0]
            frames = list(collection.indexes)
            start = str(frames[0]).zfill(collection.padding)
            end = str(frames[-1]).zfill(collection.padding)
            return collection.format(f"{{head}}[{start}-{end}]{{tail}}")

        return super().filepath_from_context(context)

    def _get_label(
        self, context: dict, part_name: Optional[str] = None
    ) -> str:
        """Return product name as label with the part name if provided."""
        label = context["product"]["name"]
        if part_name:
            label = f"{label} [{part_name}]"

        return label

    @lib.undo_chunk("Update Source")
    def update(self, container, context):
        # Update filepath
        item = container["_item"]
        item.property("path").value = self.filepath_from_context(context)

        # Update representation id
        data = lib.read(item)
        data["representation"] = context["representation"]["id"]
        lib.imprint(item, data)

        self._set_source_frame_start_property(item, context)

    @lib.undo_chunk("Remove container")
    def remove(self, container):
        """Remove all sub containers"""
        item = container["_item"]
        project = container["_project"]
        project.removeItem(item)

    def switch(self, container, context):
        """Support switch to another representation."""
        self.update(container, context)

    def _set_source_frame_start_property(
            self, source: fx.Source, context: dict):
        """Add a `frameStart` property to the source.

        This property is used to define the start frame for the source, which
        is used in the `object_created` hook to set the offset the loaded
        source from the session's start frame - this way the media actually
        plays from the expected frame even if the session does not start at
        the same frame as the source.
        """

        if "frameStart" not in context["version"]["attrib"]:
            return

        # Set the start frame for the source
        frame_start = context["version"]["attrib"]["frameStart"]

        # Property to store the start frame, we always recreate it so tht
        # the default value is the value we want it to be.
        prop = source.property("frameStart")
        if prop:
            source.removeProperty(prop)

        prop = fx.Property("frameStart", "Start Frame", frame_start)
        source.addProperty(prop)

    def _set_session_frame_range(self, context: dict):

        # Get the start frame from the loaded product
        lookup_entities = [
            # TODO: Allow taking from representation if it actually contains
            #  more sensible data. Currently it seems to just contain the
            #  task frame ranges by default?
            # context["representation"],
            context["version"]
        ]
        attrs = {"frameStart", "frameEnd", "handleStart", "handleEnd"}
        values = {}
        for attr in attrs:
            for entity in lookup_entities:
                if attr in entity.get("attrib", {}):
                    values[attr] = entity["attrib"][attr]
                    break

        if "frameStart" not in values:
            self.log.warning(
                "No start frame data found, cannot set start frame."
            )
            return

        active_session = fx.activeSession()
        if not active_session:
            self.log.warning("No active session, cannot set frame range.")
            return

        # Set start frame based on start frame with handle
        frame_start = values["frameStart"]
        handle_start = values.get("handleStart", 0)
        frame_start_handle = frame_start - handle_start
        active_session.startFrame = frame_start_handle

        # Set duration based on end frame from start frame
        if "frameEnd" not in values:
            self.log.warning(
                "No end frame data found, cannot set duration."
            )
            return

        frame_end = values["frameEnd"]
        handle_end = values.get("handleEnd", 0)
        frame_end_handle = frame_end + handle_end
        active_session.duration = (frame_end_handle - frame_start_handle) + 1
