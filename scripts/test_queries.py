#!/usr/bin/env python3
"""Test queries for OpenClaw bot"""

import asyncio
import os
from dotenv import load_dotenv
from src.services.chat_handler import chat_handler

load_dotenv()


async def run_tests():
    test_queries = [
        "men's shoes under $100",
        "red wireless headphones under 50 dollars",
        "best running shoes for women",
        "moisturizer for dry skin",
        "cheap bluetooth speaker",
    ]

    print("=" * 60)
    print("OpenClaw Bot Test Queries")
    print("=" * 60)

    for i, query in enumerate(test_queries, 1):
        print(f'\n[Test {i}] Query: "{query}"')
        print("-" * 40)

        response = await chat_handler.handle_message(query, platform="telegram")

        print(response)
        print()


if __name__ == "__main__":
    asyncio.run(run_tests())
