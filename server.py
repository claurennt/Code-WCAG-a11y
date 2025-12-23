import json
from pathlib import Path
from mcp.server.fastmcp import FastMCP
import logging


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("WCAGCodeA11y")

# Create an MCP server
mcp = FastMCP("WCAG Code A11y")


@mcp.tool("analyzeWCAG")
def analyze_file_against_WCAG(file: str) -> str:
    """Analyzes a file and relative modules and suggests what WCAG SC the component might fall under"""

    return file


# Fetch WCAG text dynamically - resource template
@mcp.resource("resource://{version}")
def get_WCAG_by_version(version: str):
    path = Path(__file__).parent / "data" / f"wcag-{version}.json"

    logger.info(f"Attempting to load WCAG version: {version}")
    logger.debug(f"Looking for file at: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        logger.info(f"Successfully loaded WCAG {version}")
        logger.debug(f"Loaded {len(data)} items")

        return data

    except FileNotFoundError:
        logger.error(f"WCAG file not found: {path}")
        return {"error": f"WCAG version {version} not available"}

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {path}: {e}")
        return {"error": "Invalid JSON format"}

    except Exception as e:
        logger.exception(f"Unexpected error loading WCAG: {e}")
        return {"error": "Internal server error"}


if __name__ == "__main__":
    mcp.run()
