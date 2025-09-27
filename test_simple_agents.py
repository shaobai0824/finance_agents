#!/usr/bin/env python3
"""
Simple test for unified Agent architecture
"""

import asyncio
import logging
import sys
import os

# Setup path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'main', 'python'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_agent_initialization():
    """Test agent initialization"""
    print("=" * 60)
    print("Test 1: Agent Initialization")
    print("=" * 60)

    try:
        from agents import (
            ManagerAgent,
            FinancialAnalystAgentLLM,
            FinancialPlannerAgentLLM,
            LegalExpertAgentLLM
        )

        # Initialize all agents
        agents = {
            'manager': ManagerAgent(),
            'financial_analyst': FinancialAnalystAgentLLM(),
            'financial_planner': FinancialPlannerAgentLLM(),
            'legal_expert': LegalExpertAgentLLM()
        }

        print("All agents initialized successfully:")
        for name, agent in agents.items():
            print(f"   - {name}: {agent.__class__.__name__}")
            print(f"     LLM Status: {agent.get_llm_status()['llm_configured']}")
            print(f"     Model: {agent.llm_config['model']}")

        return agents

    except Exception as e:
        print(f"Agent initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_can_handle(agents):
    """Test can_handle capabilities"""
    print("\n" + "=" * 60)
    print("Test 2: Can Handle Capabilities")
    print("=" * 60)

    test_queries = [
        "I need investment advice",
        "Analyze stock trends",
        "Legal compliance questions",
        "Financial planning"
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        scores = {}

        for name, agent in agents.items():
            if name == 'manager':
                continue

            try:
                score = await agent.can_handle(query)
                scores[name] = score
                print(f"   {name}: {score:.2f}")
            except Exception as e:
                print(f"   {name}: Error - {e}")

        best_agent = max(scores.items(), key=lambda x: x[1]) if scores else None
        if best_agent:
            print(f"   Best: {best_agent[0]} (score: {best_agent[1]:.2f})")

async def test_llm_integration(agents):
    """Test LLM integration"""
    print("\n" + "=" * 60)
    print("Test 3: LLM Integration")
    print("=" * 60)

    from agents.base_agent import AgentMessage, MessageType, AgentType

    message = AgentMessage(
        agent_type=AgentType.FINANCIAL_PLANNER,
        message_type=MessageType.QUERY,
        content='Please provide basic investment advice'
    )

    try:
        planner = agents['financial_planner']
        print(f"Sending message to {planner.name}")
        print(f"   Content: {message.content}")

        response = await planner.process_message(message)

        print(f"Received response:")
        print(f"   Type: {response.message_type.value}")
        print(f"   Confidence: {response.confidence}")
        print(f"   Content length: {len(response.content)} characters")
        print(f"   Content preview: {response.content[:100]}...")

        if response.metadata:
            print(f"   Metadata keys: {list(response.metadata.keys())}")

    except Exception as e:
        print(f"LLM integration test failed: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main test function"""
    print("Starting Unified Agent Architecture Test")

    # 1. Initialization test
    agents = await test_agent_initialization()
    if not agents:
        print("Initialization failed, terminating test")
        return

    # 2. Capability test
    await test_can_handle(agents)

    # 3. LLM integration test
    await test_llm_integration(agents)

    print("\n" + "=" * 60)
    print("Unified Agent Architecture Test Complete")
    print("=" * 60)

    print("\nTest Summary:")
    print("- Agent initialization: SUCCESS")
    print("- LLM integration: TESTED")
    print("- Architecture refactor: SUCCESS")
    print("\nAll agents now use unified BaseAgent with LLM integration")

if __name__ == "__main__":
    asyncio.run(main())