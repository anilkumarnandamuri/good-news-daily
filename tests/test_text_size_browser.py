"""GN-5 typography regression using the repository's own feed."""
from pathlib import Path

try:
    import pytest
except ImportError:
    pytest = None
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts" / "GN-5"

if pytest is not None:
    # Reuse the local http.server fixture without replacing the feed.
    from test_legacy_feed_browser import server

    if sync_playwright is None:
        pytestmark = pytest.mark.skip(reason="playwright is not installed")

    @pytest.mark.parametrize("width,height,mobile", [(384, 832, True), (1280, 900, False)])
    def test_text_size(server, width, height, mobile):
        ARTIFACTS.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context(
                viewport={"width": width, "height": height},
                device_scale_factor=3 if mobile else 1,
                is_mobile=mobile, has_touch=mobile,
                reduced_motion="reduce",
            )
            # Keep local data and assets; isolate optional third-party SDKs.
            context.route("**/*", lambda route: route.continue_()
                          if route.request.url.startswith(server + "/") else route.abort())
            page = context.new_page()
            page.goto(server)
            first = page.locator(".t5-c").first
            first.wait_for()
            page.evaluate("document.fonts.ready")
            assert page.locator("html").evaluate("e => getComputedStyle(e).fontSize") == "16px"
            assert page.locator("body").evaluate("e => getComputedStyle(e).fontSize") == "16px"
            assert page.locator("#textSize").count() == 0
            box = first.bounding_box()
            assert box["height"] <= (320 if mobile else 420)
            if mobile:
                assert box["y"] + box["height"] <= height
                assert page.locator(".top").bounding_box()["height"] <= 90
            for selector in [".t5-c h3", ".card h3"]:
                assert page.locator(selector).first.evaluate("e => getComputedStyle(e).webkitLineClamp") == "3"
            page.screenshot(path=str(ARTIFACTS / f"gn5-landing-{width}.png"))

            def press(selector):
                button = page.locator(selector)
                # A disabled native button ignores additional physical taps.
                if mobile:
                    button.tap(force=True)
                else:
                    button.click(force=True)

            if mobile:
                first.tap()
            else:
                first.click()
            page.wait_for_selector("#reader.show")
            paragraph = page.locator(".r-sum p").first
            font_size = lambda: paragraph.evaluate("e => parseFloat(getComputedStyle(e).fontSize)")
            original = font_size()
            if mobile:
                assert paragraph.bounding_box()["y"] < 832
                paragraph.scroll_into_view_if_needed()
                page.screenshot(path=str(ARTIFACTS / "gn5-reader-384.png"))
            press("#rLg")
            assert font_size() > original
            assert page.get_by_role("status").last.inner_text() == "Text size 115%"
            if mobile:
                paragraph.scroll_into_view_if_needed()
                page.screenshot(path=str(ARTIFACTS / "gn5-reader-Aplus-384.png"))
            press("#rSm")
            press("#rSm")
            smaller = font_size()
            assert smaller < original
            story_hash = page.evaluate("location.hash")
            page.reload()
            page.wait_for_selector("#reader.show")
            assert page.evaluate("location.hash") == story_hash
            assert font_size() == smaller
            assert page.evaluate("JSON.parse(localStorage.getItem('gn_textScale'))") == .85
            for _ in range(10):
                press("#rLg")
            assert page.locator("#rLg").is_disabled()
            assert page.locator("#rLg").get_attribute("aria-disabled") == "true"
            assert page.evaluate("GN.textScale.get()") == 1.6
            assert abs(font_size() - original * 1.6) < .02
            for _ in range(10):
                press("#rSm")
            assert page.locator("#rSm").is_disabled()
            assert page.locator("#rSm").get_attribute("aria-disabled") == "true"
            assert page.evaluate("GN.textScale.get()") == .85
            assert abs(font_size() - original * .85) < .02
            browser.close()


    @pytest.mark.parametrize("category", ["all", "science", "health"])
    def test_max_text_scale_card_containment(server, category):
        ARTIFACTS.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context(
                viewport={"width": 384, "height": 832},
                device_scale_factor=3, is_mobile=True, has_touch=True,
                reduced_motion="reduce",
            )
            context.route("**/*", lambda route: route.continue_()
                          if route.request.url.startswith(server + "/") else route.abort())
            context.add_init_script("localStorage.setItem('gn_textScale', '1.6')")
            page = context.new_page()
            page.goto(f"{server}/?cat={category}")
            # All renders Today's 5; category views render a lead hero.
            card = page.locator(".t5-c" if category == "all" else ".hero").first
            card.wait_for()
            page.evaluate("document.fonts.ready")
            assert page.evaluate("GN.textScale.get()") == 1.6
            card_box = card.bounding_box()
            body_box = card.locator(".body").bounding_box()
            heading = card.locator("h2, h3")
            heading_box = heading.bounding_box()
            for box in (body_box, heading_box):
                assert box["y"] >= card_box["y"] - 1
                assert box["y"] + box["height"] <= card_box["y"] + card_box["height"] + 1
                assert box["x"] >= card_box["x"] - 1
                assert box["x"] + box["width"] <= card_box["x"] + card_box["width"] + 1
            assert heading.evaluate("e => getComputedStyle(e).webkitLineClamp") == "3"
            if category != "all":
                assert card.locator("p").evaluate("e => getComputedStyle(e).webkitLineClamp") == "2"
            page.screenshot(path=str(ARTIFACTS / f"gn5-max-scale-{category}-384.png"), full_page=True)
            browser.close()
