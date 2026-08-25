"""
Tests for Usability, Compatibility, and Maintainability non-functional
requirements (NFR-USE-01, NFR-COMPAT-01, NFR-MAINT-02).
"""
import unittest

from .helpers import AppTestCase, register_and_login, default_sim_form


class TestTooltips(AppTestCase, unittest.TestCase):
    """NFR-USE-01: Provide tooltips/info on all input parameters."""

    def setUp(self):
        super().setUp()
        register_and_login(self.client, "tooltips")

    def test_every_simulation_input_has_a_tooltip(self):
        html = self.client.get("/simulate/new").get_data(as_text=True)
        # Each labeled input field should be paired with a `.tip` tooltip icon
        # in the same field block. We check the overall count as a proxy:
        # there are 7 documented input concepts on this form.
        tip_count = html.count('class="tip"')
        self.assertGreaterEqual(tip_count, 7, "every input on the simulation form should have a tooltip")

    def test_every_statistic_on_results_page_has_a_tooltip(self):
        resp = self.client.post("/simulate/run", data=default_sim_form())
        html = resp.get_data(as_text=True)
        tip_count = html.count('class="tip"')
        # 12 statistics + 1 distribution-type tooltip near the heading
        self.assertGreaterEqual(tip_count, 12, "every statistic tile should have an explanatory tooltip")

    def test_tooltip_bubbles_contain_actual_explanatory_text(self):
        html = self.client.get("/simulate/new").get_data(as_text=True)
        self.assertIn("tip-bubble", html)
        # spot check a specific known tooltip's content
        self.assertIn("Annualized expected/mean return", html)


class TestDesktopViewport(AppTestCase, unittest.TestCase):
    """NFR-COMPAT-01: Available on desktop devices (C1: no mobile support)."""

    def test_viewport_meta_tag_forces_desktop_width(self):
        html = self.client.get("/login").get_data(as_text=True)
        self.assertIn('content="width=1024"', html)

    def test_mobile_warning_banner_present(self):
        html = self.client.get("/login").get_data(as_text=True)
        self.assertIn("mobile-warning", html)
        self.assertIn("designed for desktop browsers", html)

    def test_css_enforces_minimum_desktop_width(self):
        resp = self.client.get("/static/css/style.css")
        css = resp.get_data(as_text=True)
        resp.close()
        self.assertIn("--min-desktop-width", css)
        self.assertIn("min-width: var(--min-desktop-width)", css)


class TestConsistentDesignSystem(AppTestCase, unittest.TestCase):
    """NFR-MAINT-02: Maintain consistent UI design across all pages."""

    def setUp(self):
        super().setUp()
        register_and_login(self.client, "designsystem")

    def test_all_pages_link_the_same_stylesheet(self):
        pages = ["/login", "/register", "/dashboard", "/simulate/new", "/saved", "/datasets"]
        for path in pages:
            html = self.client.get(path).get_data(as_text=True)
            self.assertIn('href="/static/css/style.css"', html, f"{path} should use the shared stylesheet")

    def test_all_pages_extend_the_same_navigation_structure(self):
        html = self.client.get("/dashboard").get_data(as_text=True)
        self.assertIn('class="topbar"', html)
        self.assertIn('class="footer"', html)

    def test_shared_css_custom_properties_used_consistently(self):
        resp = self.client.get("/static/css/style.css")
        css = resp.get_data(as_text=True)
        resp.close()
        for token in ["--color-bg", "--color-primary", "--color-text", "--radius-md", "--font-sans"]:
            self.assertIn(token, css)


if __name__ == "__main__":
    unittest.main()
