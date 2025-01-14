import os

from ayon_core.pipeline import publish

from tools.renderer import Renderer


class SilhouetteExtractRender(publish.Extractor):
    label = "Render Output"
    hosts = ["silhouette"]
    families = ["render"]

    def process(self, instance):

        # Collect the start and end including handles
        # start = instance.data["frameStartHandle"]
        # end = instance.data["frameEndHandle"]

        # Define extract output file path
        dir_path = self.staging_dir(instance)
        filename = "{0}.mp4".format(instance.name)
        path = os.path.join(dir_path, filename)

        # TODO: Implement
        output_node = instance.data["transientData"]["instance_node"]

        # Render node in the session
        session = instance.context.data["silhouetteSession"]
        renderer = Renderer()
        # progress = PreviewProgressHandler()
        # progress.preview = True
        # progress.pixelAspect = session.pixelAspect
        renderer.render({
                "session": session,
                "nodes": [output_node],
                # Override frame range
                # "frames": list(range(start, end+1))
            },
            # progress=progress
        )

        # TODO: Get correct extension
        representation = {
            "name": "mp4",
            "ext": "mp4",
            "files": filename,
            "stagingDir": dir_path,
        }
        instance.data.setdefault("representations", []).append(representation)

        self.log.info(f"Extracted instance '{instance.name}' to: {path}")
