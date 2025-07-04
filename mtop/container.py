"""Dependency injection container for mtop."""

import inspect
from threading import Lock
from typing import Any, Callable, Dict, Type, TypeVar, Union, cast, get_origin, get_args

T = TypeVar("T")


class Container:
    """Simple dependency injection container."""

    def __init__(self) -> None:
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable[..., Any]] = {}
        self._singletons: Dict[str, Any] = {}
        self._lock = Lock()

    def register_singleton(self, interface: Type[T], instance: T) -> None:
        """Register a singleton instance."""
        key = self._get_key(interface)
        with self._lock:
            self._singletons[key] = instance

    def register_factory(self, interface: Type[T], factory: Callable[..., T]) -> None:
        """Register a factory function."""
        key = self._get_key(interface)
        with self._lock:
            self._factories[key] = factory

    def register_transient(self, interface: Type[T], implementation: Type[T]) -> None:
        """Register a transient service (new instance each time)."""
        key = self._get_key(interface)
        with self._lock:
            self._services[key] = implementation

    def get(self, interface: Type[T]) -> T:
        """Get an instance of the requested interface."""
        key = self._get_key(interface)

        # Check singletons first
        if key in self._singletons:
            return cast(T, self._singletons[key])

        # Check factories
        if key in self._factories:
            factory = self._factories[key]
            instance = self._create_with_dependencies(factory)
            return cast(T, instance)

        # Check transient services
        if key in self._services:
            service_type = self._services[key]
            instance = self._create_with_dependencies(service_type)
            return cast(T, instance)

        raise ValueError(f"No registration found for {interface}")

    def _get_key(self, interface: Type[Any]) -> str:
        """Get string key for interface type."""
        return f"{interface.__module__}.{interface.__name__}"

    def _create_with_dependencies(self, target: Union[Type[Any], Callable[..., Any]]) -> Any:
        """Create instance with automatic dependency injection."""
        if inspect.isclass(target):
            constructor = target.__init__
            sig = inspect.signature(constructor)
        else:
            sig = inspect.signature(target)

        kwargs = {}
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue

            if param.annotation and param.annotation != inspect.Parameter.empty:
                # Handle Optional[T] types by extracting T
                actual_type = param.annotation
                if get_origin(param.annotation) is Union:
                    args = get_args(param.annotation)
                    # Check if it's Optional[T] (Union[T, None])
                    if len(args) == 2 and type(None) in args:
                        actual_type = args[0] if args[1] is type(None) else args[1]
                
                try:
                    kwargs[param_name] = self.get(actual_type)
                except ValueError:
                    if param.default != inspect.Parameter.empty:
                        kwargs[param_name] = param.default
                    else:
                        raise ValueError(
                            f"Cannot resolve dependency {actual_type} for parameter {param_name}"
                        )

        if inspect.isclass(target):
            return target(**kwargs)
        else:
            return target(**kwargs)


# Global container instance
_container: Container = Container()


def get_container() -> Container:
    """Get the global container instance."""
    return _container


def inject(interface: Type[T]) -> T:
    """Convenience function to inject dependencies."""
    return _container.get(interface)


def singleton(interface: Type[T]) -> Callable[[T], T]:
    """Decorator to register a class as a singleton."""

    def decorator(cls: T) -> T:
        instance = cls()  # type: ignore
        _container.register_singleton(interface, instance)
        return cls

    return decorator


def transient(interface: Type[T]) -> Callable[[Type[T]], Type[T]]:
    """Decorator to register a class as transient."""

    def decorator(cls: Type[T]) -> Type[T]:
        _container.register_transient(interface, cls)
        return cls

    return decorator


def factory(interface: Type[T]) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to register a factory function."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        _container.register_factory(interface, func)
        return func

    return decorator
