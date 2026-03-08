# =============================================================
# Anil Pathak's Agentic Healthcare Assistant
# Capstone Project — Agentic Healthcare Assistant for Medical
#                    Task Automation
# =============================================================
# Submitted by  : Anil Pathak
# Generated with: Claude (Anthropic) AI Coding Assistant
# File          : utils/card_helper.py
# Purpose       : Shared dashboard card renderer.
#                 Renders styled HTML cards with icon, title,
#                 description and a Streamlit navigation button.
#                 Used by Patient and Doctor/Admin dashboards
#                 to maintain consistent card styling.
# =============================================================

import streamlit as st


def render_card(icon: str, title: str, description: str,
                page: str, button_label: str = "Open →",
                bg_color: str = "#e8f4fd",
                border_color: str = "#3498db"):
    """
    Render a single styled navigation card with icon, title,
    description text, and a Streamlit page-link button.

    Args:
        icon         (str): Emoji icon displayed at top of card.
        title        (str): Bold card title.
        description  (str): Short one-line description.
        page         (str): Streamlit page path for st.switch_page().
        button_label (str): Label for the navigation button.
        bg_color     (str): Card background hex colour.
        border_color (str): Card border hex colour.

    Returns:
        None
    """
    st.markdown(f"""
    <div style="
        background-color: {bg_color};
        border: 2px solid {border_color};
        border-radius: 12px;
        padding: 28px 20px 18px 20px;
        text-align: center;
        height: 180px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        margin-bottom: 4px;
    ">
        <div style="font-size: 2.4rem; margin-bottom: 8px;">{icon}</div>
        <div style="font-weight: 700; font-size: 1.05rem;
                    margin-bottom: 6px;">{title}</div>
        <div style="font-size: 0.85rem; color: #555;">{description}</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button(button_label, key=f"card_{page}", width='stretch'):
        st.switch_page(page)
