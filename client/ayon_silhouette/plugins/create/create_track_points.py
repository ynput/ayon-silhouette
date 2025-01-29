import fx

from ayon_core.lib import EnumDef
from ayon_silhouette.api import plugin, lib


class CreateTrackPoints(plugin.SilhouetteCreator):
    """Track Points"""

    identifier = "io.ayon.creators.silhouette.trackpoints"
    label = "Track Points"
    description = __doc__
    product_type = "trackpoints"
    icon = "cubes"

    create_node_type = "TrackerNode"
    valid_node_types = {"TrackerNode", "RotoNode"}

    def get_attr_defs_for_instance(self, instance):
        # Unfortunately in Creator.get_attr_defs_for_instance we can't access
        # any transient data because this gets called on `__init__` of the
        # instance directly, not after transient data was added to the instance
        # in the `create` or `collect` method. So we must find the node by
        # node id.
        node_id = instance.data.get("instance_id")
        node = fx.findObject(node_id)

        if not node:
            return []

        items = [
            {"label": label, "value": tracker}
            for tracker, label in lib.iter_children(node)
            if isinstance(tracker, fx.Tracker)
        ]
        if not items:
            items.append({
                "label": "<No trackers found>",
                "value": None
            })

        attr_defs = [
            EnumDef(
                "trackers",
                label="Export trackers",
                items=items,
                tooltip="Select trackers to include in output. If none are"
                        " selected then all trackers will be included.",
                multiselection=True,
            )
        ]

        return attr_defs

