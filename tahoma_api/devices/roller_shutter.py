from typing import Optional, cast

from tahoma_api.devices.tahoma_device import TahomaDevice

CORE_CLOSURE_STATE = "core:ClosureState"
CORE_DEPLOYMENT_STATE = "core:DeploymentState"
CORE_PEDESTRIAN_POSITION_STATE = "core:PedestrianPositionState"
CORE_TARGET_CLOSURE_STATE = "core:TargetClosureState"

COMMAND_SET_CLOSURE = "setClosure"
COMMAND_SET_PEDESTRIAN_POSITION = "setPedestrianPosition"
COMMAND_SET_POSITION = "setPosition"


class RollerShutter(TahomaDevice):
    """Class to represent a roller shutter."""

    def get_position(self) -> Optional[int]:
        position = self.get_state(
            CORE_CLOSURE_STATE,
            CORE_DEPLOYMENT_STATE,
            CORE_PEDESTRIAN_POSITION_STATE,
            CORE_TARGET_CLOSURE_STATE,
        )
        return cast(int, position) if position else None

    def set_position(self, value: int) -> None:
        pass
        # command = self.select_command(
        #    COMMAND_SET_POSITION, COMMAND_SET_CLOSURE, COMMAND_SET_PEDESTRIAN_POSITION
        # )
        # self.send_command(command, value)

    def close(self) -> None:
        pass

    def open(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def identify(self) -> None:
        pass

    def is_closed(self) -> bool:
        pass
