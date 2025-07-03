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

    @classmethod
    def get_options(cls, contexts):
        return [
            BoolDef(
                "load_all_parts",
                label="Load All Parts",
                default=True,
                tooltip="Load all parts of the source, "
                        "not just the first one."),
        ]

    @lib.undo_chunk("Load Source")
    def load(self, context, name=None, namespace=None, options=None):
        project = fx.activeProject()
        if not project:
            raise RuntimeError("No active project found.")

        filepath = self.filepath_from_context(context)

        # A source file may contain multiple parts, such as a left view
        # and a right view in a single EXR.
        options = options or {}
        load_all_parts = options.get("load_all_parts", True)

        # If the file is not an EXR or SXR, we can only load one part so force
        # disable loading multiple parts.
        if load_all_parts and os.path.splitext(filepath)[-1].lower() not in {
            ".exr", ".sxr"
        }:
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

    def _get_label(self, context: dict, part_name: Optional[str] = None) -> str:
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

    @lib.undo_chunk("Remove container")
    def remove(self, container):
        """Remove all sub containers"""
        item = container["_item"]
        project = container["_project"]
        project.removeItem(item)

    def switch(self, container, context):
        """Support switch to another representation."""
        self.update(container, context)
