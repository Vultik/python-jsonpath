import asyncio
import dataclasses
import operator
from typing import Any
from typing import List
from typing import Mapping
from typing import Sequence
from typing import Union

import pytest

from jsonpath import JSONPathEnvironment


@dataclasses.dataclass
class Case:
    description: str
    path: str
    data: Union[Sequence[Any], Mapping[str, Any]]
    want: Union[Sequence[Any], Mapping[str, Any]]


TEST_CASES = [
    Case(
        description="property key that looks like an index",
        path="$[some][0]",
        data={"some": {"0": "thing"}},
        want=["thing"],
    ),
    Case(
        description="slice a mapping",
        path="$.some[0:4]",
        data={"some": {"thing": "else"}},
        want=[],
    ),
    Case(
        description="keys from a mapping",
        path="$.some[~]",
        data={"some": {"thing": "else"}},
        want=["thing"],
    ),
    Case(
        description="keys from a sequence",
        path="$.some.~",
        data={"some": ["thing", "else"]},
        want=[],
    ),
    Case(
        description="match key pattern",
        path="$.some[?match(#, 'thing[0-9]+')]",
        data={
            "some": {
                "thing1": {"foo": 1},
                "thing2": {"foo": 2},
                "other": {"foo": 3},
            }
        },
        want=[{"foo": 1}, {"foo": 2}],
    ),
    Case(
        description="select root value using fake root",
        path="^[?@some.thing > 7]",
        data={"some": {"thing": 42}},
        want=[{"some": {"thing": 42}}],
    ),
    Case(
        description="fake root in a filter query",
        path="^[?@some.thing > value(^.*.num)]",
        data={"some": {"thing": 42}, "num": 7},
        want=[{"some": {"thing": 42}, "num": 7}],
    ),
    Case(
        description="recurse object keys",
        path="$..~",
        data={"some": {"thing": "else", "foo": {"bar": "baz"}}},
        want=["some", "thing", "foo", "bar"],
    ),
    Case(
        description="logical expr existence tests",
        path="$[?@.a && @.b]",
        data=[{"a": True, "b": False}],
        want=[{"a": True, "b": False}],
    ),
    Case(
        description="logical expr existence tests, alternate and",
        path="$[?@.a and @.b]",
        data=[{"a": True, "b": False}],
        want=[{"a": True, "b": False}],
    ),
]


@pytest.fixture()
def env() -> JSONPathEnvironment:
    return JSONPathEnvironment()


@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("description"))
def test_find(env: JSONPathEnvironment, case: Case) -> None:
    path = env.compile(case.path)
    assert path.findall(case.data) == case.want


@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("description"))
def test_find_async(env: JSONPathEnvironment, case: Case) -> None:
    path = env.compile(case.path)

    async def coro() -> List[object]:
        return await path.findall_async(case.data)

    assert asyncio.run(coro()) == case.want
