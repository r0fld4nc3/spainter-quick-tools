from dataclasses import dataclass, field


@dataclass
class ToggleLayersToolSettings:
    unchecked_texture_sets: set[str] = field(default_factory=set)
    on_names: str = ""
    off_names: str = ""
    loose_matching: bool = False


@dataclass
class Settings:
    """
    Session-only settings, kep in memory until Painter closes.
    """

    toggle_layers_tool: ToggleLayersToolSettings = field(default_factory=ToggleLayersToolSettings)


SessionSettings: Settings = Settings()
