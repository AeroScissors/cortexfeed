# File: cortexfeed/tests/knowledge/test_path_finder.py

from cortexfeed.knowledge.graph.v3.traversal.path_finder import (
    PathFinder,
)


def test_shortest_path_multi_hop():
    adjacency = {
        "Controller.login": [
            "AuthService.login",
        ],
        "AuthService.login": [
            "UserRepository.find_user",
        ],
        "UserRepository.find_user": [],
    }

    finder = PathFinder()

    path = finder.shortest_path(
        adjacency=adjacency,
        start="Controller.login",
        target="UserRepository.find_user",
    )

    assert path == [
        "Controller.login",
        "AuthService.login",
        "UserRepository.find_user",
    ]