"""Test attribute selectors."""
from .. import util
import os
import subprocess
import sys
import soupsieve as sv


class TestAttribute(util.TestCase):
    """Test attribute selectors."""

    # Seconds a malformed selector is given to fail before it is treated as a hang.
    # A pattern that can catastrophically backtrack takes exponentially longer than this.
    COMPILE_TIMEOUT = 30

    MARKUP = """
    <div id="div">
    <p id="0">Some text <span id="1"> in a paragraph</span>.</p>
    <a id="2" href="http://google.com">Link</a>
    <span id="3">Direct child</span>
    <pre id="pre">
    <span id="4">Child 1</span>
    <span id="5">Child 2</span>
    <span id="6">Child 3</span>
    </pre>
    </div>
    """

    def test_attribute_not_equal_no_quotes(self):
        """Test attribute with value that does not equal specified value (no quotes)."""

        # No quotes
        self.assert_selector(
            self.MARKUP,
            'body [id!=\\35]',
            ["div", "0", "1", "2", "3", "pre", "4", "6"],
            flags=util.HTML5
        )

    def test_attribute_not_equal_quotes(self):
        """Test attribute with value that does not equal specified value (quotes)."""

        # Quotes
        self.assert_selector(
            self.MARKUP,
            "body [id!='5']",
            ["div", "0", "1", "2", "3", "pre", "4", "6"],
            flags=util.HTML5
        )

    def test_attribute_not_equal_double_quotes(self):
        """Test attribute with value that does not equal specified value (double quotes)."""

        # Double quotes
        self.assert_selector(
            self.MARKUP,
            'body [id!="5"]',
            ["div", "0", "1", "2", "3", "pre", "4", "6"],
            flags=util.HTML5
        )

    def assert_syntax_error_no_hang(self, selector):
        """Assert the selector fails with a syntax error promptly instead of hanging."""

        # A pattern stuck in catastrophic backtracking holds the GIL, so it can neither be
        # interrupted from another thread nor timed out with `signal.SIGALRM` (which does not
        # exist on Windows). Compiling in a child process bounds the work on every platform.
        env = os.environ.copy()
        paths = [os.path.dirname(os.path.dirname(os.path.abspath(sv.__file__)))]
        if env.get('PYTHONPATH'):
            paths.append(env['PYTHONPATH'])
        env['PYTHONPATH'] = os.pathsep.join(paths)

        try:
            results = subprocess.run(
                [sys.executable, '-c', 'import sys, soupsieve as sv; sv.compile(sys.argv[1])', selector],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                timeout=self.COMPILE_TIMEOUT
            )
        except subprocess.TimeoutExpired:
            self.fail(
                'Compiling {!r} did not finish within {} seconds'.format(selector, self.COMPILE_TIMEOUT)
            )

        self.assertIn('SelectorSyntaxError', results.stderr.decode('utf-8', 'replace'))

    def test_bad_attribute_unclused(self):
        """Test bad attribute fails for syntax error, not timeout error."""

        self.assert_syntax_error_no_hang('[a="' + ('x' * 300))

    def test_bad_attribute_unclused_single_quote(self):
        """Test bad attribute with a single quote fails for syntax error, not timeout error."""

        self.assert_syntax_error_no_hang("[a='" + ('x' * 300))

    def test_bad_attribute_unclosed_bracket(self):
        """Test bad attribute with an unquoted value fails for syntax error, not timeout error."""

        self.assert_syntax_error_no_hang('[a=' + ('x' * 300))
