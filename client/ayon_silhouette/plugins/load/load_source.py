import json

import fx

from ayon_silhouette.api import plugin


class SourceLoader(plugin.SilhouetteLoader):
    """Load media source."""

    color = "orange"
    product_types = {"*"}
    icon = "code-fork"
    label = "Load Source"
    order = -10
    representations = {"*"}

    def load(self, context, name=None, namespace=None, options=None):
        """Merge the Alembic into the scene."""

        project = fx.activeProject()
        if not project:
            raise RuntimeError("No active project found.")

        filepath = self.filepath_from_context(context)

        # Add Source item to the project
        source = fx.Source(filepath)

        # Provide a nice label indicating the product
        source.label = self._get_label(context)
        project.addItem(source)

        # Add AYON property
        # Arguments are `id`, `label` and `default_value`. By passing the
        # default value as empty string we make it a visible string attribute.
        property = fx.Property("AYON", "AYON", "")
        source.addProperty(property)

        # property.hidden = True  # hide the attribute
        property.value = json.dumps({
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

    def _get_label(self, context):
        return context["product"]["name"]

    def update(self, container, context):
        # Update filepath
        item = container["_item"]
        item.property("path").value = self.filepath_from_context(context)

        # Update representation id
        data = json.loads(item.property("AYON").value)
        data["representation"] = context["representation"]["id"]
        item.property("AYON").value = json.dumps(data)

    def remove(self, container):
        """Remove all sub containers"""
        item = container["_item"]
        project = container["_project"]
        project.removeItem(item)