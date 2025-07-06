"""Basic container tests to ensure dependency injection works."""


def test_container_singleton():
    """Container provides singletons."""
    from mtop.container import Container

    container = Container()

    class TestService:
        def __init__(self):
            self.value = "test"

    test_instance = TestService()
    container.register_singleton(TestService, test_instance)

    instance1 = container.get(TestService)
    instance2 = container.get(TestService)

    assert instance1 is instance2
    assert instance1.value == "test"


def test_container_creation():
    """Container can be created."""
    from mtop.container import Container

    container = Container()
    assert container is not None
