# File: cortexfeed/knowledge/graph/v2/graph_builder_v2.py
from typing import Any

from cortexfeed.knowledge.models import (
    Graph,
    GraphNode,
    GraphEdge,
)

NODE_FILE = "FILE"
NODE_CLASS = "CLASS"
NODE_FUNCTION = "FUNCTION"
NODE_METHOD = "METHOD"
NODE_ROUTE = "ROUTE"
NODE_DECORATOR = "DECORATOR"
NODE_MODULE = "MODULE"
NODE_EXTERNAL_SYMBOL = "EXTERNAL_SYMBOL"

EDGE_DEFINES = "DEFINES"
EDGE_IMPORTS = "IMPORTS"
EDGE_EXPOSES_ROUTE = "EXPOSES_ROUTE"

EDGE_REFERENCES = "REFERENCES"
EDGE_CALLS = "CALLS"
EDGE_INSTANTIATES = "INSTANTIATES"
EDGE_INHERITS = "INHERITS"
EDGE_DECORATED_BY = "DECORATED_BY"
EDGE_DEPENDS_ON = "DEPENDS_ON"


class GraphBuilderV2:
    def __init__(self, symbol_index: dict[str, Any]) -> None:
        self.symbol_index = symbol_index
        self._nodes: dict[str, GraphNode] = {}
        self._edge_keys: set[str] = set()
        self._edges: list[GraphEdge] = []

    def _add_node(self, node_id: str, node_type: str, name: str) -> GraphNode:
        if node_id not in self._nodes:
            self._nodes[node_id] = GraphNode(id=node_id, type=node_type, name=name)
        return self._nodes[node_id]

    def _add_edge(self, source: str, target: str, relationship: str) -> None:
        key = f"{source}|{relationship}|{target}"
        if key not in self._edge_keys:
            self._edge_keys.add(key)
            self._edges.append(
                GraphEdge(
                    source=source,
                    target=target,
                    relationship=relationship
                )
            )

    def _resolve_target_node(self, name: str) -> GraphNode:
        # Check if the target is already defined as a function, method, or class
        func_id = f"function:{name}"
        if func_id in self._nodes:
            return self._nodes[func_id]
            
        method_id = f"method:{name}"
        if method_id in self._nodes:
            return self._nodes[method_id]
            
        class_id = f"class:{name}"
        if class_id in self._nodes:
            return self._nodes[class_id]

        # Fallback to external symbol
        symbol_id = f"symbol:{name}"
        return self._add_node(symbol_id, NODE_EXTERNAL_SYMBOL, name)

    def build(self) -> Graph:
        files = self.symbol_index.get("files", [])

        # Pass 1: Build structural nodes (Files, Classes, Functions, Methods, Routes)
        for file_data in files:
            file_path = file_data.get("file_path", "")
            file_node_id = f"file:{file_path}"
            self._add_node(file_node_id, NODE_FILE, file_path)

            for cls in file_data.get("classes", []):
                cls_name = cls.get("name")
                cls_id = f"class:{cls_name}"
                self._add_node(cls_id, NODE_CLASS, cls_name)
                self._add_edge(file_node_id, cls_id, EDGE_DEFINES)

            for func in file_data.get("functions", []):
                func_name = func.get("name")
                func_id = f"function:{func_name}"
                self._add_node(func_id, NODE_FUNCTION, func_name)
                self._add_edge(file_node_id, func_id, EDGE_DEFINES)
                
                # Link function to decorators
                for dec in func.get("decorators", []):
                    dec_id = f"decorator:{dec}"
                    self._add_node(dec_id, NODE_DECORATOR, dec)
                    self._add_edge(func_id, dec_id, EDGE_DECORATED_BY)

            for method in file_data.get("methods", []):
                method_name = f"{method.get('class_name')}.{method.get('name')}"
                method_id = f"method:{method_name}"
                self._add_node(method_id, NODE_METHOD, method_name)
                self._add_edge(file_node_id, method_id, EDGE_DEFINES)
                
                # Link method to decorators
                for dec in method.get("decorators", []):
                    dec_id = f"decorator:{dec}"
                    self._add_node(dec_id, NODE_DECORATOR, dec)
                    self._add_edge(method_id, dec_id, EDGE_DECORATED_BY)

            for route in file_data.get("routes", []):
                route_name = f"{route.get('method')}:{route.get('path')}"
                route_id = f"route:{route_name}"
                self._add_node(route_id, NODE_ROUTE, route_name)
                self._add_edge(file_node_id, route_id, EDGE_EXPOSES_ROUTE)

        # Pass 2: Build intelligence relationships
        for file_data in files:
            file_path = file_data.get("file_path", "")
            file_node_id = f"file:{file_path}"

            for imp in file_data.get("imports", []):
                module_name = imp.get("module")
                if module_name:
                    mod_id = f"module:{module_name}"
                    self._add_node(mod_id, NODE_MODULE, module_name)
                    self._add_edge(file_node_id, mod_id, EDGE_IMPORTS)

            for call in file_data.get("calls", []):
                caller = call.get("caller")
                target = call.get("target")
                caller_id = f"function:{caller}" if caller and caller != "<module>" else file_node_id
                
                target_node = self._resolve_target_node(target)
                self._add_edge(caller_id, target_node.id, EDGE_CALLS)

            for ref in file_data.get("references", []):
                symbol = ref.get("symbol")
                sym_id = f"symbol:{symbol}"
                self._add_node(sym_id, NODE_EXTERNAL_SYMBOL, symbol)
                self._add_edge(file_node_id, sym_id, EDGE_REFERENCES)

            for inst in file_data.get("instantiations", []):
                class_name = inst.get("class_name")
                cls_id = f"class:{class_name}"
                self._add_node(cls_id, NODE_CLASS, class_name)
                # Fallback to file scope if instantiation function caller is not strictly known
                self._add_edge(file_node_id, cls_id, EDGE_INSTANTIATES)

            for inh in file_data.get("inherits", []):
                child_name = inh.get("class_name")
                parent_name = inh.get("parent")
                child_id = f"class:{child_name}"
                parent_id = f"class:{parent_name}"
                
                self._add_node(child_id, NODE_CLASS, child_name)
                self._add_node(parent_id, NODE_CLASS, parent_name)
                self._add_edge(child_id, parent_id, EDGE_INHERITS)
                
            for dec in file_data.get("decorators", []):
                dec_name = dec.get("decorator")
                dec_id = f"decorator:{dec_name}"
                self._add_node(dec_id, NODE_DECORATOR, dec_name)
                # General decorator usage tracked to the file
                self._add_edge(file_node_id, dec_id, EDGE_DECORATED_BY)

        return Graph(
            nodes=list(self._nodes.values()),
            edges=self._edges
        )


def build_graph_v2(symbol_index: dict[str, Any]) -> Graph:
    builder = GraphBuilderV2(symbol_index)
    return builder.build()