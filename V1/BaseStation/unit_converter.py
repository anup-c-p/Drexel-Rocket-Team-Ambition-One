from config import ATMOSPHERIC_PRESSURE_PSI


class UnitConverter:
    """Converts raw sensor voltages to engineering units for UI display.

    Raw voltages are always preserved for file and SQL logging — only the UI
    reads from this class.
    """

    @staticmethod
    def voltage_to_psi(voltage: float) -> float:
        """Pressure transducer: P (PSI) = 200 * V + atmospheric_pressure."""
        return 200.0 * voltage + ATMOSPHERIC_PRESSURE_PSI

    @staticmethod
    def voltage_to_lbf(voltage: float) -> float:
        """Force transducer: mV = voltage * 1000"""
        return voltage * 1000.0
