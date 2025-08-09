import logging
from pathlib import Path
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.scalarstring import ScalarString

yaml = YAML()
yaml.preserve_quotes = True

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
    data = load_yaml(file_path)
    file_name = Path(file_path).name
    wrap_scalar_nodes(data, "", file_name)
    return data


def load_yaml(file_path):
    yaml = YAML()
    yaml.preserve_quotes = True
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        data = f.read()
        return yaml.load(data)


def dump_yaml(data, output_file_path):
    yaml = YAML()
    yaml.preserve_quotes = True
    with open(output_file_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f)


def strip_anchor(node):
    if hasattr(node, "anchor"):
        node.anchor.value = None
    return node


def update_yaml_from_wrapped_data(wrapped_node_dict, target_file_path, output_file_path):
    target_data = load_yaml(target_file_path)

    updates_made = []

    def recursive_update(wrapped, target, updates_made: list):
        if isinstance(wrapped, dict) and isinstance(target, dict):
            for key, wrapped_value in wrapped.items():
                if key not in target:
                    continue
                if isinstance(wrapped_value, WrappedNode):
                    if wrapped_value.value != target[key]:
                        target[key] = wrapped_value.value
                        updates_made.append(wrapped_value.path)
                else:
                    recursive_update(wrapped_value, target[key], updates_made)
        elif isinstance(wrapped, list) and isinstance(target, list):
            for i, item in enumerate(wrapped):
                if i < len(target):
                    if isinstance(item, WrappedNode) and item.value != target[i]:
                        target[i] = item.value
                        updates_made.append(item.path)
                    else:
                        recursive_update(item, target[i], updates_made)


        else:
            if not isinstance(wrapped, WrappedNode):
                logger.warning(f"newtype: {type(wrapped)}")

    recursive_update(wrapped_node_dict, target_data)

    dump_yaml(target_data, output_file_path)

    logging.info(f"Update complete. {len(updates_made)} keys updated.")
    return updates_made
