"""Rendering helpers for widget items."""

from lazyclaude.models.customization import Customization, MemoryFileRef

MemoryFlatItem = tuple[Customization, MemoryFileRef | None, int]


def build_memory_flat_items(
    customizations: list[Customization],
    expanded_keys: set[str],
) -> list[MemoryFlatItem]:
    """Build flat list of memory items with expanded refs.

    Args:
        customizations: List of memory file customizations.
        expanded_keys: Set of expanded memory file keys (paths as strings).

    Returns:
        Flat list of (memory, ref, depth) tuples for display.
    """
    result: list[MemoryFlatItem] = []
    for memory in customizations:
        result.append((memory, None, 0))
        memory_key = str(memory.path)
        if memory_key in expanded_keys:
            refs: list[MemoryFileRef] = memory.metadata.get("refs", [])
            _add_refs_to_flat_list(result, memory, refs, depth=1)
    return result


def _add_refs_to_flat_list(
    result: list[MemoryFlatItem],
    memory: Customization,
    refs: list[MemoryFileRef],
    depth: int,
) -> None:
    """Add refs to flat list recursively with depth tracking."""
    for ref in refs:
        result.append((memory, ref, depth))
        if ref.children:
            _add_refs_to_flat_list(result, memory, ref.children, depth + 1)


def render_memory_item(
    index: int,
    memory: Customization,
    ref: MemoryFileRef | None,
    depth: int,
    *,
    selected_index: int,
    is_active: bool,
    expanded_keys: set[str],
) -> str:
    """Render a memory file item (memory root or referenced file).

    Args:
        index: Item index in the list.
        memory: The memory file customization.
        ref: The referenced file, or None for root memory file.
        depth: Indentation depth for nested refs.
        selected_index: Currently selected index in the panel.
        is_active: Whether the panel is active/focused.
        expanded_keys: Set of expanded memory file keys (paths as strings).

    Returns:
        Formatted string for display.
    """
    is_selected = index == selected_index and is_active
    prefix = ">" if is_selected else " "

    if ref is None:
        memory_key = str(memory.path)
        is_expanded = memory_key in expanded_keys
        has_refs = bool(memory.metadata.get("refs", []))
        expand_char = ("▼" if is_expanded else "▶") if has_refs else " "
        error_marker = " [red]![/]" if memory.has_error else ""
        return f"{prefix} {expand_char} {memory.display_name}{error_marker}"
    else:
        indent_str = "  " * depth
        exists_marker = "" if ref.exists else " [red]![/]"
        return f"{prefix} {indent_str}@{ref.name}{exists_marker}"
