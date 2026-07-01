**LangGraph SQL Agent**

An intelligent SQL agent built with LangGraph that turns natural language questions into safe, validated SQL queries — executes them against a SQLite database, and automatically fixes failed queries.

**Overview**

This project demonstrates a multi-step agentic workflow for database querying:


Understand natural language questions
Retrieve schema to understand available tables and columns
Generate a SQL query using an LLM (GPT-4o-mini)
Validate the query for safety (SELECT-only, blocks destructive keywords like INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE)
Execute the validated query
Auto-fix failed queries (up to 3 retry attempts) by analyzing the error and regenerating the query


**Architecture**

The agent is built as a state graph using LangGraph:

START → agent → (tool call?) → tools → agent → ... → END


agent node — decides which tool to call next based on the conversation state and system instructions
tools node — executes the selected tool (schema lookup, query generation, execution, or error fixing)
Conditional routing — loops between agent and tools until the agent has a final answer, then routes to END

<img width="1372" height="872" alt="image" src="https://github.com/user-attachments/assets/16008b91-1327-4182-aaae-0365b1237e12" />

**Tools**

ToolPurposeget_database_schemaFetches table structure and column infogenerate_sql_queryConverts a natural language question into a SQL queryvalidate_sql_queryChecks the query is a safe SELECT statement before executionexecute_sql_queryRuns the validated query against the databasefix_sql_errorAnalyzes a failed query + error message and generates a corrected query

**Database**

Uses the employees-db-sqlite sample dataset — a SQLite database containing employee records, salaries, departments, and job titles.

**Tech Stack**


LangGraph — agent orchestration / state graph
LangChain — tool definitions, SQLDatabase utility
OpenAI GPT-4o-mini — natural language → SQL generation and error correction
SQLite — database engineLangGraph SQL Agent

An intelligent SQL agent built with LangGraph that turns natural language questions into safe, validated SQL queries — executes them against a SQLite database, and automatically fixes failed queries.

**Overview**

This project demonstrates a multi-step agentic workflow for database querying:


Understand natural language questions
Retrieve schema to understand available tables and columns
Generate a SQL query using an LLM (GPT-4o-mini)
Validate the query for safety (SELECT-only, blocks destructive keywords like INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE)
Execute the validated query
Auto-fix failed queries (up to 3 retry attempts) by analyzing the error and regenerating the query


**Architecture**

The agent is built as a state graph using LangGraph:

START → agent → (tool call?) → tools → agent → ... → END


agent node — decides which tool to call next based on the conversation state and system instructions
tools node — executes the selected tool (schema lookup, query generation, execution, or error fixing)
Conditional routing — loops between agent and tools until the agent has a final answer, then routes to END


**Tools**

ToolPurposeget_database_schemaFetches table structure and column infogenerate_sql_queryConverts a natural language question into a SQL queryvalidate_sql_queryChecks the query is a safe SELECT statement before executionexecute_sql_queryRuns the validated query against the databasefix_sql_errorAnalyzes a failed query + error message and generates a corrected query

**Database**

Uses the employees-db-sqlite sample dataset — a SQLite database containing employee records, salaries, departments, and job titles.

**Tech Stack**


LangGraph — agent orchestration / state graph
LangChain — tool definitions, SQLDatabase utility
OpenAI GPT-4o-mini — natural language → SQL generation and error correction
SQLite — database engine

Database: **employees_db** (SQLite) with employee records, salaries, departments, and titles.

https://github.com/fracpete/employees-db-sqlite
