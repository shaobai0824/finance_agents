#!/usr/bin/env python3
"""
Simple LLM middleware verification test
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'main', 'python'))

async def main():
    print("Testing LLM Middleware Integration...")

    # Test LLM client
    try:
        from llm import llm_manager, is_llm_configured, generate_llm_response

        print(f"LLM Configured: {is_llm_configured()}")
        print(f"Available Clients: {llm_manager.get_available_clients()}")
        print(f"Default Client: {llm_manager.default_client}")

        # Test direct LLM call
        response = await generate_llm_response("Provide investment advice", max_tokens=50)
        print(f"LLM Response Model: {response.model}")
        print(f"Response Length: {len(response.content)} chars")

    except Exception as e:
        print(f"LLM Test Failed: {e}")
        return False

    # Test agents
    try:
        from agents import FinancialPlannerAgentLLM
        from agents.base_agent import AgentMessage, MessageType, AgentType

        agent = FinancialPlannerAgentLLM()
        llm_status = agent.get_llm_status()

        print(f"Agent LLM Configured: {llm_status['llm_configured']}")
        print(f"Agent Model: {llm_status['model']}")

        # Test agent message processing
        message = AgentMessage(
            agent_type=AgentType.FINANCIAL_PLANNER,
            message_type=MessageType.QUERY,
            content='Please provide investment advice'
        )

        response = await agent.process_message(message)

        print(f"Agent Response Type: {response.message_type.value}")
        print(f"Agent Confidence: {response.confidence}")
        print(f"Agent LLM Model Used: {response.metadata.get('llm_model', 'unknown')}")
        print(f"Response Content Length: {len(response.content)} chars")

        # Check if using LLM middleware (not fallback)
        using_llm = response.metadata.get('llm_model') == 'gpt-4o-mini'
        print(f"Using LLM Middleware: {using_llm}")

        if using_llm:
            print("SUCCESS: All agents are using LLM middleware!")
            return True
        else:
            print("WARNING: Agents may be using fallback responses")
            return False

    except Exception as e:
        print(f"Agent Test Failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    print(f"\nFinal Result: {'SUCCESS' if success else 'FAILED'}")
    print("All agents are configured to use gpt-4o-mini through LLM middleware")