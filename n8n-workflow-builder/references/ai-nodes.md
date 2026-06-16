# AI / LangChain Nodes

n8n's AI nodes live under the `@n8n/n8n-nodes-langchain.` prefix (note: **not**
`n8n-nodes-base.`). They wire together differently from normal nodes: a root node
like the **AI Agent** receives its model, memory, tools, and parsers through
special **`ai_*` connection types**, not through `main`.

The mental model: `main` carries the *data* flowing through the workflow; `ai_*`
connections **attach capabilities** to a root node. The sub-node (model, memory,
tool) is the *source* of the connection and the agent is the *target*.

## The key difference: ai_* connections

A normal connection goes upstream→downstream on `main`. An AI sub-node connects
*into* the agent on a typed channel. The connection is keyed by the **sub-node's
name**, and the type is the capability:

```json
"connections": {
  "Trigger": { "main": [[ { "node": "AI Agent", "type": "main", "index": 0 } ]] },
  "OpenAI Chat Model": {
    "ai_languageModel": [[ { "node": "AI Agent", "type": "ai_languageModel", "index": 0 } ]]
  },
  "Window Buffer Memory": {
    "ai_memory": [[ { "node": "AI Agent", "type": "ai_memory", "index": 0 } ]]
  },
  "Calculator": {
    "ai_tool": [[ { "node": "AI Agent", "type": "ai_tool", "index": 0 } ]]
  }
}
```

Connection types you'll use: `ai_languageModel`, `ai_memory`, `ai_tool`,
`ai_outputParser`, `ai_embedding`, `ai_vectorStore`, `ai_document`,
`ai_textSplitter`, `ai_retriever`. Each agent input accepts the matching type.

## Root nodes

**AI Agent** — the workhorse: an LLM that can call tools, use memory, and follow
a system prompt.
```json
{ "type": "@n8n/n8n-nodes-langchain.agent", "typeVersion": 1.7, "name": "AI Agent",
  "parameters": {
    "promptType": "define",
    "text": "={{ $json.chatInput }}",
    "options": { "systemMessage": "You are a helpful assistant." }
  } }
```

**Basic LLM Chain** — single prompt→completion, no tools.
```json
{ "type": "@n8n/n8n-nodes-langchain.chainLlm", "typeVersion": 1.5, "name": "Basic LLM Chain",
  "parameters": { "promptType": "define", "text": "=Summarize: {{ $json.text }}" } }
```

**Chat Trigger** — entry point for conversational workflows (gives a chat UI /
endpoint).
```json
{ "type": "@n8n/n8n-nodes-langchain.chatTrigger", "typeVersion": 1.1,
  "name": "When chat message received", "parameters": { "options": {} } }
```

Other roots: `chainRetrievalQa` (RAG Q&A), `informationExtractor`,
`textClassifier`, `sentimentAnalysis`.

## Language model sub-nodes (connect via ai_languageModel)

```json
{ "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi", "typeVersion": 1,
  "name": "OpenAI Chat Model",
  "parameters": { "model": "gpt-4o-mini", "options": {} },
  "credentials": { "openAiApi": { "id": "1", "name": "OpenAI account" } } }
```
Others: `lmChatAnthropic` (Claude), `lmChatGoogleGemini`, `lmChatOllama`,
`lmChatGroq`, `lmChatAzureOpenAi`. Each needs its own credential type.

## Memory (ai_memory)

```json
{ "type": "@n8n/n8n-nodes-langchain.memoryBufferWindow", "typeVersion": 1.3,
  "name": "Simple Memory", "parameters": { "contextWindowLength": 10 } }
```
Others: `memoryPostgresChat`, `memoryRedisChat`, `memoryMongoDbChat`.

## Tools (ai_tool) — what the agent can call

```json
{ "type": "@n8n/n8n-nodes-langchain.toolCalculator", "typeVersion": 1, "name": "Calculator", "parameters": {} }
```
Common tools: `toolHttpRequest` (call any API), `toolWorkflow` (call another n8n
workflow as a tool), `toolCode`, `toolVectorStore`, `toolSerpApi`,
`toolWikipedia`. Many regular app nodes can also act as tools in current n8n
(the `$fromAI()` pattern) — check the node's docs.

## Output parsers (ai_outputParser) — force structured output

```json
{ "type": "@n8n/n8n-nodes-langchain.outputParserStructured", "typeVersion": 1.2,
  "name": "Structured Output Parser",
  "parameters": { "jsonSchemaExample": "{\n  \"name\": \"string\",\n  \"score\": 0\n}" } }
```
Enable `hasOutputParser` on the agent/chain when attaching one.

## Embeddings & vector stores (RAG)

```json
{ "type": "@n8n/n8n-nodes-langchain.embeddingsOpenAi", "typeVersion": 1,
  "name": "Embeddings OpenAI", "parameters": { "options": {} } }
```
Vector stores: `vectorStorePinecone`, `vectorStoreQdrant`,
`vectorStoreSupabase`, `vectorStoreInMemory`. A vector store connects to the
agent/chain via `ai_vectorStore`, takes an embedding via `ai_embedding`, and
documents via `ai_document`.

## Minimal agent workflow skeleton

Chat Trigger → AI Agent, with a chat model and a tool attached:

```json
{
  "name": "Simple AI Agent",
  "nodes": [
    { "type": "@n8n/n8n-nodes-langchain.chatTrigger", "typeVersion": 1.1,
      "id": "00000000-0000-0000-0000-000000000001",
      "name": "When chat message received", "position": [0, 0], "parameters": { "options": {} } },
    { "type": "@n8n/n8n-nodes-langchain.agent", "typeVersion": 1.7,
      "id": "00000000-0000-0000-0000-000000000002",
      "name": "AI Agent", "position": [260, 0],
      "parameters": { "options": { "systemMessage": "You are helpful." } } },
    { "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi", "typeVersion": 1,
      "id": "00000000-0000-0000-0000-000000000003",
      "name": "OpenAI Chat Model", "position": [160, 200],
      "parameters": { "model": "gpt-4o-mini", "options": {} },
      "credentials": { "openAiApi": { "id": "1", "name": "OpenAI account" } } },
    { "type": "@n8n/n8n-nodes-langchain.toolCalculator", "typeVersion": 1,
      "id": "00000000-0000-0000-0000-000000000004",
      "name": "Calculator", "position": [360, 200], "parameters": {} }
  ],
  "connections": {
    "When chat message received": { "main": [[ { "node": "AI Agent", "type": "main", "index": 0 } ]] },
    "OpenAI Chat Model": { "ai_languageModel": [[ { "node": "AI Agent", "type": "ai_languageModel", "index": 0 } ]] },
    "Calculator": { "ai_tool": [[ { "node": "AI Agent", "type": "ai_tool", "index": 0 } ]] }
  },
  "settings": { "executionOrder": "v1" }
}
```

AI node `typeVersion`s move quickly. If an agent errors on import, pull a current
export of an equivalent agent from the instance and match its versions — see the
"Staying current" guidance in SKILL.md.
