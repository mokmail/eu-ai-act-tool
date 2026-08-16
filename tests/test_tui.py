"""Headless smoke test for the TUI using Textual's pilot API."""
import pytest
from textual.pilot import Pilot

from eu_ai_act.tui import EUAIActApp


@pytest.mark.asyncio
async def test_tui_launches_and_has_menu():
    app = EUAIActApp()
    async with app.run_test() as pilot:
        # Home screen should be showing with the menu
        assert app.screen is not None
        # Navigate: press down then enter to select "Articles"
        await pilot.press("down")
        await pilot.press("enter")
        # Should now be on the ArticleListScreen
        assert "ArticleListScreen" in type(app.screen).__name__
        await pilot.pause()


@pytest.mark.asyncio
async def test_tui_search_screen():
    app = EUAIActApp()
    async with app.run_test() as pilot:
        # Go to search (first menu item)
        await pilot.press("enter")
        assert "SearchScreen" in type(app.screen).__name__
        # Type a query and submit
        await pilot.press("h", "u", "m", "a", "n")
        await pilot.press("enter")
        await pilot.pause()
        # Should have results
        assert app.screen is not None


@pytest.mark.asyncio
async def test_tui_markdown_screens_render():
    """All Markdown-based detail screens must render without crashing."""
    from eu_ai_act.tui import (
        ActorDetailScreen,
        ChecklistDetailScreen,
        CitationScreen,
        CrossrefsScreen,
        DefinitionsScreen,
        GovernanceScreen,
        PenaltiesScreen,
        TierDetailScreen,
        TimelineScreen,
    )

    screens = [
        ChecklistDetailScreen("provider"),
        TimelineScreen(),
        PenaltiesScreen(),
        TierDetailScreen("high_risk"),
        TierDetailScreen("prohibited"),
        ActorDetailScreen("provider"),
        DefinitionsScreen(),
        GovernanceScreen(),
        CrossrefsScreen(),
        CitationScreen(),
    ]
    app = EUAIActApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        for screen in screens:
            app.push_screen(screen)
            await pilot.pause()
            assert app.screen is not None
