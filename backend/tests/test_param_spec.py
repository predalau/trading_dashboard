from app.backtest.param_spec import describe_params, _infer


class _Dummy:
    def __init__(self, params, spec=None):
        self.params = params
        self.param_spec = spec or []


def test_infer_bool_before_int():
    assert _infer("flag", True)["type"] == "bool"
    assert _infer("n", 5)["type"] == "int"
    assert _infer("x", 1.5)["type"] == "float"
    assert _infer("name", "abc")["type"] == "str"


def test_describe_derives_from_params_when_no_spec():
    spec = describe_params(_Dummy({"lookback": 12}))
    assert len(spec) == 1
    p = spec[0]
    assert p["name"] == "lookback" and p["type"] == "int"
    assert p["default"] == 12 and p["min"] == 1 and p["max"] >= 100 and p["step"] == 1


def test_describe_uses_declared_spec_and_fills_default():
    declared = [{"name": "fast", "type": "int", "min": 2, "max": 100, "step": 1}]
    spec = describe_params(_Dummy({"fast": 10}, declared))
    assert spec[0]["default"] == 10 and spec[0]["label"] == "fast"


def test_list_strategies_endpoint_includes_builtin_with_spec(client):
    r = client.get("/api/v1/backtest/strategies")
    assert r.status_code == 200, r.text
    data = r.json()
    sma = next((s for s in data if s["module"] == "strategies.sma_cross"), None)
    assert sma is not None, "built-in sma_cross should be listed"
    names = {p["name"] for p in sma["param_spec"]}
    assert {"fast", "slow"} <= names
