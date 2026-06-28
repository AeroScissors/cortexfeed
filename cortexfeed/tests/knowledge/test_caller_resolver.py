# File: cortexfeed/tests/knowledge/test_caller_resolver.py

from pathlib import Path

from cortexfeed.knowledge.graph.v3.call_graph import (
    CallGraphBuilder,
)
from cortexfeed.knowledge.graph.v3.call_models import (
    CallRelationship,
)
from cortexfeed.knowledge.graph.v3.models import (
    EdgeType,
)
from cortexfeed.knowledge.graph.v3.resolvers.caller_resolver import (
    CallerResolver,
)


def test_resolve_returns_list() -> None:
    resolver = CallerResolver()

    relationships = resolver.resolve(
        project_root=Path("."),
        symbol_index={},
        import_index={},
    )

    assert isinstance(relationships, list)


def test_resolve_returns_call_relationships() -> None:
    resolver = CallerResolver()

    relationships = resolver.resolve(
        project_root=Path("."),
        symbol_index={},
        import_index={},
    )

    assert all(
        isinstance(
            relationship,
            CallRelationship,
        )
        for relationship in relationships
    )


def test_same_file_method_call_expected_shape() -> None:
    """
    Future target:

    class A:
        def a(self):
            self.b()

        def b(self):
            pass

    Expected:

    A.a
      ↓
    A.b
    """

    expected = CallRelationship(
        caller_symbol="A.a",
        callee_symbol="A.b",
        caller_file="example.py",
        callee_file="example.py",
        line_number=3,
    )

    assert expected.caller_symbol == "A.a"
    assert expected.callee_symbol == "A.b"


def test_cross_file_call_expected_shape() -> None:
    """
    Future target:

    Controller.login
      ↓
    Service.login
    """

    expected = CallRelationship(
        caller_symbol="Controller.login",
        callee_symbol="Service.login",
        caller_file="controller.py",
        callee_file="service.py",
        line_number=5,
    )

    assert expected.caller_symbol == "Controller.login"
    assert expected.callee_symbol == "Service.login"


def test_multi_hop_call_chain_expected_shape() -> None:
    """
    Future target:

    Controller.login
      ↓
    AuthService.login
      ↓
    UserRepository.find_user
    """

    relationships = [
        CallRelationship(
            caller_symbol="Controller.login",
            callee_symbol="AuthService.login",
            caller_file="controller.py",
            callee_file="auth_service.py",
            line_number=5,
        ),
        CallRelationship(
            caller_symbol="AuthService.login",
            callee_symbol="UserRepository.find_user",
            caller_file="auth_service.py",
            callee_file="repository.py",
            line_number=12,
        ),
    ]

    assert len(relationships) == 2

    assert relationships[0].caller_symbol == "Controller.login"
    assert relationships[0].callee_symbol == "AuthService.login"

    assert relationships[1].caller_symbol == "AuthService.login"
    assert relationships[1].callee_symbol == "UserRepository.find_user"


def test_python_same_file_resolution(tmp_path):
    source = """
class A:
    def a(self):
        self.b()

    def b(self):
        pass
"""

    file_path = tmp_path / "example.py"
    file_path.write_text(source)

    resolver = CallerResolver()

    from cortexfeed.knowledge.indexing.symbol_index import (
        build_symbol_index,
    )

    symbol_index = build_symbol_index(
        tmp_path,
    )

    relationships = resolver.resolve(
        project_root=tmp_path,
        symbol_index=symbol_index,
        import_index={},
    )

    assert len(relationships) == 1

    relationship = relationships[0]

    assert relationship.caller_symbol == "A.a"
    assert relationship.callee_symbol == "A.b"


def test_python_multi_method_chain(tmp_path):
    source = """
class Controller:
    def login(self):
        self.validate()

    def validate(self):
        self.save()

    def save(self):
        pass
"""

    file_path = tmp_path / "controller.py"
    file_path.write_text(source)

    resolver = CallerResolver()

    from cortexfeed.knowledge.indexing.symbol_index import (
        build_symbol_index,
    )

    symbol_index = build_symbol_index(
        tmp_path,
    )

    relationships = resolver.resolve(
        project_root=tmp_path,
        symbol_index=symbol_index,
        import_index={},
    )

    pairs = {
        (
            r.caller_symbol,
            r.callee_symbol,
        )
        for r in relationships
    }

    assert (
        "Controller.login",
        "Controller.validate",
    ) in pairs

    assert (
        "Controller.validate",
        "Controller.save",
    ) in pairs


def test_call_relationship_to_graph_edge() -> None:
    relationship = CallRelationship(
        caller_symbol="Controller.login",
        callee_symbol="AuthService.login",
        caller_file="controller.py",
        callee_file="service.py",
        line_number=10,
    )

    builder = CallGraphBuilder()

    edges = builder.build(
        [relationship],
    )

    assert len(edges) == 1

    edge = edges[0]

    assert edge.source == "Controller.login"
    assert edge.target == "AuthService.login"
    assert edge.edge_type == EdgeType.CALLS


def test_cross_file_service_call(tmp_path):
    controller = """
from service import Service

class Controller:
    def login(self):
        Service().login()
"""

    service = """
class Service:
    def login(self):
        pass
"""

    (tmp_path / "controller.py").write_text(controller)
    (tmp_path / "service.py").write_text(service)

    from cortexfeed.knowledge.indexing.symbol_index import (
        build_symbol_index,
    )

    symbol_index = build_symbol_index(
        tmp_path,
    )

    resolver = CallerResolver()

    relationships = resolver.resolve(
        project_root=tmp_path,
        symbol_index=symbol_index,
        import_index={},
    )

    pairs = {
        (r.caller_symbol, r.callee_symbol)
        for r in relationships
    }

    assert (
        "Controller.login",
        "Service.login",
    ) in pairs


def test_variable_based_service_call(tmp_path):
    source = """
class Service:
    def login(self):
        pass

class Controller:
    def login(self):
        service = Service()
        service.login()
"""

    (tmp_path / "example.py").write_text(source)

    from cortexfeed.knowledge.indexing.symbol_index import (
        build_symbol_index,
    )

    symbol_index = build_symbol_index(
        tmp_path,
    )

    resolver = CallerResolver()

    relationships = resolver.resolve(
        project_root=tmp_path,
        symbol_index=symbol_index,
        import_index={},
    )

    pairs = {
        (r.caller_symbol, r.callee_symbol)
        for r in relationships
    }

    assert (
        "Controller.login",
        "Service.login",
    ) in pairs


def test_imported_service_variable_call(tmp_path):
    controller = """
from service import Service

class Controller:
    def login(self):
        service = Service()
        service.login()
"""

    service = """
class Service:
    def login(self):
        pass
"""

    (tmp_path / "controller.py").write_text(controller)
    (tmp_path / "service.py").write_text(service)

    from cortexfeed.knowledge.indexing.symbol_index import (
        build_symbol_index,
    )

    symbol_index = build_symbol_index(
        tmp_path,
    )

    resolver = CallerResolver()

    relationships = resolver.resolve(
        project_root=tmp_path,
        symbol_index=symbol_index,
        import_index={},
    )

    pairs = {
        (r.caller_symbol, r.callee_symbol)
        for r in relationships
    }

    assert (
        "Controller.login",
        "Service.login",
    ) in pairs


def test_cross_file_callee_file_resolution(tmp_path):
    controller = """
from service import Service

class Controller:
    def login(self):
        service = Service()
        service.login()
"""

    service = """
class Service:
    def login(self):
        pass
"""

    (tmp_path / "controller.py").write_text(controller)
    (tmp_path / "service.py").write_text(service)

    from cortexfeed.knowledge.indexing.symbol_index import (
        build_symbol_index,
    )

    symbol_index = build_symbol_index(
        tmp_path,
    )

    resolver = CallerResolver()

    relationships = resolver.resolve(
        project_root=tmp_path,
        symbol_index=symbol_index,
        import_index={},
    )

    relationship = next(
        (
            r
            for r in relationships
            if r.caller_symbol == "Controller.login"
            and r.callee_symbol == "Service.login"
        ),
        None,
    )

    assert relationship is not None

    assert relationship.callee_file == "service.py"