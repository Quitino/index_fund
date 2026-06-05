import pandas as pd
import pytest
from xalpha.cons import pd_to_datetime


def test_pd_to_datetime_single_string():
    res = pd_to_datetime("2023-01-01")
    assert isinstance(res, pd.Timestamp)
    assert res == pd.Timestamp("2023-01-01")


def test_pd_to_datetime_list():
    res = pd_to_datetime(["2023-01-01", "2023-01-02"])
    assert isinstance(res, pd.DatetimeIndex)
    assert res[0] == pd.Timestamp("2023-01-01")


def test_pd_to_datetime_series():
    series = pd.Series(["2023-01-01", "2023-01-02"])
    res = pd_to_datetime(series)
    # pd.to_datetime(pd.Series) returns a pd.Series
    assert isinstance(res, pd.Series)
    assert res.iloc[0] == pd.Timestamp("2023-01-01")


def test_pd_to_datetime_with_format():
    res = pd_to_datetime("20230101", format="%Y%m%d")
    assert res == pd.Timestamp("2023-01-01")


def test_pd_to_datetime_already_datetime():
    dt = pd.Timestamp("2023-01-01")
    res = pd_to_datetime(dt)
    assert res == dt


def test_pd_to_datetime_mixed_format():
    # This test verifies behavior for mixed formats, which pd_to_datetime handles
    res = pd_to_datetime(["2023-01-01", "2023/01/02"])
    assert res[0] == pd.Timestamp("2023-01-01")
    assert res[1] == pd.Timestamp("2023-01-02")


def test_pd_to_datetime_invalid_string():
    # Verify that invalid strings raise a ValueError by default (standard pandas behavior)
    with pytest.raises(ValueError):
        pd_to_datetime("not-a-date")


def test_pd_to_datetime_errors_coerce():
    # Verify that errors='coerce' works as expected
    res = pd_to_datetime("not-a-date", errors="coerce")
    assert pd.isna(res)
