from atom_mujoco.module_monitor import ModuleMonitor


def test_bounded_trace_and_latest_event_preserve_subscriber_order():
    monitor = ModuleMonitor()
    delivered = []
    monitor.on_event = delivered.append
    for index in range(250):
        monitor.emit('controller', 'running', str(index))
    monitor.emit('controller', 'completed', 'done')
    assert len(monitor.events) == 200
    assert len(delivered) == 251
    assert monitor.latest['controller'] == delivered[-1]
    assert list(monitor.events) == delivered[-200:]
    assert all(a.timestamp_s <= b.timestamp_s for a, b in zip(delivered, delivered[1:]))
