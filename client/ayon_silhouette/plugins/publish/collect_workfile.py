import os
import pyblish.api


class CollectWorkfileData(pyblish.api.InstancePlugin):
    """Inject project into Workfile instance"""

    order = pyblish.api.CollectorOrder - 0.01
    label = "Silhouette Workfile"
    families = ["workfile"]

    def process(self, instance):
        """Inject the current working file"""

        # Note that Silhouette project workfiles are actually folders,
        # not files.

        context = instance.context
        current_file = context.data["currentFile"]
        folder, file = os.path.split(current_file)
        filename, ext = os.path.splitext(file)

        data = {  # noqa
            "setMembers": [current_file],
            "frameStart": context.data["frameStart"],
            "frameEnd": context.data["frameEnd"],
            "handleStart": context.data["handleStart"],
            "handleEnd": context.data["handleEnd"]
        }

        data["representations"] = [{
            "name": ext.lstrip("."),
            "ext": ext.lstrip("."),
            "files": file,
            "stagingDir": folder,
        }]

        instance.data.update(data)
