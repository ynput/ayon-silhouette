import pyblish.api
import fx

from ayon_core.pipeline import publish
from ayon_silhouette.api import lib


class ValidateShapes(pyblish.api.InstancePlugin):
    """Validate shapes exist on node."""

    label = "Missing Shapes"
    hosts = ["silhouette"]
    families = ["matteshapes"]
    order = pyblish.api.ValidatorOrder

    def process(self, instance):
        # Node should be a node that contains 'shapes' children
        node = instance.data["transientData"]["instance_node"]
        if not any(
            shape for shape, _label in lib.iter_children(node)
            if isinstance(shape, fx.Shape)
        ):
            raise publish.PublishValidationError(
                "No shapes found on node: {0}".format(node.label)
            )
