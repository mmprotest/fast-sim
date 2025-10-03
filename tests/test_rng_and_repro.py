from fast_sim.core.rng import RNG


def test_spawn_reproducibility():
    rng = RNG(123)
    child_a1 = rng.spawn("stream-a")
    child_a2 = rng.spawn("stream-a")
    assert child_a1.normal(size=5) == child_a2.normal(size=5)


def test_child_independence():
    rng = RNG(123)
    child_a = rng.spawn("a")
    child_b = rng.spawn("b")
    values_a = child_a.random(10)
    values_b = child_b.random(10)
    assert values_a != values_b
