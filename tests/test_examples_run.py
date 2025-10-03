from typer.testing import CliRunner

from fast_sim.cli import app
from fast_sim.examples import build_mm1_config, build_seir_config, build_traffic_config, run_mm1, run_seir, run_traffic


def test_example_functions():
    mm1_state = run_mm1(20.0)
    assert mm1_state["arrivals"][0] >= mm1_state["departures"][0]
    seir_state = run_seir(10.0)
    assert len(seir_state["status"]) == build_seir_config().state.size
    traffic_state = run_traffic(10.0)
    assert len(traffic_state["road"]) == build_traffic_config().state.size


def test_cli_run(tmp_path):
    runner = CliRunner()
    cfg = build_mm1_config()
    yaml_path = tmp_path / "config.yaml"
    from ruamel.yaml import YAML

    yaml = YAML()
    with yaml_path.open("w") as fh:
        yaml.dump(cfg.model_dump(mode="python"), fh)
    result = runner.invoke(app, ["run", str(yaml_path), "--out", str(tmp_path / "runs"), "--runs", "1"])
    assert result.exit_code == 0
    outputs = list((tmp_path / "runs").glob("**/metrics.*"))
    assert outputs
