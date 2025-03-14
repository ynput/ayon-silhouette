import fx
import clique

from ayon_silhouette.api import plugin, lib

from ayon_core.pipeline import Anatomy
from ayon_core.lib.transcoding import (
    VIDEO_EXTENSIONS, IMAGE_EXTENSIONS
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

    @lib.undo_chunk("Load Source")
    def load(self, context, name=None, namespace=None, options=None):
        project = fx.activeProject()
        if not project:
            raise RuntimeError("No active project found.")

        filepath = self.filepath_from_context(context)

        # Add Source item to the project
        source = fx.Source(filepath)

        # Provide a nice label indicating the product
        source.label = self._get_label(context)
        project.addItem(source)

        # property.hidden = True  # hide the attribute
        lib.imprint(source, data={
            "name": str(name),
            "namespace": str(namespace),
            "loader": str(self.__class__.__name__),
            "representation": context["representation"]["id"],
        })

        # container = pipeline.containerise(
        #     name=str(name),
        #     namespace=str(namespace),
        #     nodes=nodes,
        #     context=context,
        #     loader=str(self.__class__.__name__),
        # )

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

    def _get_label(self, context):
        return context["product"]["name"]

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
