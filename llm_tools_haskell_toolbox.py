import llm
import json
import yaml
import subprocess
from urllib.parse import urlencode, quote
import html2text


class Haskell (llm.Toolbox):
    def __init__(self): pass

    def hoogle(self, query: str, offset: int = 0) -> str:
        """
        This function will access Hoogle (a Haskell type search engine) and
        search for functions matching the type provided in the `query` argument.

        You should generally provide either a type or a name, not both, and you
        probably do not want to provide class constraints. If your request is
        too specific, you will get no results.

        Parameters:
        - query (str): A Haskell function name or type, possibly with polymorphic type variables.
        - offset (int, optional): An optional number of the search result to start from, default 0.

        Returns:
        - str: A list of matches, each match a search result with a
            documentation snippet, formatted in YAML.
        """
        request_parameters = {
            "mode": "json",
            "hoogle": query,
            "start": offset + 1,
            "count": 10,
        }
        base = "https://hoogle.haskell.org"
        url = f"{base}?{urlencode(request_parameters)}"
        curl_output = subprocess.run(
            ["curl", "--fail", "--silent", "--show-error", url],
            capture_output=True,
            text=True,
            check=True,
        )
        results = json.loads(curl_output.stdout)
        if not isinstance(results, list):
            raise ValueError(f"Expected a JSON list, got {type(results).__name__}")
        return yaml.safe_dump (results)

    def hackage(self, package: str, module: str = None, version: str = None, source: bool = False) -> str:
        """
        This function retrieves documentation or source code from Hackage, the central
        repository for Haskell packages. It can be used to fetch the main page of a
        package or the specific documentation for a module within that package.

        Parameters:
        - package (str): The name of the Haskell package to retrieve.
        - module (str, optional): The name of a specific module within the package.
            If provided, the function will target that module's documentation page.
        - version (str, optional): A specific version of the package. If omitted,
            Hackage will typically resolve to the latest version.
        - source (bool, optional): Determines the type of module page to fetch.
            Set to True to retrieve the source code view, or False (default) to
            retrieve the rendered documentation.

        Returns:
        - str: The raw HTML content of the requested Hackage page.
        """
        base = "https://hackage.haskell.org"
        text = get_hackage(base = base, package = package, module = module, version = version, source = source)
        return text

    def local_hackage(self, package: str, module: str = None, version: str = None, source: bool = False) -> str:
        """
        This function retrieves documentation or source code from a local
        instance of hackage — a private repository for Haskell packages. It can
        be used to fetch the main page of a package or the specific
        documentation for a module within that package.

        Parameters:
        - package (str): The name of the Haskell package to retrieve.
        - module (str, optional): The name of a specific module within the package.
            If provided, the function will target that module's documentation page.
        - version (str, optional): A specific version of the package. If omitted,
            Hackage will typically resolve to the latest version.
        - source (bool, optional): Determines the type of module page to fetch.
            Set to True to retrieve the source code view, or False (default) to
            retrieve the rendered documentation.

        Returns:
        - str: The raw HTML content of the requested Hackage page.
        """
        base = "http://localhost:1024"
        text = get_hackage(base = base, package = package, module = module, version = version, source = source)
        return text

@llm.hookimpl
def register_tools(register):
    register(Haskell)

def get_hackage(base: str, package: str, module: str = None, version: str = None, source: bool = False):
    version_suffix = "-" + version if version else ""
    package_base = f"{base}/package/{quote(package, safe='')}{quote(version_suffix, safe='')}"
    if module:
        if source:
            url = f"{package_base}/docs/src/{quote(module)}.html"
        else:
            url = f"{package_base}/docs/{quote(module.replace(".", "-"))}.html"
    else:
        url = f"{package_base}"
    curl_output = subprocess.run(
        ["curl", "--location", "--fail", "--silent", "--show-error", url],
        capture_output=True,
        text=True,
        check=True,
    )
    converter = html2text.HTML2Text()
    converter.ignore_links = True
    text = converter.handle(curl_output.stdout)
    return text
