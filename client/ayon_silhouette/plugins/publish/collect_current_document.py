import pyblish.api

import fx


class CollectSilhouetteActiveDocument(pyblish.api.ContextPlugin):
    """Inject the active project and session"""

    order = pyblish.api.CollectorOrder - 0.5
    label = "Silhouette Active Project"
    hosts = ['silhouette']

    def process(self, context):

        project = fx.activeProject()
        session = fx.activeSession()
        if not project:
            self.log.warning("No active project found.")
        if not session:
            self.log.warning("No active session found.")

        context.data["silhouetteProject"] = project
        context.data["silhouetteSession"] = session

