from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING, Union

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.pretty import Pretty
from rich.table import Table
from rich.text import Text

if TYPE_CHECKING:
    from weaviate_agents.query.classes import (
        ProgressMessage,
        QueryAgentResponse,
        StreamedTokens,
    )

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
        console.print(Panel("🔭 No Searches Required", style="indian_red", padding=1))

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
        console.print(Panel("📊 No Aggregations Required", style="indian_red", padding=1))

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


display_context: ContextVar[Union[LiveDisplayState, None]] = ContextVar("display_context", default=None)


class LiveDisplayState:
    def __init__(self):
        self.final_answer: str = ""
        self.progress_messages: list[str] = []
        self.response: Union["QueryAgentResponse", None] = None
        self.live: Union[Live, None] = None

    def render(self):
        """Prints a formatted response from the Query Agent using rich."""
        console.clear()
        if self.response is not None:
            print_query_agent_response(self.response)
            return

        console.print(Markdown("# Query Agent streaming..."))
        if self.progress_messages:
            for message in self.progress_messages[:-1]:
                text = Text(message)
                text.stylize("bright_black")
                console.print(text)

            text = Text(self.progress_messages[-1])
            text.stylize("indian_red")
            console.print(text)

        if self.final_answer:
            console.print(
                Panel(self.final_answer, title="📝 Final Answer", style="cyan", padding=1)
            )

    def update(self, item: Union["ProgressMessage", "StreamedTokens", "QueryAgentResponse"]):
        if self.live is None:
            raise RuntimeError("LiveDisplayState.live must be set before calling update()")
        
        if item.output_type == "progress_message":
            self.progress_messages.append(item.message)
        elif item.output_type == "streamed_tokens":
            self.final_answer += item.delta
        elif item.output_type == "final_state":
            self.response = item
        self.live.update(self.render())


@contextmanager
def live_display_state():
    state = LiveDisplayState()
    token = display_context.set(state)

    try:
        with Live(state.render(), refresh_per_second=4) as live:
            state.live = live
            yield
    finally:
        display_context.reset(token)
