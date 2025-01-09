import pyblish.api


class CollectInstances(pyblish.api.InstancePlugin):
    label = "Collect Instances"
    order = pyblish.api.CollectorOrder - 0.4
    hosts = ["silhouette"]

    def process(self, instance):
        self.log.debug(f"Collecting members for {instance}")

        # Add the creator attributes to instance.data
        self.creator_attributes_to_instance_data(instance)

        # Define nice instance label
        instance_node = instance.data.get(
            "transientData", {}).get("instance_node")
        name = instance_node.label if instance_node else instance.name
        label = "{0} ({1})".format(name, instance.data["folderPath"])

        # Set frame start handle and frame end handle if frame ranges are
        # available
        if "frameStart" in instance.data and "frameEnd" in instance.data:
            # Enforce existence if handles
            instance.data.setdefault("handleStart", 0)
            instance.data.setdefault("handleEnd", 0)

            # Compute frame start handle and end start handle
            frame_start_handle = (
                instance.data["frameStart"] - instance.data["handleStart"]
            )
            frame_end_handle = (
                instance.data["frameEnd"] - instance.data["handleEnd"]
            )
            instance.data["frameStartHandle"] = frame_start_handle
            instance.data["frameEndHandle"] = frame_end_handle

            # Include frame range in label
            label += "  [{0}-{1}]".format(int(frame_start_handle),
                                          int(frame_end_handle))

        instance.data["label"] = label

    def creator_attributes_to_instance_data(self, instance):
        creator_attributes = instance.data.get("creator_attributes", {})
        if not creator_attributes:
            return

        for key, value in creator_attributes.items():
            if key in instance.data:
                continue

            instance.data[key] = value
