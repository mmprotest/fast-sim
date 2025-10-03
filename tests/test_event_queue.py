from fast_sim.core.event_queue import Event, EventQueue


def test_event_queue_ordering():
    queue = EventQueue()
    queue.push(Event(time=5.0, priority=0, kind="A"))
    queue.push(Event(time=1.0, priority=0, kind="B"))
    queue.push(Event(time=1.0, priority=1, kind="C"))
    first = queue.pop()
    second = queue.pop()
    third = queue.pop()
    assert first.kind == "B"
    assert second.kind == "C"
    assert third.kind == "A"
