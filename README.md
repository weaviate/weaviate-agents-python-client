<p align="center">
    <a href="https://github.com/weaviate/weaviate-agents-python-client">
        <img src="./docs/images/banner.png" alt="Weaviate Agents">
    </a>
</p>

<p align="center">
  <a href="https://docs.weaviate.io/query-agent">Docs</a> •
  <a href="https://weaviate-python-client.readthedocs.io/en/latest/weaviate-agents-python-client/docs/modules.html">Reference Guide</a> •
  <a href="https://weaviate.io">Weaviate</a>
</p>

<p align="center">
  <a href="https://github.com/weaviate/weaviate-agents-python-client/actions"><img src="https://github.com/weaviate/weaviate-agents-python-client/actions/workflows/main.yaml/badge.svg?branch=main" alt="Main Branch"></a>
  <a href="https://badge.fury.io/py/weaviate-agents"><img src="https://badge.fury.io/py/weaviate-agents.svg" alt="PyPI version"></a>
</p>


Weaviate Agents allow you to automatically interface with your Weaviate collections without writing any complex code.

# Installation

This package is a sub-package to be used in conjunction with the [Weaviate Python Client](https://github.com/weaviate/weaviate-python-client). Rather than installing this package directly, you should install it as an optional extra when installing the Weaviate Python Client.

```bash
pip install -U "weaviate-client[agents]"
```

If you are having trouble, try to explicitly install/upgrade the agents package via `pip install -U weaviate-agents`.

# Query Agent

The Query Agent turns natural-language questions into precise database operations, making full use of:

* dynamic filters
* cross-collection routing
* query optimization
* aggregations

It returns accurate and relevant results with source citations. It replaces manual query construction and ad-hoc logic with runtime, context-aware planning that optimizes and executes queries across user collections.

## Ask Mode

**Ask mode** is natural-language in and natural-language out. It searches or aggregates your data, depending on the user's query, and then answers the question with respect to the retrieved data. This can be accessed using the `ask()` or `ask_stream()` methods, depending on whether your application needs streaming tokens and progress messages.

```python
from weaviate.agents.query import QueryAgent

qa = QueryAgent(
    client=client,  # your Weaviate cloud client
    collections=["FinancialContracts"],
)

res = qa.ask("Find all contracts signed in 2025")
```

Ask mode can be optionally customized with:
* Output formats for structured outputs
* LLM-based evaluation of retrieved sources
* Async operations

[Learn more about ask mode in the official documentation.](https://docs.weaviate.io/query-agent/guides/ask_mode)

## Search Mode

**Search mode** is designed for high quality information retrieval with strong recall and controlled precision, without the final-answer generation. This can be accessed using the `search()` method.

```python
from weaviate.agents.query import QueryAgent

qa = QueryAgent(
    client=client,
    collections=["ECommerce"],
)
search_response = qa.search(
    query="Find me some vintage shoes under $70",
    limit=10,
    effort="medium",
)
```

Search mode can be optionally customized with:
* Different filtering strategies for recall or precision based search priorities
* Effort level to control search quality versus latency
* Diversity weights to improve diversity amongst results
* Async operations

[Learn more about search mode in the official documentation.](https://docs.weaviate.io/query-agent/guides/search_mode)

# Documentation

[Full documentation](https://docs.weaviate.io/query-agent)

[Tutorials & Guides](https://docs.weaviate.io/query-agent/recipes)

[API reference manual](https://weaviate-python-client.readthedocs.io/en/latest/weaviate-agents-python-client/docs/modules.html)

# Citation

If you use the Query Agent in your research, please consider citing our paper:

```tex
@article{query-agent,
  title={Querying databases with function calling},
  author={Shorten, Connor and Pierse, Charles and Smith, Thomas Benjamin and D'Oosterlinck, Karel and Celik, Tuana and Cardenas, Erika and Monigatti, Leonie and Hasan, Mohd Shukri and Schmuhl, Edward and Williams, Daniel and others},
  journal={arXiv preprint arXiv:2502.00032},
  year={2025}
}
```