import pandas as pd

from fast_sim.io.datasets import read_results, write_results


def test_results_roundtrip(tmp_path):
    df = pd.DataFrame({"metric": ["a", "b"], "t": [0, 1], "value": [1.0, 2.0]})
    state_df = pd.DataFrame({"x": [1, 2]})
    outputs = write_results(tmp_path, df, state_df)
    assert outputs["metrics"].exists()
    rs = read_results(tmp_path)
    combined = rs.concat()
    assert len(combined) == len(df)
    summary = rs.summary()
    assert not summary.empty
