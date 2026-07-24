# Databricks notebook source
# MAGIC %md
# MAGIC # 06 · Prompt Playbook — Build a "Chat with your Data" App
# MAGIC
# MAGIC This notebook is a set of **prompts you paste into Databricks Assistant / Genie Code** to generate a
# MAGIC **Databricks App** where a user can:
# MAGIC 1. **Chat with the fraud data** via the Genie Conversation API, and
# MAGIC 2. **Upload a document** (PDF/text) and ask questions grounded in that document + the Genie space.
# MAGIC
# MAGIC > The user runs these prompts through **Genie Code** (the coding assistant). This notebook contains the
# MAGIC > prompts and the scaffolding instructions — not a finished app. Each prompt builds one part of the app.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Prerequisites
# MAGIC - Genie Space from notebook `05` exists — copy its **Space ID** from the Genie Space URL
# MAGIC   (`.../genie/rooms/<SPACE_ID>`).
# MAGIC - A SQL Warehouse ID (Serverless).
# MAGIC - Permission to create **Databricks Apps** (`Apps` in the left sidebar).

# COMMAND ----------

# MAGIC %md
# MAGIC ## Prompt 1 · Scaffold the app
# MAGIC Paste into Genie Code:
# MAGIC
# MAGIC ```
# MAGIC Create a Databricks App using Python and Streamlit called "fraud-genie-chat".
# MAGIC It should have:
# MAGIC - app.yaml with command to run streamlit, and env vars GENIE_SPACE_ID and DATABRICKS_WAREHOUSE_ID.
# MAGIC - requirements.txt with streamlit, databricks-sdk, pypdf.
# MAGIC - app.py with a chat UI (st.chat_input / st.chat_message) and a sidebar file uploader.
# MAGIC Use the Databricks SDK for authentication (WorkspaceClient picks up the app service principal).
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Prompt 2 · Wire up the Genie Conversation API
# MAGIC
# MAGIC ```
# MAGIC In app.py, add a function ask_genie(question, conversation_id=None) that calls the Genie
# MAGIC Conversation API via the Databricks SDK (w.genie). Start a conversation on the first message
# MAGIC with start_conversation_and_wait, and continue it with create_message_and_wait using the stored
# MAGIC conversation_id. Return the message text, any generated SQL, and the result table (query_result).
# MAGIC Render the SQL in an expander and the result as a dataframe in the chat message.
# MAGIC ```
# MAGIC
# MAGIC Reference SDK shape (for validation):
# MAGIC ```python
# MAGIC from databricks.sdk import WorkspaceClient
# MAGIC w = WorkspaceClient()
# MAGIC conv = w.genie.start_conversation_and_wait(space_id=GENIE_SPACE_ID, content=question)
# MAGIC # follow-ups:
# MAGIC msg = w.genie.create_message_and_wait(space_id=GENIE_SPACE_ID,
# MAGIC                                        conversation_id=conv.conversation_id,
# MAGIC                                        content=question)
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Prompt 3 · Add document upload + Q&A
# MAGIC
# MAGIC ```
# MAGIC Add a sidebar file_uploader accepting PDF and TXT. When a file is uploaded:
# MAGIC - Extract its text with pypdf (or read text directly for .txt).
# MAGIC - Store the text in st.session_state["doc_text"].
# MAGIC When the user asks a question and a document is loaded, prepend a system-style preamble to the
# MAGIC Genie question that includes the relevant document text as context, e.g.:
# MAGIC "Using this uploaded document as additional context:\n<doc_text>\n\nAnswer: <user question>".
# MAGIC If no document is loaded, send the question to Genie directly.
# MAGIC Truncate document text to a safe token budget (e.g. first 6000 characters) and note the truncation.
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Prompt 4 · Optionally ground answers with a Foundation Model
# MAGIC
# MAGIC ```
# MAGIC Add a toggle "Blend document with LLM". When on, after Genie returns data, call the Foundation Model
# MAGIC API (databricks-meta-llama or claude via serving endpoint) with the Genie result + the document text
# MAGIC to produce a natural-language summary answer. Use w.serving_endpoints.query. Show both the raw Genie
# MAGIC table and the LLM summary.
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Prompt 5 · Deploy the app
# MAGIC
# MAGIC ```
# MAGIC Deploy the fraud-genie-chat app to Databricks Apps. Set the app resources so the service principal
# MAGIC has CAN QUERY on the SQL warehouse and CAN RUN on the Genie space. Provide the databricks apps deploy
# MAGIC command and the app.yaml env block. After deploy, print the app URL.
# MAGIC ```
# MAGIC
# MAGIC CLI reference:
# MAGIC ```bash
# MAGIC databricks apps create fraud-genie-chat
# MAGIC databricks sync ./fraud-genie-chat /Workspace/Users/<you>/fraud-genie-chat
# MAGIC databricks apps deploy fraud-genie-chat \
# MAGIC   --source-code-path /Workspace/Users/<you>/fraud-genie-chat
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Reference · minimal `app.yaml`
# MAGIC ```yaml
# MAGIC command: ["streamlit", "run", "app.py"]
# MAGIC env:
# MAGIC   - name: GENIE_SPACE_ID
# MAGIC     value: "<your-genie-space-id>"
# MAGIC   - name: DATABRICKS_WAREHOUSE_ID
# MAGIC     value: "<your-warehouse-id>"
# MAGIC ```
# MAGIC
# MAGIC ## Reference · `requirements.txt`
# MAGIC ```
# MAGIC streamlit>=1.35
# MAGIC databricks-sdk>=0.30
# MAGIC pypdf>=4.2
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ### ✅ Workshop complete
# MAGIC You now have the full path: **Setup → Data → Bronze → Silver/Gold (Visual Data Prep) → Genie → App.**
# MAGIC See the repo `README.md` for the run order and add your own screenshots.
