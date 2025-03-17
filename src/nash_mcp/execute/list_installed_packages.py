import pkg_resources
import sys
import traceback


def list_installed_packages() -> str:
    """List all installed Python packages and their versions in the environment.

    IMPORTANT: ALWAYS USE THIS TOOL FIRST before writing code that imports non-standard libraries
    to ensure the packages you need are available in the environment. This prevents execution
    errors and allows you to adapt your code to the available resources.

    Standard library modules (os, sys, json, etc.) are always available and don't
    need to be checked.

    USAGE WORKFLOW:
    1. Call list_installed_packages() first in your interaction
    2. Note which packages are available (pandas, requests, beautifulsoup4, etc.)
    3. Plan your solution around available packages
    4. If a needed package is missing, consider:
       - Using standard library alternatives
       - Implementing the functionality manually
       - Asking the user if they want to install it

    COMMON PACKAGES TO CHECK FOR:
    - Data analysis: pandas, numpy, matplotlib, scipy
    - Web requests: requests, urllib3, aiohttp
    - Web scraping: beautifulsoup4, lxml, html5lib
    - File formats: openpyxl, xlrd, pyyaml, python-docx
    - Machine learning: scikit-learn, tensorflow, pytorch
    - Image processing: pillow, opencv-python

    IMPLEMENTATION NOTES:
    - Uses pkg_resources to list installed packages
    - Returns both Python version and all package information
    - Handles exceptions gracefully with detailed error messages

    Returns:
        A formatted string containing Python version and all installed packages with their versions
    """
    try:
        # Get Python version info
        python_version = sys.version

        # Get list of installed packages
        installed_packages = sorted([f"{pkg.key}=={pkg.version}" for pkg in pkg_resources.working_set])

        # Format the output
        output = f"Python version: {python_version}\n\n"
        output += "Installed packages:\n"
        output += "\n".join(installed_packages)

        return output
    except Exception as e:
        return f"Error listing packages: {str(e)}\nTraceback: {traceback.format_exc()}\n\n"
