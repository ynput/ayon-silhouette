import pyblish.api


class CollectWorkfileData(pyblish.api.InstancePlugin):
    """Inject project data into Workfile instance"""

    order = pyblish.api.CollectorOrder - 0.01
    label = "Silhouette Workfile"
    families = ["workfile"]

    def process(self, instance):
        """Inject the current working file data"""
        context = instance.context
        instance.data.update({
            "frameStart": context.data["frameStart"],
            "frameEnd": context.data["frameEnd"],
            "handleStart": context.data["handleStart"],
            "handleEnd": context.data["handleEnd"]
        })
