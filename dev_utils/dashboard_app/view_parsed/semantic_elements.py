from __future__ import annotations

import json
import random
import string
from enum import Enum, auto

import streamlit as st

import sec_parser as sp
from dev_utils.dashboard_app.view_parsed._utils import NoContext

PAGINATION_OFF = "off"
LARGE_TABLE_ROWS_THRESHOLD = 7


class ShowSkippedElements(Enum):
    HIDE = auto()
    MINIMAL = auto()
    SHOW = auto()

    @classmethod
    def get_items(cls):
        return ["hide", "minimal", "show"]

    @classmethod
    def from_value(cls, value):
        return ShowSkippedElements(1 + cls.get_items().index(value))


def render_view_parsed_semantic_elements(
    elements: list[sp.AbstractSemanticElement | sp.TreeNode] | sp.SemanticTree,
    do_show_nested_composite_elements: bool,
):
    with st.sidebar:
        do_open_all_expanders = st.checkbox(
            "Open All Expanders",
        )

        i = -1
        columns = st.columns(1 + int(not do_show_nested_composite_elements))

        if not do_show_nested_composite_elements:
            i += 1
            with columns[i]:
                show_skipped_elements_option = ShowSkippedElements.from_value(
                    st.select_slider(
                        "Visibility of Filtered",
                        ShowSkippedElements.get_items(),
                        value=ShowSkippedElements.get_items()[1],
                        help="This option determines the visibility of elements that have been filtered out.",
                    ),
                )
        else:
            show_skipped_elements_option = ShowSkippedElements.SHOW

        i += 1
        with columns[i]:
            pagination_size = st.select_slider(
                "Set Page Size",
                [10, 20, 30, 50, 100, 200, 300, 500, PAGINATION_OFF],
                value=30,
                help=(
                    "Set the number of elements displayed per page. "
                    "Use this to improve UI responsiveness. "
                ),
            )

    if show_skipped_elements_option == ShowSkippedElements.HIDE:
        elements = [k for k in elements if not isinstance(k, list)]

    #### PAGINATION START
    if pagination_size != PAGINATION_OFF:
        elements_list = list(elements)
        pagination_size = int(pagination_size)
        total_items = len(elements_list)
        max_value = ((total_items // pagination_size) + 1) if pagination_size else 1
        selected_page = 1
        if max_value == 1:
            st.markdown(
                f"<p style='text-align: center; color: lightgrey;'>Top level elements: {total_items}</p>",
                unsafe_allow_html=True,
            )
        elif max_value > 1:
            cols = st.columns(3)
            with cols[1]:
                label = f"Choose a page (out of {max_value} total pages)"
                selected_page = st.number_input(
                    label,
                    min_value=1,
                    max_value=max_value,
                    value=1,
                    step=1,
                    format="%d",
                )

                start_item = (selected_page - 1) * pagination_size + 1
                end_item = min(selected_page * pagination_size, total_items)
                st.markdown(
                    f"<p style='text-align: center;'>{start_item}-{end_item} / {total_items} items</p>",
                    unsafe_allow_html=True,
                )
        pagination_start_idx = (selected_page - 1) * pagination_size
        pagination_end_idx = selected_page * pagination_size
        if max_value > 1:
            elements = elements_list[pagination_start_idx:pagination_end_idx]
    #### PAGINATION END

    for element in elements:
        render_element(
            element,
            show_skipped_elements_option,
            do_open_all_expanders,
        )


def render_element(
    element: sp.AbstractSemanticElement | sp.TreeNode,
    show_skipped_elements_option,
    do_open_all_expanders,
):
    tree_node = None
    if isinstance(element, sp.TreeNode):
        tree_node = element
        element = element.semantic_element

    is_semantic_tree_node = tree_node is not None and tree_node.children
    is_composite_element = isinstance(element, sp.CompositeSemanticElement)
    is_large_table = (
        isinstance(element, sp.TableElement)
        and element.html_tag.get_approx_table_metrics().rows
        >= LARGE_TABLE_ROWS_THRESHOLD
    )

    if isinstance(element, list):  # skipped elements are put in lists
        skipped_elements_list = element
        if show_skipped_elements_option == ShowSkippedElements.MINIMAL:
            st.markdown(
                f'<div align="center" style="color: lightgrey; margin-bottom: 10px;"><span style="font-style: italic;">(filtered out {len(element)} elements)</span></div>',
                unsafe_allow_html=True,
            )
        if show_skipped_elements_option == ShowSkippedElements.SHOW:
            with st.expander(f"*------------- {len(element)} skipped -------------*"):
                for skipped_element in skipped_elements_list:
                    render_element(
                        skipped_element,
                        show_skipped_elements_option,
                        do_open_all_expanders,
                    )
        return

    box_name = element.__class__.__name__
    if hasattr(element, "level"):
        box_name += f" (Level {element.level})"

    with st.expander(box_name, expanded=do_open_all_expanders):
        tab_names = []
        if is_composite_element:
            tab_names.append("Inner Elements")
        if not is_semantic_tree_node and not is_large_table:
            tab_names.append("Rendered")
        if is_large_table:
            tab_names.extend(("Summary", "Rendered"))
        if is_semantic_tree_node:
            tab_names.append("Children Elements")

        tab_names.extend(("Source code", "Processing Log"))

        if not is_large_table and is_semantic_tree_node:
            st.markdown(
                element.get_source_code(enable_compatibility=True),
                unsafe_allow_html=True,
            )

        i = -1
        tabs = st.tabs(tab_names)

        if is_composite_element:
            i += 1
            with tabs[i]:
                for inner_element in element.inner_elements:
                    render_element(
                        inner_element,
                        show_skipped_elements_option,
                        do_open_all_expanders,
                    )

        if not is_semantic_tree_node and not is_large_table:
            i += 1
            with tabs[i]:
                st.markdown(
                    element.get_source_code(enable_compatibility=True),
                    unsafe_allow_html=True,
                )

        if is_large_table:
            i += 1
            with tabs[i]:
                st.write(element.get_summary())
            i += 1
            with tabs[i]:
                st.markdown(
                    element.get_source_code(enable_compatibility=True),
                    unsafe_allow_html=True,
                )

        if is_semantic_tree_node:
            i += 1
            with tabs[i]:
                for c in tree_node.children:
                    render_element(
                        c,
                        show_skipped_elements_option,
                        do_open_all_expanders,
                    )

        i += 1
        with tabs[i]:
            st.code(element.get_source_code(pretty=True), language="text")

        i += 1
        with tabs[i]:
            output = ""
            processing_log = element.processing_log.get_items()
            for item in processing_log:
                payload: str = ""
                if isinstance(item.payload, dict):
                    obj_json = json.dumps(
                        item.payload,
                        indent=4,
                    )
                    payload = f"Created element {obj_json}"
                else:
                    payload = str(item.payload)
                output += f"{item.origin}: {payload}\n"
            st.code(output, language="text")

        assert i == len(tabs) - 1, "tabs should be exhausted"