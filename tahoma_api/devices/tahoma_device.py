from typing import Optional

from tahoma_api.models import Device


class TahomaDevice:
    def __init__(self, device: Device) -> None:
        self.device = device

    def get_state(self, *states: str) -> Optional[str]:
        """Get the value of the first existing state."""
        if self.device.states:
            return next(
                (
                    state.value
                    for state in self.device.states
                    if state.name in list(states)
                ),
                None,
            )
        return None

    def select_command(self, *commands: str) -> Optional[str]:
        """Select first existing command in a list of commands."""
        return next(
            (
                command.command_name
                for command in self.device.definition.commands
                if command.command_name in list(commands)
            ),
            None,
        )

    def send_command(self, command_name: Optional[str] = None,) -> None:
        pass
        # if command_name is None:
        #    raise ValueError("Missing command name.")
        # TODO Parameter
