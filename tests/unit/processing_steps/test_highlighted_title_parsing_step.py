import pytest

from sec_parser.processing_steps.highlighted_text_parsing_step import (
    HighlightedTextParsingStep,
)
from sec_parser.processing_steps.title_parsing_step import TitleParsingStep
from sec_parser.semantic_elements.semantic_elements import (
    TitleElement,
    UndeterminedElement,
)
from tests.unit.processing_steps._utils import assert_elements, get_elements_from_html


@pytest.mark.parametrize(
    ("html_str", "expected_elements"),
    [
        (  # From Apple 10-Q
            """
                <div style="margin-top:18pt;text-align:justify">
                    <span style="color:#000000;font-family:'Helvetica',sans-serif;font-size:9pt;font-weight:700;line-height:120%">
                        Available Information
                    </span>
                </div>
                <div style="margin-top:6pt;text-align:justify">
                    <span style="color:#000000;font-family:'Helvetica',sans-serif;font-size:9pt;font-weight:400;line-height:120%">
                        The Company periodically provides certain information for investors on its corporate website
                    </span>
                </div>
            """,
            [
                {"type": TitleElement, "tag": "div"},
                {"type": UndeterminedElement, "tag": "div"},
            ],
        ),
    ],
)
def test_title_step(html_str, expected_elements):
    """
    This test checks that the HighlightedTextParsingStep and TitleParsingStep
    can successfully transform a list of semantic elements returned by
    `get_elements_from_html`. These elements can be of type
    `UndeterminedElement` or `SpecialElement`.
    """
    # Arrange
    elements = get_elements_from_html(html_str)

    highlighter_step = HighlightedTextParsingStep()
    title_step = TitleParsingStep()

    # Act
    elements = highlighter_step.process(elements)
    elements = title_step.process(elements)

    # Assert
    assert_elements(elements, expected_elements)
    # Assert
    assert_elements(elements, expected_elements)