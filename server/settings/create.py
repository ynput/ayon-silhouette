from ayon_server.settings import BaseSettingsModel, SettingsField


class ProductTypeItemModel(BaseSettingsModel):
    _layout = "compact"
    product_type: str = SettingsField(
        "",
        title="Product type",
        description="Product type name",
    )
    label: str = SettingsField(
        "",
        title="Label",
        description="Label to display in UI for the product type",
    )


class CreatePluginModel(BaseSettingsModel):
    enabled: bool = SettingsField(
        True,
        title="Enabled",
    )
    product_type_items: list[ProductTypeItemModel] = SettingsField(
        default_factory=list,
        title="Product type items",
        description=(
            "Optional list of product types that this plugin can create."
        )
    )


class CreatePluginsModel(BaseSettingsModel):
    CreateMatteShapes: CreatePluginModel = SettingsField(
        title="Matte Shapes",
        description="Create Matte Shapes plugin settings.",
    )
    CreateRender: CreatePluginModel = SettingsField(
        title="Render",
        description="Create Render plugin settings.",
    )
    CreateTrackPoints: CreatePluginModel = SettingsField(
        title="Track Points",
        description="Create Track Points plugin settings.",
    )


DEFAULT_SILHOUETTE_CREATE_SETTINGS = {
    "CreateMatteShapes": {
        "enabled": True,
        "product_type_items": [],
    },
    "CreateRender": {
        "enabled": True,
        "product_type_items": [],
    },
    "CreateTrackPoints": {
        "enabled": True,
        "product_type_items": [],
    },
}
