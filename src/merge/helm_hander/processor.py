import logging
from pathlib import Path
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.scalarstring import ScalarString

def remove_aliases_yaml():
    yaml = YAML(typ='rt')
    yaml.preserve_quotes = True
    yaml.representer.ignore_aliases = lambda x: True
    return yaml

def make_yaml():
    yaml = YAML(typ='rt')
    yaml.preserve_quotes = True
    return yaml

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class WrappedNode:
    def __init__(
        self,
        value,
        path,
        file_path,
        line_no=None,
        quote_style=None,
        is_anchored=False,
        anchor_name=None,
        was_aliased=False,
    ):
        self.value = value
        self.path = path
        self.file_path = file_path
        self.line_no = line_no
        self.quote_style = quote_style
        self.is_anchored = is_anchored
        self.anchor_name = anchor_name
        self.was_aliased = was_aliased

    def __repr__(self):
        return (
            f"WrappedNode({self.path} @ {self.file_path}:{self.line_no} = {self.value!r}, "
            f"quote_style={self.quote_style!r}, anchor={self.anchor_name!r}, aliased={self.was_aliased})"
        )

def get_line_no(node):
    return getattr(getattr(node, "lc", None), "line", -1) + 1 if hasattr(node, "lc") else None

def get_quote_style(node):
    return getattr(node, "style", None) if isinstance(node, ScalarString) else None

def wrap_scalar_nodes(node, path="", file_path=""):
    if isinstance(node, CommentedMap):
        for k, v in node.items():
            child_path = f"{path}.{k}" if path else k
            node[k] = wrap_scalar_nodes(v, child_path, file_path)
        return node
    elif isinstance(node, CommentedSeq):
        new_seq = CommentedSeq()
        for idx, item in enumerate(node):
            child_path = f"{path}[{idx}]"
            line_no = get_line_no(item)
            wrapped_item = WrappedNode(
                value=item,
                path=child_path,
                file_path=file_path,
                line_no=line_no,
                quote_style=None,
                is_anchored=False,
                anchor_name=None,
                was_aliased=False,
            )
            new_seq.append(wrapped_item)
        return new_seq
    elif isinstance(node, (str, int, float, bool, type(None))):
        quote_style = get_quote_style(node)
        line_no = get_line_no(node)
        is_anchored = hasattr(node, "anchor") and bool(getattr(node, "anchor", None).value)
        anchor_name = getattr(getattr(node, "anchor", None), "value", None)
        was_aliased = getattr(node, "anchor", None) is not None and getattr(node.anchor, "always_dump", False)
        return WrappedNode(
            value=node,
            path=path,
            file_path=file_path,
            line_no=line_no,
            quote_style=quote_style,
            is_anchored=is_anchored,
            anchor_name=anchor_name,
            was_aliased=was_aliased,
        )
    else:
        return node

def load_yaml_with_wrapped_scalars(file_path):
    data = load_yaml(file_path, remove_aliases_yaml)
    file_name = Path(file_path).name
    wrap_scalar_nodes(data, "", file_name)
    return data

def load_yaml(file_path, yaml_method = make_yaml):
    yaml = yaml_method()
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return yaml.load(f)

def dump_yaml(data, output_file_path, yaml_method = make_yaml):
    yaml = yaml_method()
    with open(output_file_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f)

def strip_anchor(node):
    if hasattr(node, "anchor"):
        node.anchor.value = None
    return node

def _unwrap_value(node):
    return getattr(node, "value", node)

def _get_anchor_name(node):
    return getattr(getattr(node, "anchor", None), "value", None)

def _collect_anchors(node, anchor_map):
    if isinstance(node, (CommentedMap, dict)):
        for k, v in node.items():
            name = _get_anchor_name(v)
            if name:
                anchor_map[name] = v
            _collect_anchors(v, anchor_map)
    elif isinstance(node, (CommentedSeq, list)):
        for item in node:
            name = _get_anchor_name(item)
            if name:
                anchor_map[name] = item
            _collect_anchors(item, anchor_map)

def update_yaml_from_wrapped_data(wrapped_node_dict, target_file_path, output_file_path):
    target_data = load_yaml(target_file_path)
    updates_made = []
    anchor_map = {}
    _collect_anchors(target_data, anchor_map)

    def recursive_update(wrapped, target, base_path=""):
        if isinstance(wrapped, (CommentedMap, dict)) and isinstance(target, (CommentedMap, dict)):
            for key, wrapped_value in wrapped.items():
                if key not in target:
                    continue
                child_path = f"{base_path}.{key}" if base_path else str(key)
                if isinstance(wrapped_value, WrappedNode):
                    new_scalar = _unwrap_value(wrapped_value.value)
                    current_target = target[key]
                    current_scalar = _unwrap_value(current_target)
                    if new_scalar != current_scalar:
                        logger.info(f"Updating {child_path}: {current_scalar!r} -> {new_scalar!r}")
                        target_anchor_name = _get_anchor_name(current_target)
                        if target_anchor_name:
                            if hasattr(current_target, "value"):
                                current_target.value = new_scalar
                            else:
                                target[key] = new_scalar
                        else:
                            source_anchor_name = wrapped_value.anchor_name
                            if source_anchor_name and source_anchor_name in anchor_map:
                                anchor_node = anchor_map[source_anchor_name]
                                if hasattr(anchor_node, "value"):
                                    anchor_node.value = new_scalar
                                else:
                                    anchor_map[source_anchor_name] = new_scalar
                                logger.debug(f" - Updated anchor definition {source_anchor_name}")
                            else:
                                target[key] = new_scalar
                        updates_made.append(child_path)
                    else:
                        logger.debug(f"Skipping {child_path} (no change)")
                else:
                    recursive_update(wrapped_value, target[key], child_path)
        elif isinstance(wrapped, (CommentedSeq, list)) and isinstance(target, (CommentedSeq, list)):
            for idx, item in enumerate(wrapped):
                child_path = f"{base_path}[{idx}]"
                if idx < len(target):
                    if isinstance(item, WrappedNode):
                        new_scalar = _unwrap_value(item.value)
                        current_target = target[idx]
                        current_scalar = _unwrap_value(current_target)
                        if new_scalar != current_scalar:
                            logger.info(f"Updating {child_path}: {current_scalar!r} -> {new_scalar!r}")
                            target_anchor_name = _get_anchor_name(current_target)
                            if target_anchor_name and hasattr(current_target, "value"):
                                current_target.value = new_scalar
                            else:
                                source_anchor_name = item.anchor_name
                                if source_anchor_name and source_anchor_name in anchor_map:
                                    anchor_node = anchor_map[source_anchor_name]
                                    if hasattr(anchor_node, "value"):
                                        anchor_node.value = new_scalar
                                    else:
                                        anchor_map[source_anchor_name] = new_scalar
                                    logger.debug(f" - Updated anchor definition {source_anchor_name}")
                                else:
                                    target[idx] = new_scalar
                            updates_made.append(child_path)
                        else:
                            logger.debug(f"Skipping {child_path} (no change)")
                    else:
                        recursive_update(item, target[idx], child_path)
                else:
                    val_to_append = _unwrap_value(item.value) if isinstance(item, WrappedNode) else item
                    target.append(val_to_append)
                    updates_made.append(child_path)

    recursive_update(wrapped_node_dict, target_data, "")
    dump_yaml(target_data, output_file_path)
    logger.info(f"Update complete. {len(updates_made)} paths updated.")
    return updates_made
