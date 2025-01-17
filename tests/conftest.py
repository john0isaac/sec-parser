from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from sec_parser.processing_engine.core import Edgar10QParser
from sec_parser.processing_engine.html_tag_parser import HtmlTagParser
from tests.types import ExpectedSection, ParsedDocumentComponents

if TYPE_CHECKING:  # pragma: no cover
    from tests.types import Report


def pytest_addoption(parser):
    parser.addoption(
        "--with-saved-output",
        action="store_true",
        default=False,
        help="Save the output of the tests to files.",
    )
    parser.addoption(
        "--with-verbose-output",
        action="store_true",
        default=False,
        help="Print the output of the tests to the console.",
    )
    parser.addoption(
        "--update",
        action="store_true",
        default=False,
        help="Create missing files. Overwrite files that were previously generated automatically.",
    )


@pytest.fixture(scope="session")
def parse():
    results = {}

    def _get_result(report: Report):
        if report not in results:
            html_text = report.primary_doc_html_path.read_text()

            expected_sections: list[ExpectedSection] | None = None
            if report.expected_top_level_sections_json_path.exists():
                with report.expected_top_level_sections_json_path.open("r") as file:
                    sections = json.load(file)
                    expected_sections = [
                        ExpectedSection(
                            section_type=section["identifier"],
                            character_count=section["character_count"],
                        )
                        for section in sections
                    ]

            root_tags = HtmlTagParser().parse(html_text)

            elements = Edgar10QParser().parse_from_tags(root_tags)

            results[report] = ParsedDocumentComponents(
                report,
                root_tags,
                elements,
                expected_sections=expected_sections,
            )
        return results[report]

    return _get_result
