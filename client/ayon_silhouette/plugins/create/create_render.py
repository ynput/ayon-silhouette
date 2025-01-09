from ayon_silhouette.api import (
    lib,
    plugin
)


class CreateRender(plugin.SilhouetteCreator):
    """Render Output"""

    identifier = "io.ayon.creators.silhouette.render"
    label = "Render"
    description = __doc__
    product_type = "render"
    icon = "eye"

    # TODO: Set default output filepath?

    def get_instance_attr_defs(self):
        defs = lib.collect_animation_defs(self.create_context)
        return defs
