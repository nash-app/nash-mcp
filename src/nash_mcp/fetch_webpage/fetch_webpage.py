import html2text
import requests
import logging
import traceback


def fetch_webpage(url: str) -> str:
    """Fetch content from a webpage and convert to readable text.

    This tool retrieves the HTML content from a URL and converts it to plain text,
    removing HTML tags, formatting, and other non-text elements. The conversion
    ignores links and images to focus on the textual content.

    USE CASES:
    - Retrieving article content for analysis
    - Accessing documentation from websites
    - Scraping data from public web pages
    - Gathering information from online resources
    - Reading blog posts, news articles, or reference materials

    USAGE WORKFLOW:
    1. Call fetch_webpage with a complete URL (including https://)
    2. Process the returned text directly or with execute_python()
    3. For complex HTML parsing needs, use execute_python() with BeautifulSoup after this

    NOTE: For sites that load content dynamically with JavaScript after initial page load,
    or for interactive websites requiring form filling, button clicking, or navigation,
    use the operate_browser tool instead, which provides full browser automation capabilities.

    IMPLEMENTATION DETAILS:
    - Uses requests library to fetch the webpage
    - Uses html2text to convert HTML to markdown-like plain text
    - Ignores links and images in the conversion
    - Returns error message if the fetch fails

    SECURITY AND ETHICAL CONSIDERATIONS:
    - Only fetch publicly accessible webpages
    - Respect robots.txt and website terms of service
    - Don't use for scraping private/protected content
    - Avoid making excessive requests to the same site
    - Don't use for accessing internal network resources or localhost
    - Be mindful of rate limits and server load

    Args:
        url: Complete URL to fetch (including https:// protocol)

    Returns:
        Plain text content of the webpage with HTML elements removed
        Error message if the fetch fails
    """
    logging.info(f"Fetching webpage: {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()
        logging.info(f"Successfully retrieved content from {url} (status code: {response.status_code})")

        h = html2text.HTML2Text()
        h.ignore_links = True
        h.ignore_images = True

        converted_text = h.handle(response.text)
        logging.info(f"Successfully converted HTML to text (content length: {len(converted_text)} chars)")

        return converted_text
    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP error while fetching {url}: {str(e)}")
        return f"Error fetching {url}: HTTP status code {e.response.status_code}"
    except requests.exceptions.ConnectionError as e:
        logging.error(f"Connection error while fetching {url}: {str(e)}")
        return f"Error fetching {url}: Connection failed. Check the URL and your internet connection."
    except requests.exceptions.Timeout as e:
        logging.error(f"Timeout error while fetching {url}: {str(e)}")
        return f"Error fetching {url}: Request timed out."
    except requests.exceptions.RequestException as e:
        logging.error(f"Request exception while fetching {url}: {str(e)}")
        return f"Error fetching {url}: {str(e)}"
    except Exception as e:
        logging.error(f"Unexpected error while fetching {url}: {str(e)}")
        logging.error(traceback.format_exc())
        return f"Error fetching {url}: {str(e)}"
