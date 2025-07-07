"""Basic import tests to ensure package structure is valid."""


def test_mtop_imports():
    """Ensure package can be imported."""
    import mtop

    assert mtop.__version__ is not None


def test_core_module_imports():
    """Ensure all core modules import."""
    from column_engine import ColumnEngine
    from config_loader import load_config
    from mtop import container, interfaces, mtop_logging

    assert container is not None
    assert interfaces is not None
    assert mtop_logging is not None
    assert load_config is not None
    assert ColumnEngine is not None
