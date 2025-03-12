import os
import asyncio
import logging
import traceback
from langchain_anthropic import ChatAnthropic
from browser_use import Agent


def operate_webpage(task: str) -> str:
    """
    Automate web browsing tasks using browser-use and Claude to control a browser.
    
    This tool uses Claude to operate a web browser, allowing it to perform complex web tasks
    like navigating websites, filling forms, clicking buttons, and extracting information.
    Use this tool when you need to interact with websites in a way that requires browser
    automation rather than simple HTTP requests.
    
    Examples of tasks this tool can handle:
    - "Search for topic X on Google and summarize the top 3 results"
    - "Go to website Y and fill out their contact form"
    - "Log into service Z and extract my account information"
    - "Find and download a specific report from a website"
    - "Complete a multi-step process on a website"
    
    WHEN TO USE:
    - When you need to interact with websites that require clicking, form filling or navigation
    - When you need to extract data from dynamic websites that load content with JavaScript
    - When you need to perform complex sequences of actions on a website
    - When simple HTTP requests with WebFetchTool would not work
    
    LIMITATIONS:
    - Cannot access sites requiring CAPTCHA or advanced anti-bot measures
    - Cannot access sites requiring 2FA or authentication methods beyond username/password
    - Task execution might take 30+ seconds for complex operations
    - Browser interactions have natural variance and may occasionally fail
    
    Args:
        task: A detailed description of the web task to accomplish
    
    Returns:
        The result of the web automation task, typically containing extracted information
        or confirmation of task completion
    """
    try:
        # Run the async function in a new event loop
        return asyncio.run(_run_browser_agent(task))
    except Exception as e:
        logging.error(f"Error in operate_webpage: {str(e)}")
        logging.error(traceback.format_exc())
        return f"Error executing web task: {str(e)}\nTraceback: {traceback.format_exc()}"

async def _run_browser_agent(task: str) -> str:
    """Run browser-use agent asynchronously."""
    logging.info(f"Starting browser automation task: {task}")
    
    # Get API key from environment
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return "Error: ANTHROPIC_API_KEY not found in environment variables"
    
    # Initialize LLM
    try:
        llm = ChatAnthropic(
            model="claude-3-opus-20240229",
            anthropic_api_key=api_key,
            temperature=0
        )
        logging.info("LLM initialized successfully")
    except Exception as e:
        logging.error(f"Error initializing LLM: {str(e)}")
        return f"Error initializing LLM: {str(e)}"
    
    # Create and run agent
    try:
        agent = Agent(
            task=task,
            llm=llm,
        )
        logging.info("Agent created successfully")
        
        # Run the agent with timeout
        result = await asyncio.wait_for(agent.run(), timeout=300)  # 5 minute timeout
        logging.info("Agent completed task successfully")
        
        # Extract the final text result
        if hasattr(result, 'final_result'):
            final_result = result.final_result()
        else:
            final_result = str(result)
        
        return final_result
        
    except asyncio.TimeoutError:
        logging.error("Browser automation timed out after 300 seconds")
        return "Error: Browser automation timed out after 300 seconds"
    except Exception as e:
        logging.error(f"Error during browser automation: {str(e)}")
        return f"Error during browser automation: {str(e)}"
