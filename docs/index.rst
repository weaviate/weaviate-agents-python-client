===============
Weaviate Agents
===============

Weaviate Agents are pre-built agentic services designed to simplify common tasks when working with Large Language Models (LLMs) and your Weaviate instance. They are experts in performing Weaviate-specific data operations, streamlining AI development and data engineering workflows.

.. warning::
   Weaviate Agents are currently only available for users of `Weaviate Cloud (WCD) <https://weaviate.io/developers/wcs/>`_. They require a connection to a WCD instance and are not available for self-hosted Weaviate clusters at this time.

Available agents
----------------

The Weaviate Agents framework currently includes the following:

* `Query Agent <https://weaviate.io/developers/agents/query>`_: Designed to answer natural language questions by intelligently querying the data stored within your Weaviate database.

* `Transformation Agent <https://weaviate.io/developers/agents/transformation>`_: Enhances your data by manipulating it based on specific user instructions. This can involve tasks like summarizing, extracting information, or reformatting data stored in Weaviate.

* `Personalization Agent <https://weaviate.io/developers/agents/personalization>`_: Customizes outputs based on persona-specific information. This agent can learn user behavior and provide recommendations tailored to individual preferences.

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

* `Weaviate Agents - Official documentation <https://weaviate.io/developers/agents>`_

Client API reference
------------------------

Detailed documentation for the Python client classes and functions corresponding to these agents can be found below:

.. toctree::
   :maxdepth: 2

   weaviate_agents

Support
-------

- Use our `Forum <https://forum.weaviate.io>`_ for support or any other question.
- Use our `Slack Channel <https://weaviate.io/slack>`_ for discussions or any other question.
- Use the ``weaviate`` tag on `StackOverflow <https://stackoverflow.com/questions/tagged/weaviate>`_  for questions.
- For bugs or problems, submit a GitHub `issue <https://github.com/weaviate/weaviate-python-client/issues>`_.
