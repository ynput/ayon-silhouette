from ayon_server.settings import BaseSettingsModel, SettingsField


def bit_depth_enum_resolver() -> list[dict[str, str]]:
    return [
        {"label": "8 Bit", "value": "8"},
        {"label": "Float 16", "value": "F16"},
        {"label": "Float 32", "value": "F32"},
    ]


class SessionSettingsModel(BaseSettingsModel):
    bit_depth: str = SettingsField(
        "8",
        enum_resolver=bit_depth_enum_resolver,
        title="Bit Depth",
        description=(
            "Default bit depth for the workfile Session."
        ),
    )


DEFAULT_SILHOUETTE_SESSION_SETTINGS = {
    "bit_depth": "8",
}
