# File: cortexfeed/tests/knowledge/v2/test_symbol_index_v2.py

from pathlib import Path

from cortexfeed.knowledge.indexing.v2.symbol_index_v2 import (
    build_symbol_index_v2,
)


def test_extracts_classes_functions_methods_and_imports(
    tmp_path: Path,
) -> None:
    source = '''
import os
from pathlib import Path


class UserService:
    def create_user(self):
        return True


def helper():
    return UserService()
'''

    (tmp_path / "service.py").write_text(
        source,
        encoding="utf-8",
    )

    index = build_symbol_index_v2(tmp_path)

    assert index["project"] == tmp_path.name
    assert len(index["files"]) == 1

    file_data = index["files"][0]

    assert file_data["file_path"] == "service.py"

    assert any(
        cls["name"] == "UserService"
        for cls in file_data["classes"]
    )

    assert any(
        fn["name"] == "helper"
        for fn in file_data["functions"]
    )

    assert any(
        method["name"] == "create_user"
        for method in file_data["methods"]
    )

    assert any(
        imp["module"] == "os"
        for imp in file_data["imports"]
    )

    assert any(
        imp["module"] == "pathlib"
        and imp["imported"] == "Path"
        for imp in file_data["imports"]
    )


def test_extracts_route_decorators(
    tmp_path: Path,
) -> None:
    source = '''
class Router:
    def get(self, path):
        pass


router = Router()


@router.get("/users")
def get_users():
    return []
'''

    (tmp_path / "routes.py").write_text(
        source,
        encoding="utf-8",
    )

    index = build_symbol_index_v2(tmp_path)

    file_data = index["files"][0]

    assert len(file_data["routes"]) == 1

    route = file_data["routes"][0]

    assert route["path"] == "/users"
    assert route["method"] == "GET"
    assert route["function_name"] == "get_users"


def test_extracts_inheritance_relationships(
    tmp_path: Path,
) -> None:
    source = '''
class UserService:
    pass


class AdminService(UserService):
    pass
'''

    (tmp_path / "inheritance.py").write_text(
        source,
        encoding="utf-8",
    )

    index = build_symbol_index_v2(tmp_path)

    file_data = index["files"][0]

    assert len(file_data["inherits"]) == 1

    relation = file_data["inherits"][0]

    assert relation["class_name"] == "AdminService"
    assert relation["parent"] == "UserService"


def test_extracts_function_calls(
    tmp_path: Path,
) -> None:
    source = '''
def create_user():
    return True


def controller():
    create_user()
'''

    (tmp_path / "calls.py").write_text(
        source,
        encoding="utf-8",
    )

    index = build_symbol_index_v2(tmp_path)

    file_data = index["files"][0]

    calls = file_data["calls"]

    assert any(
        call["caller"] == "controller"
        and call["target"] == "create_user"
        for call in calls
    )


def test_extracts_instantiations(
    tmp_path: Path,
) -> None:
    source = '''
class UserService:
    pass


def build():
    service = UserService()
    return service
'''

    (tmp_path / "instantiation.py").write_text(
        source,
        encoding="utf-8",
    )

    index = build_symbol_index_v2(tmp_path)

    file_data = index["files"][0]

    assert any(
        item["class_name"] == "UserService"
        for item in file_data["instantiations"]
    )


def test_extracts_attribute_access(
    tmp_path: Path,
) -> None:
    source = '''
class User:
    pass


def process(user):
    return user.name
'''

    (tmp_path / "attributes.py").write_text(
        source,
        encoding="utf-8",
    )

    index = build_symbol_index_v2(tmp_path)

    file_data = index["files"][0]

    assert any(
        attr["object_name"] == "user"
        and attr["attribute"] == "name"
        for attr in file_data["attributes"]
    )


def test_extracts_symbol_references(
    tmp_path: Path,
) -> None:
    source = '''
value = 10

def compute():
    return value
'''

    (tmp_path / "references.py").write_text(
        source,
        encoding="utf-8",
    )

    index = build_symbol_index_v2(tmp_path)

    file_data = index["files"][0]

    symbols = {
        ref["symbol"]
        for ref in file_data["references"]
    }

    assert "value" in symbols


def test_skips_invalid_python_files(
    tmp_path: Path,
) -> None:
    (tmp_path / "broken.py").write_text(
        "def broken(",
        encoding="utf-8",
    )

    index = build_symbol_index_v2(tmp_path)

    assert index["project"] == tmp_path.name
    assert index["files"] == []