#!/usr/bin/env python3

import json
import signal
import sys

from typing import Literal
from warnings import filters
from code_wcag_a11y.scripts.utils import index
from code_wcag_a11y.utils.clean_code import (
    clean_code_snippet,
    extract_applicability_signals,
)
from code_wcag_a11y.utils.logger import logger
from playwright.async_api import async_playwright

# from llama_index.core.vector_stores import (
#     MetadataFilters,
#     ExactMatchFilter,
# )
# from langchain import OpenAI
# from langchain.embeddings import OpenAIEmbeddings
import os


import random
import os

os.environ["COHERE_API_KEY"] = "8jYsb9xoOxQpLjxiMum44fVajK3E18yuDzv2QDJO"

from mcp.server.fastmcp import FastMCP


from code_wcag_a11y.globals import DATA_DIR
from code_wcag_a11y.scripts.build_index import get_index
from code_wcag_a11y.scripts.types.chunk_types import WcagVersion


from FlagEmbedding import FlagReranker

# Use FP16 for faster inference (optional)
reranker = FlagReranker("BAAI/bge-reranker-v2-m3", use_fp16=True)

# Create an MCP server
mcp = FastMCP("Code WCAG A11y")

# Or modify PYTHONPATH
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@mcp.tool("getAccessibilityData")
async def get_accessibility_data(code: str) -> dict:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        cdp = await context.new_cdp_session(page)

        html = clean_code_snippet(code)
        logger.debug(code)

        await page.set_content(html, wait_until="load")
        await page.wait_for_timeout(50)

        ax_tree = await cdp.send("Accessibility.getFullAXTree")

        accessible_nodes = normalize_ax_tree(ax_tree)

        await browser.close()
        return accessible_nodes


# return snapshot
def normalize_ax_tree(ax_tree):
    nodes = {}
    for node in ax_tree["nodes"]:
        if node.get("ignored", False):
            continue
        props = {
            p["name"]: p["value"]["value"]
            for p in node.get("properties", [])
            if "value" in p
        }
        labelledby = props.get("labelledby", {})
        labels = []
        if labelledby.get("type") == "nodeList":
            labels = [n["text"] for n in labelledby.get("relatedNodes", [])]

        nodes[node["nodeId"]] = {
            "role": node.get("role", {}).get("value"),
            "name": node.get("name", {}).get("value"),
            "focusable": props.get("focusable", False),
            "editable": props.get("editable", False),
            "readonly": props.get("readonly", False),
            "required": props.get("required", False),
            "labels": labels,
            "ignored": node.get("ignored", False),
        }
    return nodes


@mcp.tool("analyzeWCAG")
async def analyze_file_against_WCAG(
    code: str, wcag_version: WcagVersion = "2.2"
) -> dict:
    accessible_nodes = await get_accessibility_data(code)

    # 1️⃣ Retrieve top chunks from your LlamaIndex
    index = get_index(wcag_version)

    query_engine = index.as_query_engine(similarity_top_k=20)
    top_nodes = query_engine.retrieve(code)  # adjust for your engine API

    # 2️⃣ Prepare reranker

    reranker = FlagReranker("BAAI/bge-reranker-v2-m3", use_fp16=True)

    query_text = f"""
You are an accessibility expert specializing in WCAG {wcag_version}.

Your task is to IDENTIFY which WCAG Success Criteria are RELEVANT to the given code snippet,
based on the types of elements present and their computed accessibility properties.

IMPORTANT:
- Do NOT determine whether the code PASSES or FAILS any Success Criteria.
- Do NOT suggest fixes.
- ONLY identify which WCAG Success Criteria apply and SHOULD be considered during development or testing.

---

INPUT 1: HTML CODE SNIPPET
{code}

---

INPUT 2: COMPUTED ACCESSIBILITY SNAPSHOT

Each item represents one accessible element with its computed properties
(as exposed by the browser accessibility tree).

Schema:
- role: semantic role (e.g. textbox, button, link)
- name: accessible name (string or empty)
- focusable: whether the element can receive focus
- editable: whether user input is allowed
- readonly: whether the element is read-only
- required: whether input is required
- labels: associated label text(s), if any

Data:
{accessible_nodes}

---

INSTRUCTIONS FOR ANALYSIS:

1. List the WCAG Success Criteria that are relevant to this code.
2. Find also techniques that may apply.

---

OUTPUT FORMAT:

Return a list of WCAG Success Criteria and techniques relevant to the provided code snippet,
 why this SC is relevant to this code.

Do NOT include:
- pass/fail judgments
- remediation advice
- speculative criteria not supported by the inputs
"""

    # 3️⃣ Make query-passage pairs
    pairs = [[query_text, chunk.text] for chunk in top_nodes]

    # 4️⃣ Compute relevance scores
    scores = reranker.compute_score(pairs, normalize=True)

    # 5️⃣ Sort chunks by score
    ranked_chunks = [
        chunk
        for _, chunk in sorted(zip(scores, top_nodes), key=lambda x: x[0], reverse=True)
    ]

    # 6️⃣ Format output
    return {
        "wcag_version": wcag_version,
        "ranked_chunks": [
            {
                "id": c.metadata.get("chunk_id"),
                "title": c.metadata.get("title"),
                "score": s,
            }
            for c, s in zip(ranked_chunks, sorted(scores, reverse=True))
        ],
    }


# @mcp.tool("analyzeWCAG")
# async def analyze_file_against_WCAG(
#     code: str,
#     wcag_version: WcagVersion = "2.2",
# ) -> dict:
#     accessible_nodes = await get_accessibility_data(code)

#     """
#     Analyze code and suggest relevant WCAG Success Criteria.
#     """
#     index = get_index(wcag_version)
#     signals = extract_applicability_signals(accessible_nodes)
#     reranker = FlagEmbeddingReranker(
#         model="BAAI/bge-reranker-large",
#         top_n=5,
#     )
#     filters = MetadataFilters(
#         filters=[
#             ExactMatchFilter(key="type", value="success_criterion"),
#             ExactMatchFilter(key="applicable_roles", values=signals["roles"]),
#             ExactMatchFilter(key="applicable_categories", values=signals["categories"]),
#         ]
#     )
#     query_engine = index.as_query_engine(
#         similarity_top_k=8,
#         filters=filters,
#         node_postprocessors=[reranker],
#     )

#     response = query_engine.query(query)

#     return {
#         "wcag_version": wcag_version,
#         "analysis": str(response),
#     }


# Fetch WCAG text dynamically - resource template
@mcp.resource("resource://WCAG/{wcag_version}/{data_type}")
def get_WCAG_by_version(
    wcag_version: WcagVersion = "2.2", data_type: Literal["raw", "processed"] = "raw"
):

    if data_type == "processed":
        filename = f"wcag-{wcag_version}_preprocessed.json"
    else:
        filename = f"wcag-{wcag_version}.json"

    file_path = DATA_DIR / data_type / filename
    logger.info(f"Attempting to load WCAG version: {wcag_version}")
    logger.debug(f"Looking for file at: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        logger.info(f"Successfully loaded WCAG {wcag_version}")

        return data

    except FileNotFoundError:
        logger.error(f"WCAG file not found: {file_path}")
        return {"error": f"WCAG version {wcag_version} not available"}

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return {"error": "Invalid JSON format"}

    except Exception as e:
        logger.exception(f"Unexpected error loading WCAG: {e}")
        return {"error": "Internal server error"}


def shutdown(signum):
    logger.info(f"Received signal {signum}. Shutting down MCP server gracefully...")
    sys.exit(0)


signal.signal(signal.SIGINT, shutdown)  # Ctrl+C
signal.signal(signal.SIGTERM, shutdown)  # Inspector / UV / OS


if __name__ == "__main__":
    logger.info("Starting Code WCAG A11y MCP server...")
    mcp.run()
