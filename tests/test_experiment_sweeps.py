from fast_sim.core.rng import RNG
from fast_sim.core.state import State
from fast_sim.io.config import Config
from fast_sim.io.experiment import Experiment


def tick_fn(state: State, rng: RNG, t: float) -> None:
    counter = state["counter"]
    counter[0] += 1


def test_parameter_sweep(tmp_path):
    config_data = {
        "seed": 5,
        "state": {
            "size": 1,
            "fields": {
                "counter": {"dtype": "int64", "init": 0},
            },
        },
        "engine": {
            "type": "step",
            "dt": 1.0,
            "horizon": 5.0,
            "tick": "tests.test_experiment_sweeps:tick_fn",
        },
        "sweep": {"engine.horizon": [5.0, 7.0]},
    }
    cfg = Config.model_validate(config_data)
    exp = Experiment(cfg, sweep=cfg.sweep, runs=2)
    summary = exp.execute(tmp_path)
    assert len(summary.runs) == 4
    for run in summary.runs:
        assert run.metrics_path.exists()
        manifest = run.run_path / "manifest.json"
        assert manifest.exists()
    df = summary.result_set().concat()
    assert not df.empty
