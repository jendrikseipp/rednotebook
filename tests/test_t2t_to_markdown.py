from rednotebook.util.t2t_to_markdown import convert_to_markdown as c


class TestHeadings:
    def test_levels(self):
        assert c("= Title =") == "# Title"
        assert c("== Title ==") == "## Title"
        assert c("===== Title =====") == "##### Title"

    def test_heading_with_anchor(self):
        assert c("== Clouds ==[clouds]") == "## Clouds"

    def test_markdown_heading_untouched(self):
        assert c("# Already Markdown") == "# Already Markdown"


class TestInlineFormatting:
    def test_italic(self):
        assert c("//italic//") == "*italic*"

    def test_bold_unchanged(self):
        assert c("**bold**") == "**bold**"

    def test_underline(self):
        assert c("__underlined__") == "<u>underlined</u>"

    def test_strikethrough(self):
        assert c("--struck--") == "~~struck~~"

    def test_monospace(self):
        assert c("``code``") == "`code`"

    def test_combination(self):
        assert c("a //b// and **c** and --d--") == "a *b* and **c** and ~~d~~"

    def test_italic_does_not_touch_urls(self):
        assert c("see http://example.com now") == "see http://example.com now"


class TestHorizontalRule:
    def test_long_equals(self):
        assert c("====================") == "---"

    def test_long_dashes(self):
        assert c("--------------------") == "---"

    def test_short_dashes_untouched(self):
        # Three dashes is already a Markdown rule and must survive.
        assert c("---") == "---"


class TestLists:
    def test_bullet_unchanged(self):
        assert c("- item") == "- item"

    def test_numbered(self):
        assert c("+ item") == "1. item"

    def test_indented_numbered(self):
        assert c("  + item") == "  1. item"


class TestLinks:
    def test_named_web_link(self):
        assert c("[heise http://heise.de]") == "[heise](http://heise.de)"

    def test_quoted_link(self):
        assert c('[my file ""file:///home/me/f.txt""]') == "[my file](file:///home/me/f.txt)"

    def test_bare_url_unchanged(self):
        assert c("http://example.com") == "http://example.com"


class TestImages:
    def test_simple_image(self):
        assert c('[""/home/pic"".png]') == "![](/home/pic.png)"

    def test_image_with_width(self):
        assert c('[""/home/pic"".png?50]') == "![](/home/pic.png?50)"

    def test_named_image(self):
        assert c('[alt ""/home/pic"".jpg]') == "![alt](/home/pic.jpg)"


class TestLineBreak:
    def test_trailing_backslashes(self):
        assert c("First\\\\\nSecond") == "First  \nSecond"

    def test_backslashes_midline_unchanged(self):
        assert c("First\\\\Second") == "First\\\\Second"


class TestFencedCodeIsPreserved:
    def test_no_inline_conversion_in_fence(self):
        text = "```\n//not italic//\n+ not numbered\n```"
        assert c(text) == text

    def test_entry_reference_passthrough(self):
        # Entry references are handled later in the pipeline, not here.
        assert c("[2019-08-01]") == "[2019-08-01]"
