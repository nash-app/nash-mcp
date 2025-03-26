#!/usr/bin/env python
import os
import sys
import json
import asyncio
import logging
import signal
import atexit
from dotenv import load_dotenv
from browser_use import Agent, Browser, BrowserConfig
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

# Configure logging to stderr
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", stream=sys.stderr)

# Configure browser_use logging
browser_use_logger = logging.getLogger("browser_use")
browser_use_logger.setLevel(logging.INFO)

# Load environment variables from .env file
load_dotenv()

# Global variable to track browser instance for cleanup
_browser_instance = None


# Make sure to clean up browser on exit
def cleanup_browser():
    if _browser_instance:
        logging.info("Cleaning up browser instance through atexit handler")
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(_browser_instance.close())
        else:
            # Create a new event loop if the main one is closed
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            new_loop.run_until_complete(_browser_instance.close())
            new_loop.close()


# Register cleanup handler
atexit.register(cleanup_browser)


# Handle termination signals
def signal_handler(sig, frame):
    logging.info(f"Received signal {sig}, cleaning up and exiting")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


async def run_browser_agent(task):
    """Run the browser-use agent with the given task."""
    # Load secrets from environment variable
    secrets_path = os.environ.get("NASH_SECRETS_PATH")
    if secrets_path and os.path.exists(secrets_path):
        try:
            with open(secrets_path, "r") as f:
                secrets = json.load(f)

            # Add secrets to environment variables
            for secret in secrets:
                if "key" in secret and "value" in secret:
                    os.environ[secret["key"]] = secret["value"]

            logging.info(f"Loaded secrets from {secrets_path}")
        except Exception as e:
            logging.error(f"Error loading secrets: {str(e)}")
    else:
        logging.warning(f"Secrets path not found or invalid: {secrets_path}")

    # Get API key from JSON file at NASH_MODELS_PATH
    models_path = os.environ.get("NASH_MODELS_PATH")
    if not models_path:
        print(json.dumps({"error": "NASH_MODELS_PATH not found in environment variables"}))
        return

    try:
        with open(models_path, "r") as f:
            api_key_data = json.load(f)
            # Find entries for both providers
            anthropic_keys = [item["value"] for item in api_key_data if item.get("provider") == "anthropic"]
            openai_keys = [item["value"] for item in api_key_data if item.get("provider") == "openai"]

            # Determine which provider to use and set appropriate model
            if anthropic_keys:
                api_key = anthropic_keys[0]
                model_name = "claude-3-7-sonnet-latest"
                llm_class = ChatAnthropic
                api_key_param = "anthropic_api_key"
            elif openai_keys:
                api_key = openai_keys[0]
                model_name = "o3-mini"
                llm_class = ChatOpenAI
                api_key_param = "openai_api_key"
            else:
                print(json.dumps({"error": "No supported API keys found in JSON file (needs OpenAI or Anthropic)"}))
                return
    except Exception as e:
        print(json.dumps({"error": f"Failed to read API key from {models_path}: {str(e)}"}))
        return

    if not api_key:
        print(json.dumps({"error": "No API key found in JSON file"}))
        return

    try:
        # Initialize LLM
        llm = llm_class(model=model_name, **{api_key_param: api_key}, temperature=0)
        logging.info(f"LLM initialized successfully with {model_name}")

        # Check if Chrome is installed (macOS only since repo specified this is only for macOS)
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

        if not os.path.exists(chrome_path):
            error_msg = "Google Chrome is not installed. Please install Chrome to use the browser automation feature."
            logging.error(f"Chrome not found at {chrome_path}")
            print(json.dumps({"error": error_msg}))
            return

        # Configure browser to use user's Chrome installation
        browser = Browser(
            config=BrowserConfig(
                chrome_instance_path=chrome_path,
                extra_chromium_args=[
                    "--user-data-dir=/tmp/chrome-temp",  # Use temporary profile directory
                    "--profile-directory=Guest",  # Use Guest profile
                    "--disable-extensions",  # Disable all extensions
                ],
            )
        )

        # Store browser in global variable for cleanup
        global _browser_instance
        _browser_instance = browser
        logging.info("Set browser instance for global cleanup tracking")

        # Create the agent with configured browser
        agent = Agent(task=task, llm=llm, browser=browser)
        logging.info("Agent created successfully with user's Chrome installation")

        try:
            # Run the agent with a browser wrapper to ensure closing
            result = await agent.run(max_steps=4)
            logging.info("Agent completed task successfully")

            # Extract and return the result
            if hasattr(result, "final_result"):
                final_result = result.final_result()
            else:
                final_result = str(result)

            # Return the result as JSON to stdout
            print(json.dumps({"result": final_result}))
        finally:
            # Ensure browser is closed properly
            try:
                await browser.close()
                logging.info("Browser closed successfully")
            except Exception as close_error:
                logging.error(f"Error closing browser: {str(close_error)}")
                # Force exit to ensure browser process is terminated
                print(json.dumps({"result": "Task completed but had trouble closing the browser cleanly."}))
                # Not calling sys.exit() here as we want controlled shutdown

    except Exception as e:
        logging.error(f"Error during browser automation: {str(e)}")
        print(json.dumps({"error": str(e)}))


def main():
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No task provided. Usage: python browser_agent.py 'Your task description'"}))
        sys.exit(1)

    # Get the task from command line arguments
    task = sys.argv[1]

    # Run the agent
    try:
        asyncio.run(run_browser_agent(task))
    except Exception as e:
        logging.error(f"Unhandled exception: {str(e)}")
        print(json.dumps({"error": f"Unhandled exception: {str(e)}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
