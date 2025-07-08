#!/usr/bin/env python3
"""
Dynamic column engine for configurable table display
"""

from typing import Any, Callable, Dict, List, Optional

from .config_loader import ColorThreshold, ColumnConfig, Config

# Try to import rich for table functionality
try:
    from rich.table import Table

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class ColumnEngine:
    """Handles dynamic column generation and formatting based on configuration"""

    def __init__(self, config: Config):
        if not RICH_AVAILABLE:
            raise ImportError(
                "Rich library is required for column display. Install with: pip install rich"
            )

        self.config = config
        self.enabled_columns = [col for col in config.display.columns if col.enabled]
        self.sortable_columns = self._build_sortable_mapping()
        self.formatters = self._init_formatters()

    def _build_sortable_mapping(self) -> Dict[str, ColumnConfig]:
        """Build mapping of sort keys to column configurations"""
        mapping = {}
        for col in self.enabled_columns:
            if col.sortable and col.sort_key:
                mapping[col.sort_key] = col
        return mapping

    def _init_formatters(self) -> Dict[str, Callable]:
        """Initialize formatting functions for different data types"""
        return {
            "string": lambda x: str(x),
            "integer": lambda x: str(int(x)),
            "integer_comma": lambda x: f"{int(x):,}",
            "percentage": lambda x: f"{int(x)}%",
            "percentage_1dp": lambda x: f"{x:.1f}%",
            "latency_ms": lambda x: f"{int(x)}ms",
            "emoji_status": self._format_status,
            "vram_usage": self._format_vram,
        }

    def _format_status(self, status: str) -> str:
        """Format status with emoji"""
        if status == "Ready":
            return "🟢 Ready"
        elif status == "NotReady":
            return "🔴 NotReady"
        elif status == "Degraded":
            return "🔴 Degraded"
        elif status == "Recovering":
            return "🟡 Recovering"
        else:
            return "⚪ Unknown"

    def _format_vram(self, vram_data: Any) -> str:
        """Format VRAM usage - placeholder for future implementation"""
        if hasattr(vram_data, "used") and hasattr(vram_data, "total"):
            return f"{vram_data.used}/{vram_data.total}"
        return "N/A"

    def create_table(self) -> Table:
        """Create Rich table with configured columns"""
        table = Table(show_header=True, header_style="bold cyan")

        for col in self.enabled_columns:
            table.add_column(col.name, width=col.width, justify=col.justify)

        return table

    def format_row(self, metrics: Any) -> List[str]:
        """Format a single row of data using configured columns"""
        row_data = []

        for col in self.enabled_columns:
            # Get raw value from metrics object
            raw_value = self._get_field_value(metrics, col.field)

            # Apply formatting
            formatted_value = self._apply_formatting(raw_value, col)

            # Apply color styling if configured
            styled_value = self._apply_color_styling(formatted_value, raw_value, col)

            # Apply truncation if configured
            final_value = self._apply_truncation(styled_value, col)

            row_data.append(final_value)

        return row_data

    def _get_field_value(self, metrics: Any, field: str) -> Any:
        """Get field value from metrics object"""
        try:
            return getattr(metrics, field)
        except AttributeError:
            # Handle special cases or nested fields
            if field == "name":
                return getattr(metrics, "name", "Unknown")
            return "N/A"

    def _apply_formatting(self, value: Any, col: ColumnConfig) -> str:
        """Apply configured formatting to a value"""
        formatter = self.formatters.get(col.format, self.formatters["string"])
        try:
            return formatter(value)
        except (ValueError, TypeError):
            return str(value)

    def _apply_color_styling(self, formatted_value: str, raw_value: Any, col: ColumnConfig) -> str:
        """Apply color styling based on thresholds"""
        if not col.color_thresholds:
            return formatted_value

        # Determine color based on thresholds
        color = self._determine_color(raw_value, col.color_thresholds)

        if color and color != "white":
            return f"[{color}]{formatted_value}[/{color}]"
        return formatted_value

    def _determine_color(self, value: float, thresholds: List[ColorThreshold]) -> Optional[str]:
        """Determine color based on value and thresholds"""
        try:
            numeric_value = float(value)
        except (ValueError, TypeError):
            return None

        for threshold in thresholds:
            if threshold.min is not None and threshold.max is not None:
                if threshold.min <= numeric_value <= threshold.max:
                    return threshold.color
            elif threshold.min is not None:
                if numeric_value >= threshold.min:
                    return threshold.color
            elif threshold.max is not None:
                if numeric_value <= threshold.max:
                    return threshold.color

        return None

    def _apply_truncation(self, value: str, col: ColumnConfig) -> str:
        """Apply truncation if configured"""
        if col.truncate and len(value) > col.truncate:
            # Account for Rich markup when truncating
            if "[" in value and "]" in value:
                # Complex case: preserve markup while truncating
                return self._truncate_with_markup(value, col.truncate)
            else:
                # Simple case: just truncate
                return value[: col.truncate] + ("..." if len(value) > col.truncate else "")
        return value

    def _truncate_with_markup(self, value: str, max_length: int) -> str:
        """Truncate string while preserving Rich markup"""
        # This is a simplified implementation
        # For a full implementation, you'd need to parse Rich markup properly
        if len(value) > max_length + 20:  # Account for markup overhead
            return value[:max_length] + "..."
        return value

    def get_sort_key_function(self, sort_key: str) -> Optional[Callable]:
        """Get sorting function for a given sort key"""
        if sort_key not in self.sortable_columns:
            return None

        col = self.sortable_columns[sort_key]
        field = col.field

        if sort_key == "name":
            return lambda item: item[0]  # Sort by name (first element of tuple)
        else:
            return lambda item: getattr(item[1], field, 0)  # Sort by metric field

    def get_available_sort_keys(self) -> List[str]:
        """Get list of available sort keys"""
        return list(self.sortable_columns.keys())

    def get_default_sort_key(self) -> str:
        """Get default sort key from configuration"""
        return self.config.display.sorting.get("default_key", "name")

    def validate_sort_key(self, sort_key: str) -> bool:
        """Validate if a sort key is available"""
        available_keys = self.config.display.sorting.get("available_keys", [])
        return sort_key in available_keys and sort_key in self.sortable_columns


class TableRenderer:
    """High-level table rendering with configuration"""

    def __init__(self, config: Config):
        self.engine = ColumnEngine(config)
        self.config = config

    def create_table_with_data(self, models_data: Dict[str, Any], sort_key: str = None) -> Table:
        """Create complete table with data"""
        table = self.engine.create_table()

        # Determine sort key
        if sort_key is None:
            sort_key = self.engine.get_default_sort_key()

        # Validate sort key
        if not self.engine.validate_sort_key(sort_key):
            sort_key = self.engine.get_default_sort_key()

        # Sort the data
        sort_func = self.engine.get_sort_key_function(sort_key)
        if sort_func:
            if sort_key == "name":
                sorted_items = sorted(models_data.items(), key=sort_func)
            else:
                sorted_items = sorted(models_data.items(), key=sort_func, reverse=True)
        else:
            sorted_items = list(models_data.items())

        # Add rows to table
        for name, metrics in sorted_items:
            row_data = self.engine.format_row(metrics)
            table.add_row(*row_data)

        return table

    def get_table_title(self) -> str:
        """Get table title from configuration"""
        emoji = self.config.build.branding.emoji
        return f"{emoji} Live LLM Inference Traffic"


# Convenience functions
def create_table_renderer(config_path: str = "config/config.yaml") -> TableRenderer:
    """Create table renderer from config file"""
    from .config_loader import load_config

    config = load_config(config_path)
    return TableRenderer(config)


def get_default_table_renderer() -> TableRenderer:
    """Get table renderer with default configuration"""
    from .config_loader import get_default_config

    config = get_default_config()
    return TableRenderer(config)


if __name__ == "__main__":
    # Test the column engine
    try:
        from .config_loader import load_config

        config = load_config()
        engine = ColumnEngine(config)

        print("✅ ColumnEngine created successfully")
        print(f"Enabled columns: {len(engine.enabled_columns)}")
        print(f"Sortable columns: {list(engine.sortable_columns.keys())}")
        print(f"Default sort key: {engine.get_default_sort_key()}")

        # Test table creation
        table = engine.create_table()
        print("✅ Table creation successful")

    except Exception as e:
        print(f"❌ ColumnEngine error: {e}")
