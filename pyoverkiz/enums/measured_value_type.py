import sys
from enum import unique

# Since we support Python versions lower than 3.11, we use
# a backport for StrEnum when needed.
if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from backports.strenum import StrEnum


@unique
class MeasuredValueType(StrEnum):
    """See https://github.com/Somfy-Developer/Somfy-TaHoma-Developer-Mode/issues/68#issuecomment-1281474879"""

    ABSOLUTE_VALUE = "core:AbsoluteValue"
    ANGLE_IN_DEGREES = "core:AngleInDegrees"
    ANGULAR_SPEED_IN_DEGREES_PER_SECOND = "core:AngularSpeedInDegreesPerSecond"
    ELECTRICAL_ENERGY_IN_KWH = "core:ElectricalEnergyInKWh"
    ELECTRICAL_ENERGY_IN_WH = "core:ElectricalEnergyInWh"
    ELECTRICAL_POWER_IN_KW = "core:ElectricalPowerInKW"
    ELECTRICAL_POWER_IN_W = "core:ElectricalPowerInW"
    ELECTRIC_CURRENT_IN_AMPERE = "core:ElectricCurrentInAmpere"
    ELECTRIC_CURRENT_IN_MILLI_AMPERE = "core:ElectricCurrentInMilliAmpere"
    ENERGY_IN_CAL = "core:EnergyInCal"
    ENERGY_IN_KCAL = "core:EnergyInkCal"
    FLOW_IN_LITRE_PER_SECOND = "core:FlowInLitrePerSecond"
    FLOW_IN_METER_CUBE_PER_HOUR = "core:FlowInMeterCubePerHour"
    FLOW_IN_METER_CUBE_PER_SECOND = "core:FlowInMeterCubePerSecond"
    FOSSIL_ENERGY_IN_WH = "core:FossilEnergyInWh"
    GRADIENT_IN_PERCENTAGE_PER_SECOND = "core:GradientInPercentagePerSecond"
    LENGTH_IN_METER = "core:LengthInMeter"
    LINEAR_SPEED_IN_METER_PER_SECOND = "core:LinearSpeedInMeterPerSecond"
    LUMINANCE_IN_LUX = "core:LuminanceInLux"
    PARTS_PER_BILLION = "core:PartsPerBillion"
    PARTS_PER_MILLION = "core:PartsPerMillion"
    PARTS_PER_QUADRILLION = "core:PartsPerQuadrillion"
    PARTS_PER_TRILLION = "core:PartsPerTrillion"
    POWER_PER_SQUARE_METER = "core:PowerPerSquareMeter"
    PRESSURE_IN_HPA = "core:PressureInHpa"
    PRESSURE_IN_MILLI_BAR = "core:PressureInMilliBar"
    RELATIVE_VALUE_IN_PERCENTAGE = "core:RelativeValueInPercentage"
    TEMPERATURE_IN_CELCIUS = "core:TemperatureInCelcius"
    TEMPERATURE_IN_KELVIN = "core:TemperatureInKelvin"
    TIME_IN_SECOND = "core:TimeInSecond"
    VECTOR_COORDINATE = "core:VectorCoordinate"
    VOLTAGE_IN_MILLI_VOLT = "core:VoltageInMilliVolt"
    VOLTAGE_IN_VOLT = "core:VoltageInVolt"
    VOLUME_IN_CUBIC_METER = "core:VolumeInCubicMeter"
    VOLUME_IN_GALLON = "core:VolumeInGallon"
    VOLUME_IN_LITER = "core:VolumeInLiter"
