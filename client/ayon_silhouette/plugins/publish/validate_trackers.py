import pyblish.api
import fx

from ayon_core.pipeline import publish


class ValidateTrackers(pyblish.api.InstancePlugin):
    """Validate trackers exist on node."""

    label = "Missing Trackers"
    hosts = ["silhouette"]
    families = ["trackpoints"]
    order = pyblish.api.ValidatorOrder

    def process(self, instance):
        # Node should be a node that contains 'tracker' children
        node = instance.data["transientData"]["instance_node"]
        if not any(
            tracker for tracker in node.children
            if isinstance(tracker, fx.Tracker)
        ):
            raise publish.PublishValidationError(
                "No trackers found on node: {0}".format(node.label)
            )