===============
Weaviate Agents
===============

The Query Agent is a pre-built agentic service designed to intelligently and easily query your Weaviate collections in natural language, using Large Language Models (LLMs) to dynamically determine filters, searches and aggregations.

.. warning::
   Weaviate Agents are currently only available for users of `Weaviate Cloud (WCD) <https://weaviate.io/developers/wcs/>`_. They require a connection to a WCD instance and are not available for self-hosted Weaviate clusters at this time.

Available modes
----------------

The Weaviate Agents framework currently includes the following:

* `Ask mode <https://docs.weaviate.io/query-agent/guides/ask_mode>`_: Ask Mode transforms your query into actionable searches or aggregations, and then provides a final answer to the question.

* `Search mode <https://docs.weaviate.io/query-agent/guides/search_mode>`_: Search Mode combines AI-powered semantic search with structured filtering and returns the matching Weaviate objects directly.

* `Suggest queries mode <https://docs.weaviate.io/query-agent/guides/suggest_queries>`_: The Query Agent can suggest queries based on the data in your collections.

Installation
------------

To use the Weaviate Agents, you need to install the main `weaviate-client` package with the optional `[agents]` extra dependency. Run the following command:

.. code-block:: bash

   pip install -U "weaviate-client[agents]"

This ensures you have both the core client and the necessary components for interacting with the agents.

**Troubleshooting: Force pip to install the latest version**

If you suspect you don't have the latest agent features, or if instructed to use a specific version, you can try explicitly upgrading or installing the ``weaviate-agents`` package itself:

* To upgrade to the latest available ``weaviate-agents`` version:

    .. code-block:: bash

       pip install -U weaviate-agents

* To install a specific ``weaviate-agents`` version:

    .. code-block:: bash

       pip install -U weaviate-agents==<version_number>

    *(Replace `<version_number>` with the desired version, e.g., `0.5.0`)*

Official documentation
--------------------

For the most comprehensive and up-to-date information, examples, and guides on Weaviate Agents, please refer to the main Weaviate documentation website:

* `Weaviate Agents - Official documentation <https://docs.weaviate.io/query-agent>`_

Client API reference
------------------------

Detailed documentation for the Python client classes and functions corresponding to these agents can be found below:

.. toctree::
   :maxdepth: 2

   weaviate_agents

Support
-------

- Use our `Forum <https://forum.weaviate.io>`_ for support or any other question.
- Use the ``weaviate`` tag on `StackOverflow <https://stackoverflow.com/questions/tagged/weaviate>`_  for questions.
- For bugs or problems, submit a GitHub `issue <https://github.com/weaviate/weaviate-python-client/issues>`_.
