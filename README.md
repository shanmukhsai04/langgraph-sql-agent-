# LangGraph SQL Agent

> Ask a question in plain English, get a real answer from your database — safely.

An intelligent SQL agent built with **LangGraph** that turns natural language questions into safe, validated SQL queries — executes them against a SQLite database, and automatically fixes failed queries.

## Overview

This project demonstrates a multi-step agentic workflow for database querying:

1. **Understand** natural language questions
2. **Retrieve schema** to understand available tables and columns
3. **Generate** a SQL query using an LLM (GPT-4o-mini)
4. **Validate** the query for safety (SELECT-only, blocks destructive keywords like `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `CREATE`)
5. **Execute** the validated query
6. **Auto-fix** failed queries (up to 3 retry attempts) by analyzing the error and regenerating the query

## Architecture


<img width="1372" height="872" alt="image" src="https://github.com/user-attachments/assets/f74f7e31-0a72-41e2-aa4a-093c43b5b8bb" />


The agent is built as a state graph using LangGraph:

START → agent → (tool call?) → tools → agent → ... → END

- **`agent` node** — decides which tool to call next based on the conversation state and system instructions
- **`tools` node** — executes the selected tool (schema lookup, query generation, execution, or error fixing)
- **Conditional routing** — loops between `agent` and `tools` until the agent has a final answer, then routes to `END`

## SQLite Agent Architecture

*A natural language question flows through query generation, safety validation, error-fixing, and execution to produce a final result — orchestrated as a loop between the agent and its tools until a complete answer is reached.*

## Tools

| Tool | Purpose |
|---|---|
| `get_database_schema` | Fetches table structure and column info |
| `generate_sql_query` | Converts a natural language question into a SQL query |
| `validate_sql_query` | Checks the query is a safe `SELECT` statement before execution |
| `execute_sql_query` | Runs the validated query against the database |
| `fix_sql_error` | Analyzes a failed query + error message and generates a corrected query |

## Database

Uses the [employees-db-sqlite](https://github.com/fracpete/employees-db-sqlite) sample dataset — a SQLite database containing employee records, salaries, departments, and job titles.

## Tech Stack

- **LangGraph** — agent orchestration / state graph
- **LangChain** — tool definitions, SQLDatabase utility
- **OpenAI GPT-4o-mini** — natural language → SQL generation and error correction
- **SQLite** — database engine
