# Weaviate Agents Python Client

[![Main Branch](https://github.com/weaviate/weaviate-agents-python-client/actions/workflows/main.yaml/badge.svg?branch=main)](https://github.com/weaviate/weaviate-agents-python-client/actions)
[![PyPI version](https://badge.fury.io/py/weaviate-agents.svg)](https://badge.fury.io/py/weaviate-agents)

This package is a sub-package to be used in conjunction with the [Weaviate Python Client](https://github.com/weaviate/weaviate-python-client). Rather than installing this package directly, you should install it as an optional extra when installing the Weaviate Python Client.

```bash
pip install weaviate-client[agents]
```

# Query Agent

Query Agent is a Weaviate-native agent that turns natural-language questions into precise database operations, making full use of dynamic filters, cross-collection routing, query optimization, and aggregations. It returns accurate and relevant results with source citations. It replaces manual query construction and ad-hoc logic with runtime, context-aware planning that optimizes and executes queries across user collections.

Query Agent supports two modes:
- Ask mode: for building agentic applications that require conversational interactions and answers backed by data stored in Weaviate. This can be accessed using the `ask()` and `ask_stream()` methods, depending on whether your application needs streaming tokens and progress messages.
- Search mode: for building agentic applications that require high quality information retrieval with strong recall and controlled precision, without the final-answer generation. This can be accessed using the `search()` method.

The `QueryAgent` and `AsyncQueryAgent` clients provide sync and async versions of the same methods.

The Weviate Query Agent is Generally Available. For more information, see the [Weaviate Agents - Query Agent Docs](https://weaviate.io/developers/agents/query).

# Transformation Agent

The Weaviate Transformation Agent is an agentic service designed to augment and transform data using generative models. Use the Transformation Agent to append new properties and/or update existing properties of data on existing objects in Weaviate.

> ⚠️ **Alpha Release**: Weaviate Transformation Agent is currently in alpha and is subject to change. Features may be modified or removed without notice. Please check that you are using the latest version of the package.

For more information, see the [Weaviate Agents - Transformation Agent Docs](https://docs.weaviate.io/agents/transformation).

# Personalization Agent

The Weaviate Personalization Agent is an agentic service designed to return personalized recommendations tailored to each user. The developer would simply provide a user profile with a history of interactions, and the Personalization Agent takes care of all intervening steps to provide a set of personalized recommendations from Weaviate.

> ⚠️ **Alpha Release**: Weaviate Personalization Agent is currently in alpha and is subject to change. Features may be modified or removed without notice. Please check that you are using the latest version of the package.

For more information, see the [Weaviate Agents - Personalization Agent Docs](https://docs.weaviate.io/agents/personalization).