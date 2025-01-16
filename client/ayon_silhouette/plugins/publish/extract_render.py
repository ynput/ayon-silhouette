import os

from ayon_core.pipeline import publish

import fx
from tools.renderer import Renderer


def get_progress_handler(allow_popup=True):
    if fx.gui and allow_popup:
        return fx.PreviewProgressHandler()
    else:
        from tools.progress import CommandLineProgress
        return CommandLineProgress()


class SilhouetteExtractRender(publish.Extractor):
    label = "Render Output"
    hosts = ["silhouette"]
    families = ["render"]

    def process(self, instance):
        # TODO: Collect colorspace?
        # TODO: Support alpha + depth channels?
        # TODO: Support multiple views (L/R)?

        # Collect the start and end including handles
        start = instance.data["frameStartHandle"]
        end = instance.data["frameEndHandle"]

        output_node = instance.data["transientData"]["instance_node"]

        # Render node in the session
        session = instance.context.data["silhouetteSession"]
        renderer = Renderer()
        finished = renderer.render({
                "session": session,
                "nodes": [output_node],
                # Override frame range
                # "frames": list(range(start, end+1))
            },
            progress=get_progress_handler()
        )

        if not finished:
            raise publish.PublishError("Render was cancelled or interrupted.")

        outputs = renderer.outputs
        if not outputs:
            raise publish.PublishError("Render generated no outputs.")

        # Collect all rendered outputs
        filepaths = []
        for output in outputs:
            for frame in range(start, end+1):
                filepath = output.buildPath(frame)
                filepaths.append(filepath)

        # All files must exist. A rendered output may not exist due to
        # unexpected failures, or if the work range is smaller than the render
        # range.
        # TODO: Validate to handle render range out of work range better
        for filepath in filepaths:
            if not os.path.exists(filepath):
                raise publish.PublishError(f"File does not exist: {filepath}")

        # For now assume one output sequence per instance
        first_filepath = filepaths[0]
        files = [os.path.basename(path) for path in filepaths]
        staging_dir = os.path.dirname(first_filepath)
        ext = os.path.splitext(first_filepath)[-1]

        # Workaround: Single files must not be a list
        if len(files) == 1:
            files = files[0]

        representation = {
            "name": ext.lstrip("."),
            "ext": ext.lstrip("."),
            "files": files,
            "stagingDir": staging_dir,
        }
        instance.data.setdefault("representations", []).append(representation)

        self.log.debug(
            f"Extracted instance '{instance.name}' to: {filepaths[0]}")
