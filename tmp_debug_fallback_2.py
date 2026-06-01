from agentic.agent import Agent
from agentic.schemas import Goal

queries = [
    "Fetch https://en.wikipedia.org/wiki/Claude_Shannon and tell me his birth date, death date, and three key contributions to information theory.",
    "Find 3 family-friendly things to do in Tokyo this weekend. Check Saturday's weather forecast there and tell me which one is most appropriate.",
]

for query in queries:
    print('--- QUERY ---')
    print(query)
    agent = Agent()
    context = agent.memory.read()
    perception = agent.perception.process(query, context, run_history=[])
    print('perception goals', perception.goals)
    print('context_summary repr', repr(perception.context_summary))
    unfinished = [g for g in perception.goals if not g.is_done]
    print('unfinished', unfinished)
    print('strip', bool(perception.context_summary.strip()))
    if not unfinished:
        print('fallback branch start')
        decision = agent.decision.plan(
            Goal(description=query),
            context,
            agent._get_tools(),
            original_query=query,
            relevant_artifacts=perception.relevant_artifacts,
            perception_summary=perception.context_summary,
        )
        print('decision final_answer repr', repr(decision.final_answer))
        direct_result = agent.llm.chat(
            prompt=f"Please answer the following user request directly and succinctly:\n\n{query}",
            system=(
                "You are a helpful assistant. Provide a complete direct answer to the user request. "
                "Do not output JSON or extra metadata."
            ),
            provider=agent.perception.provider,
        )
        print('direct_result text repr', repr(direct_result.get('text')))
        print('direct_result type', type(direct_result.get('text')))
    print()