import pytest
import pandas as pd
import os
import json
from nucleo.utilidades import (
    validate_inputs,
    save_history,
    load_history,
    export_history_csv,
    estimate_water_saving,
    clear_history,
    timestamp
)


def test_validate_inputs_valid():
    # Should not raise
    validate_inputs(25.0, 50.0, 20.0, 60.0, 10.0)


@pytest.mark.parametrize("temp", [-1, 46])
def test_validate_inputs_temperature_invalid(temp):
    with pytest.raises(ValueError, match="temperatura"):
        validate_inputs(temp, 50.0, 20.0, 60.0, 10.0)


@pytest.mark.parametrize("humidity", [-1, 101])
def test_validate_inputs_soil_humidity_invalid(humidity):
    with pytest.raises(ValueError, match="humedad del suelo"):
        validate_inputs(25.0, humidity, 20.0, 60.0, 10.0)


@pytest.mark.parametrize("rain_prob", [-1, 101])
def test_validate_inputs_rain_probability_invalid(rain_prob):
    with pytest.raises(ValueError, match="probabilidad de lluvia"):
        validate_inputs(25.0, 50.0, rain_prob, 60.0, 10.0)


@pytest.mark.parametrize("air_humidity", [-1, 101])
def test_validate_inputs_air_humidity_invalid(air_humidity):
    with pytest.raises(ValueError, match="humedad ambiental"):
        validate_inputs(25.0, 50.0, 20.0, air_humidity, 10.0)


@pytest.mark.parametrize("wind_speed", [-1, 51])
def test_validate_inputs_wind_speed_invalid(wind_speed):
    with pytest.raises(ValueError, match="velocidad del viento"):
        validate_inputs(25.0, 50.0, 20.0, 60.0, wind_speed)


def test_save_and_load_history(tmp_path):
    # Use temporary directory
    import nucleo.utilidades
    original_data_dir = nucleo.utilidades.DATA_DIR
    nucleo.utilidades.DATA_DIR = str(tmp_path)
    nucleo.utilidades.HISTORY_CSV = os.path.join(str(tmp_path), "history.csv")
    nucleo.utilidades.HISTORY_JSONL = os.path.join(str(tmp_path), "history.jsonl")

    # Clear any existing
    clear_history()

    record = {
        "ts": 1234567890,
        "temperatura": 25.0,
        "humedad_suelo": 50.0,
        "prob_lluvia": 20.0,
        "humedad_ambiental": 60.0,
        "viento": 10.0,
        "planta": "tomate",
        "tiempo_min": 30.0,
        "frecuencia": 2.0,
    }

    save_history(record)

    df = load_history()
    assert len(df) == 1
    assert df.iloc[0]["temperatura"] == 25.0
    assert df.iloc[0]["planta"] == "tomate"

    # Test JSONL
    with open(nucleo.utilidades.HISTORY_JSONL, "r") as f:
        lines = f.readlines()
        assert len(lines) == 1
        loaded_record = json.loads(lines[0])
        assert loaded_record["temperatura"] == 25.0

    # Restore
    nucleo.utilidades.DATA_DIR = original_data_dir
    nucleo.utilidades.HISTORY_CSV = os.path.join(original_data_dir, "history.csv")
    nucleo.utilidades.HISTORY_JSONL = os.path.join(original_data_dir, "history.jsonl")


@pytest.mark.parametrize("tiempo,frecuencia,expected", [
    (30.0, 2.0, (100 * 7) * ((60*3 - 30*2) / (60*3))),  # approx 466.7
    (60.0, 4.0, (100 * 7) * ((60*3 - 60*4) / (60*3))),  # below 0, so 0
    (0.0, 0.0, 700.0),
])
def test_estimate_water_saving(tiempo, frecuencia, expected):
    # Simplified calculation
    ahorro = estimate_water_saving(tiempo, frecuencia)
    if tiempo == 60.0 and frecuencia == 4.0:
        assert ahorro == 0.0  # clamped below to 0
    elif tiempo == 0.0 and frecuencia == 0.0:
        assert ahorro == 700.0
    else:
        base = 60.0 * 3.0
        actual = tiempo * frecuencia
        ahorro_rel = max(0.0, (base - actual) / base)
        expected_exact = round(ahorro_rel * 100.0 * 7.0, 1)
        assert ahorro == expected_exact


def test_timestamp():
    ts = timestamp()
    assert isinstance(ts, int)
    assert ts > 0


def test_clear_history(tmp_path):
    import nucleo.utilidades
    original_data_dir = nucleo.utilidades.DATA_DIR
    nucleo.utilidades.DATA_DIR = str(tmp_path)
    nucleo.utilidades.HISTORY_CSV = os.path.join(str(tmp_path), "history.csv")
    nucleo.utilidades.HISTORY_JSONL = os.path.join(str(tmp_path), "history.jsonl")

    # Add something
    record = {"ts": 1, "temperatura": 25.0, "humedad_suelo": 50.0, "prob_lluvia": 20.0, "humedad_ambiental": 60.0, "viento": 10.0, "planta": "test", "tiempo_min": 30.0, "frecuencia": 2.0}
    save_history(record)
    df = load_history()
    assert len(df) == 1

    clear_history()
    df = load_history()
    assert len(df) == 0

    # Restore
    nucleo.utilidades.DATA_DIR = original_data_dir
    nucleo.utilidades.HISTORY_CSV = os.path.join(original_data_dir, "history.csv")
    nucleo.utilidades.HISTORY_JSONL = os.path.join(original_data_dir, "history.jsonl")
