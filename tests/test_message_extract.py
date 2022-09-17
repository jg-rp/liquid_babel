"""Test cases for translatable message extraction."""
# pylint: disable=missing-class-docstring,missing-function-docstring
import unittest

from liquid import Environment
from liquid import Template

from liquid_babel.filters.translate import register_translation_filters
from liquid_babel.messages.extract import extract_from_template


class ExtractFromTemplateTestCase(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.env = Environment()
        register_translation_filters(self.env)

    def test_no_registered_filters(self) -> None:
        """Test that we don't get messages if translation filters are not registered."""
        source = (
            "{{ 'Hello, World!' }}"
            "{{ 'Hello, World!' | gettext }}"
            "{{ 'Hello, World!' }}"
        )

        template = Template(source)
        messages = list(extract_from_template(template))
        self.assertEqual(len(messages), 0)

    def test_gettext_filter(self) -> None:
        """Test that we can extract messages from the GetText filter."""
        source = (
            "{{ 'Hello, World!' }}\n"
            "{{ 'Hello, World!' | gettext }}\n"
            "{{ 'Hello, World!' }}\n"
        )

        template = self.env.from_string(source)
        messages = list(extract_from_template(template))

        self.assertEqual(len(messages), 1)
        message = messages[0]

        self.assertEqual(message.lineno, 2)
        self.assertEqual(message.funcname, "gettext")
        self.assertEqual(message.message, ("Hello, World!",))
        self.assertEqual(message.comments, [])

    def test_gettext_filter_with_comment(self) -> None:
        """Test that we can extract messages from the GetText filter with comments."""
        source = (
            "{{ 'Hello, World!' }}\n"
            "{% # Translators: greeting %}\n"
            "{{ 'Hello, World!' | gettext }}\n"
            "{{ 'Hello, World!' }}\n"
        )

        template = self.env.from_string(source)
        messages = list(
            extract_from_template(
                template,
                comment_tags=["Translators:"],
            )
        )

        self.assertEqual(len(messages), 1)
        message = messages[0]

        self.assertEqual(message.lineno, 3)
        self.assertEqual(message.funcname, "gettext")
        self.assertEqual(message.message, ("Hello, World!",))
        self.assertEqual(message.comments, ["Translators: greeting"])

    def test_preceding_comments(self) -> None:
        """Test that comments that do no immediately precede a translatable filter
        are excluded."""
        source = (
            "{{ 'Hello, World!' }}\n"
            "{% # Translators: greeting %}\n"
            "\n"
            "{{ 'Hello, World!' | gettext }}\n"
            "{{ 'Hello, World!' }}\n"
        )

        template = self.env.from_string(source)
        messages = list(
            extract_from_template(
                template,
                comment_tags=["Translators:"],
            )
        )

        self.assertEqual(len(messages), 1)
        message = messages[0]

        self.assertEqual(message.lineno, 4)
        self.assertEqual(message.funcname, "gettext")
        self.assertEqual(message.message, ("Hello, World!",))
        self.assertEqual(message.comments, [])

    def test_multiple_preceding_comments(self) -> None:
        """Test that only the last comment is included."""
        source = (
            "{{ 'Hello, World!' }}\n"
            "{% # Translators: hello %}\n"
            "{% # Translators: greeting %}\n"
            "{{ 'Hello, World!' | gettext }}\n"
            "{{ 'Hello, World!' }}\n"
        )

        template = self.env.from_string(source)
        messages = list(
            extract_from_template(
                template,
                comment_tags=["Translators:"],
            )
        )

        self.assertEqual(len(messages), 1)
        message = messages[0]

        self.assertEqual(message.lineno, 4)
        self.assertEqual(message.funcname, "gettext")
        self.assertEqual(message.message, ("Hello, World!",))
        self.assertEqual(message.comments, ["Translators: greeting"])

    def test_comment_with_no_tag(self) -> None:
        """Test that tag-less comments are excluded."""
        source = (
            "{{ 'Hello, World!' }}\n"
            "{% # greeting %}\n"
            "{{ 'Hello, World!' | gettext }}\n"
            "{{ 'Hello, World!' }}\n"
        )

        template = self.env.from_string(source)
        messages = list(
            extract_from_template(
                template,
                comment_tags=["Translators:"],
            )
        )

        self.assertEqual(len(messages), 1)
        message = messages[0]

        self.assertEqual(message.lineno, 3)
        self.assertEqual(message.funcname, "gettext")
        self.assertEqual(message.message, ("Hello, World!",))
        self.assertEqual(message.comments, [])

    def test_gettext_filter_excess_args(self) -> None:
        """Test that the GetText filter handles excess arguments."""
        source = (
            "{{ 'Hello, World!' }}\n"
            "{{ 'Hello, World!' | gettext: 1 }}\n"
            "{{ 'Hello, World!' }}\n"
        )

        template = self.env.from_string(source)
        messages = list(extract_from_template(template))

        self.assertEqual(len(messages), 1)
        message = messages[0]

        self.assertEqual(message.lineno, 2)
        self.assertEqual(message.funcname, "gettext")
        self.assertEqual(message.message, ("Hello, World!",))
        self.assertEqual(message.comments, [])

    def test_ngettext_filter(self) -> None:
        """Test that we can extract messages from the NGetText"""
        source = (
            "{{ 'Hello, World!' }}\n"
            "{{ 'Hello, World!' | ngettext: 'Hello, Worlds!', 2 }}\n"
            "{{ 'Hello, World!' }}\n"
        )

        template = self.env.from_string(source)
        messages = list(extract_from_template(template))

        self.assertEqual(len(messages), 1)
        message = messages[0]

        self.assertEqual(message.lineno, 2)
        self.assertEqual(message.funcname, "ngettext")
        self.assertEqual(message.message, ("Hello, World!", "Hello, Worlds!"))
        self.assertEqual(message.comments, [])

    def test_ngettext_filter_too_few_args(self) -> None:
        """Test that the NGetText handles missing arguments."""
        source = (
            "{{ 'Hello, World!' }}\n"
            "{{ 'Hello, World!' | ngettext }}\n"
            "{{ 'Hello, World!' | ngettext: 'Hello, Worlds!' }}\n"
            "{{ 'Hello, World!' }}\n"
        )

        template = self.env.from_string(source)
        messages = list(extract_from_template(template))

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].message, ("Hello, World!", "Hello, Worlds!"))

    def test_ngettext_filter_too_many_args(self) -> None:
        """Test that the NGetText handles excess arguments."""
        source = (
            "{{ 'Hello, World!' }}\n"
            "{{ 'Hello, World!' | ngettext: 'Hello, Worlds!', 2, foo }}\n"
            "{{ 'Hello, World!' }}\n"
        )

        template = self.env.from_string(source)
        messages = list(extract_from_template(template))

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].message, ("Hello, World!", "Hello, Worlds!"))

    def test_pgettext_filter(self) -> None:
        """Test that we can extract messages from the NGetText."""
        source = (
            "{{ 'Hello, World!' }}\n"
            "{{ 'Hello, World!' | pgettext: 'greeting' }}\n"
            "{{ 'Hello, World!' }}\n"
        )

        template = self.env.from_string(source)
        messages = list(extract_from_template(template))

        self.assertEqual(len(messages), 1)
        message = messages[0]

        self.assertEqual(message.lineno, 2)
        self.assertEqual(message.funcname, "pgettext")
        self.assertEqual(message.message, (("greeting", "c"), "Hello, World!"))
        self.assertEqual(message.comments, [])

    def test_pgettext_filter_too_few_args(self) -> None:
        """Test that the PGetText handles missing arguments."""
        source = (
            "{{ 'Hello, World!' }}\n"
            "{{ 'Hello, World!' | pgettext }}\n"
            "{{ 'Hello, World!' }}\n"
        )

        template = self.env.from_string(source)
        messages = list(extract_from_template(template))
        self.assertEqual(len(messages), 0)

    def test_npgettext_filter(self) -> None:
        """Test that we can extract messages from the NPGetText"""
        source = (
            "{{ 'Hello, World!' }}\n"
            "{{ 'Hello, World!' | npgettext: 'greeting', 'Hello, Worlds!', 2 }}\n"
            "{{ 'Hello, World!' }}\n"
        )

        template = self.env.from_string(source)
        messages = list(extract_from_template(template))

        self.assertEqual(len(messages), 1)
        message = messages[0]

        self.assertEqual(message.lineno, 2)
        self.assertEqual(message.funcname, "npgettext")
        self.assertEqual(
            message.message, (("greeting", "c"), "Hello, World!", "Hello, Worlds!")
        )
        self.assertEqual(message.comments, [])

    def test_npgettext_filter_too_few_args(self) -> None:
        """Test that the NPGetText handles missing arguments."""
        source = (
            "{{ 'Hello, World!' }}\n"
            "{{ 'Hello, World!' | npgettext }}\n"
            "{{ 'Hello, World!' | npgettext: 'greeting' }}\n"
            "{{ 'Hello, World!' }}\n"
        )

        template = self.env.from_string(source)
        messages = list(extract_from_template(template))
        self.assertEqual(len(messages), 0)

    def test_t_filter_gettext(self) -> None:
        """Test that the `t` filter can behave like gettext."""
        source = (
            "{{ 'Hello, World!' }}\n"
            "{{ 'Hello, World!' | t }}\n"
            "{{ 'Hello, World!' }}\n"
        )

        template = self.env.from_string(source)
        messages = list(extract_from_template(template))

        self.assertEqual(len(messages), 1)
        message = messages[0]

        self.assertEqual(message.lineno, 2)
        self.assertEqual(message.funcname, "gettext")
        self.assertEqual(message.message, ("Hello, World!",))
        self.assertEqual(message.comments, [])

    def test_t_filter_ngettext(self) -> None:
        """Test that the `t` filter can behave like ngettext."""
        source = (
            "{{ 'Hello, World!' }}\n"
            "{{ 'Hello, World!' | t: plural: 'Hello, Worlds!' }}\n"
            "{{ 'Hello, World!' }}\n"
        )

        template = self.env.from_string(source)
        messages = list(extract_from_template(template))

        self.assertEqual(len(messages), 1)
        message = messages[0]

        self.assertEqual(message.lineno, 2)
        self.assertEqual(message.funcname, "ngettext")
        self.assertEqual(message.message, ("Hello, World!", "Hello, Worlds!"))
        self.assertEqual(message.comments, [])

    def test_t_filter_pgettext(self) -> None:
        """Test that the `t` filter can behave like pgettext."""
        source = (
            "{{ 'Hello, World!' }}\n"
            "{{ 'Hello, World!' | t: context: 'greeting' }}\n"
            "{{ 'Hello, World!' }}\n"
        )

        template = self.env.from_string(source)
        messages = list(extract_from_template(template))

        self.assertEqual(len(messages), 1)
        message = messages[0]

        self.assertEqual(message.lineno, 2)
        self.assertEqual(message.funcname, "pgettext")
        self.assertEqual(message.message, (("greeting", "c"), "Hello, World!"))
        self.assertEqual(message.comments, [])

    def test_t_filter_npgettext(self) -> None:
        """Test that the `t` filter can behave like npgettext."""
        source = (
            "{{ 'Hello, World!' }}\n"
            "{{ 'Hello, World!' | t: context: 'greeting', plural: 'Hello, Worlds!' }}\n"
            "{{ 'Hello, World!' }}\n"
        )

        template = self.env.from_string(source)
        messages = list(extract_from_template(template))

        self.assertEqual(len(messages), 1)
        message = messages[0]

        self.assertEqual(message.lineno, 2)
        self.assertEqual(message.funcname, "npgettext")
        self.assertEqual(
            message.message, (("greeting", "c"), "Hello, World!", "Hello, Worlds!")
        )
        self.assertEqual(message.comments, [])