import uuid

import pytest

from lib_management.core.errors import ValidationFailed
from lib_management.core.pagination import build_page, decode_cursor, encode_cursor


def test_cursor_round_trip():
    row_id = uuid.uuid4()
    cursor = decode_cursor(encode_cursor(["2026-11-03T00:00:00Z"], row_id))
    assert cursor.k == ["2026-11-03T00:00:00Z"]
    assert cursor.id == row_id


@pytest.mark.parametrize(
    "value", ["", "!!!", "e30", encode_cursor(["a"], uuid.uuid4())[:-3]]
)
def test_malformed_cursor_is_422(value):
    with pytest.raises(ValidationFailed):
        decode_cursor(value)


def test_build_page_sets_next_cursor_only_when_more():
    rows = [(str(i), uuid.uuid4()) for i in range(3)]
    page = build_page(rows, 2, key=lambda row: ([row[0]], row[1]))
    assert page.data == rows[:2]
    assert decode_cursor(page.nextCursor).id == rows[1][1]
    assert (
        build_page(rows[:2], 2, key=lambda row: ([row[0]], row[1])).nextCursor is None
    )
