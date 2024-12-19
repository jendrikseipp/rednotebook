import logging
import re

import gi


gi.require_version("Pango", "1.0")

from gi.repository import GObject, Pango

from rednotebook.external import txt2tags
from rednotebook.util.markup import REGEX_HTML_LINK, REGEX_LINEBREAK


def convert_to_pango(txt, headers=None, options=None):
    """
    Code partly taken from txt2tags tarball
    """
    original_txt = txt

    # Here is the marked body text, it must be a list.
    txt = txt.split("\n")

    # Set the three header fields
    if headers is None:
        headers = ["", "", ""]

    config = txt2tags.ConfigMaster()._get_defaults()

    config["outfile"] = txt2tags.MODULEOUT  # results as list
    config["target"] = "html"

    config["preproc"] = []
    # We need to escape the ampersand here, otherwise "&amp;" would become
    # "&amp;amp;"
    config["preproc"].append([r"&amp;", "&"])

    # Allow line breaks
    config["postproc"] = []
    config["postproc"].append([REGEX_LINEBREAK, "\n"])

    if options is not None:
        config.update(options)

    # Let's do the conversion
    try:
        body, toc = txt2tags.convert(txt, config)
        full_doc = body
        finished = txt2tags.finish_him(full_doc, config)
        result = "".join(finished)

    # Txt2tags error, show the message to the user
    except txt2tags.error as msg:
        logging.error(msg)
        result = msg

    # Unknown error, show the traceback to the user
    except Exception:
        result = txt2tags.getUnknownErrorMessage()
        logging.error(result)

    print(result)

    # remove unwanted paragraphs
    result = result.replace('<div class="body"><p>', "").replace("</p></div>", "")

    logging.log(
        5,
        f'Converted "{repr(original_txt)}" text to "{repr(result)}" txt2tags markup',
    )

    # Remove unknown tags (<a>)
    def replace_links(match):
        """Return the link name."""
        return match.group(1)

    result = re.sub(REGEX_HTML_LINK, replace_links, result)
    print(result)

    for new_tag, old_tag in [("del", "s"), ("em", "i"), ("strong", "b")]:
        result = result.replace(f"<{new_tag}>", f"<{old_tag}>")
        result = result.replace(f"</{new_tag}>", f"</{old_tag}>")
    print(result)

    try:
        Pango.parse_markup(result, -1, "0")
        # result is valid pango markup, return the markup.
        return result
    except GObject.GError:
        # There are unknown tags in the markup, return the original text
        logging.debug(f"There are unknown tags in the markup: {result}")
        return original_txt


def convert_from_pango(pango_markup):
    original_txt = pango_markup
    replacements = {
        "<b>": "**",
        "</b>": "**",
        "<i>": "//",
        "</i>": "//",
        "<s>": "--",
        "</s>": "--",
        "<u>": "__",
        "</u>": "__",
        "&amp;": "&",
        "&lt;": "<",
        "&gt;": ">",
        "\n": r"\\",
    }
    for orig, repl in replacements.items():
        pango_markup = pango_markup.replace(orig, repl)

    logging.log(
        5,
        f'Converted "{repr(original_txt)}" pango to "{repr(pango_markup)}" txt2tags',
    )
    return pango_markup
