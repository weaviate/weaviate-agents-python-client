from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel
from rich.pretty import Pretty
from rich.table import Table

if TYPE_CHECKING:
    from weaviate_agents.query.classes import AskModeResponse, QueryAgentResponse

console = Console()


def print_query_agent_response(response: "QueryAgentResponse"):
    """Prints a formatted response from the Query Agent using rich."""
    console.print(
        Panel(
            response.original_query,
            title="🔍 Original Query",
            padding=1,
        )
    )

    console.print(
        Panel(response.final_answer, title="📝 Final Answer", style="cyan", padding=1)
    )

    for collection_searches in response.searches:
        for i, result in enumerate(collection_searches):
            console.print(
                Panel(
                    Pretty(result),
                    title=f"🔭 Searches Executed {i+1}/{len(collection_searches)}",
                    style="white",
                    padding=1,
                )
            )
    if len(response.searches) == 0:
        console.print(Panel("🔭 No Searches Run", style="indian_red", padding=1))

    for collection_aggs in response.aggregations:
        for i, agg in enumerate(collection_aggs):
            console.print(
                Panel(
                    Pretty(agg),
                    title=f"📊 Aggregations Run {i+1}/{len(collection_aggs)}",
                    style="white",
                    padding=1,
                )
            )
    if len(response.aggregations) == 0:
        console.print(Panel("📊 No Aggregations Run", style="indian_red", padding=1))

    if response.missing_information:
        title = (
            "⚠️ Answer is Partial - Missing Information:"
            if response.is_partial_answer
            else "⚠️ Missing Information:"
        )
        missing_info = []
        for missing in response.missing_information:
            missing_info.append(f"- {missing}")

        console.print(
            Panel("\n".join(missing_info), title=title, style="yellow", padding=1)
        )

    sources = []
    for source in response.sources:
        sources.append(f" - {source}")
    if sources:
        console.print(
            Panel("\n".join(sources), title="📚 Sources", style="white", padding=1)
        )

    print("\n")

    table = Table(title="📊 Usage Statistics", show_header=False)
    table.add_row("LLM Requests:", str(response.usage.requests))
    table.add_row("Input Tokens:", str(response.usage.request_tokens))
    table.add_row("Output Tokens:", str(response.usage.response_tokens))
    table.add_row("Total Tokens:", str(response.usage.total_tokens))
    console.print(table)

    console.print(
        f"\n[bold]Total Time Taken:[/bold] {response.total_time:.2f}s", style="cyan"
    )


def print_ask_mode_response(response: "AskModeResponse"):
    """Prints a formatted response from the Ask Mode using rich."""
    console.print(
        Panel(
            response.final_answer, title="💬 Ask Mode Response", style="cyan", padding=1
        )
    )

    for i, result in enumerate(response.searches):
        search_content = Pretty(result)
        console.print(
            Panel(
                search_content,
                title=f"🔭 Search {i+1}/{len(response.searches)}",
                style="white",
                padding=1,
            )
        )

    if len(response.searches) == 0:
        console.print(Panel("🔭 No Searches Run", style="indian_red", padding=1))

    for i, agg in enumerate(response.aggregations):
        agg_content = Pretty(agg)
        console.print(
            Panel(
                agg_content,
                title=f"📊 Aggregation {i+1}/{len(response.aggregations)}",
                style="white",
                padding=1,
            )
        )

    if len(response.aggregations) == 0:
        console.print(Panel("📊 No Aggregations Run", style="indian_red", padding=1))

    if response.missing_information:
        title = (
            "⚠️ Answer is Partial - Missing Information:"
            if response.is_partial_answer
            else "⚠️ Missing Information:"
        )
        missing_info = []
        for missing in response.missing_information:
            missing_info.append(f"- {missing}")

        console.print(
            Panel("\n".join(missing_info), title=title, style="yellow", padding=1)
        )

    if response.sources:
        sources = []
        for source in response.sources:
            sources.append(f" - {source}")
        console.print(
            Panel("\n".join(sources), title="📚 Sources", style="white", padding=1)
        )

    print("\n")

    table = Table(title="📊 Usage Statistics", show_header=False)
    table.add_row("Model Units:", str(response.usage.model_units))
    table.add_row("Usage in Plan:", str(response.usage.usage_in_plan))
    table.add_row(
        "Remaining Plan Requests:", str(response.usage.remaining_plan_requests)
    )
    console.print(table)

    console.print(
        f"\n[bold]Total Time Taken:[/bold] {response.total_time:.2f}s", style="cyan"
    )
