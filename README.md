# Lyfegen Document Intelligence Application

A full-stack document intelligence application that combines a powerful LangGraph-based conversational agent with a modern React frontend. The system can answer questions about ingested documents, process uploaded files, and maintain conversational context across sessions.

## 🏗️ Architecture

### Backend
- **FastAPI** application with streaming Server-Sent Events (SSE) support
- **LangGraph** conversational agent with tool-based architecture
- **PostgreSQL** database for structured data storage
- **ChromaDB** vector database for document embeddings
- **LangChain** document processing and retrieval pipeline
- **OpenAI GPT-4** for reasoning and response generation

### Frontend
- **React** with Vite for fast development
- **Tailwind CSS** for modern, responsive UI
- **Real-time streaming** chat interface
- **File upload** support for PDF, DOCX, and TXT files
- **Authentication** with API key management

## 🚀 Features

### Core Capabilities
- **Document Q&A**: Ask questions about pre-ingested documents in the knowledge base
- **File Upload**: Upload and analyze specific documents (PDF, DOCX, TXT)
- **Conversational Memory**: Maintains context across conversation turns
- **Real-time Streaming**: See the agent's thinking process in real-time
- **Source Citations**: Responses include links to source documents
- **Structured Data Queries**: Query database information using natural language

### Agent Tools
- **Document Retrieval**: Semantic search across document chunks
- **Full Document Access**: Retrieve complete documents when needed
- **SQL Queries**: Convert natural language to SQL for structured data
- **Conversation Summarization**: Automatic context management

## 📁 Project Structure

```
├── backend/
│   ├── app/
│   │   ├── agent/
│   │   │   ├── main_agent.py          # LangGraph agent definition
│   │   │   ├── tool_agents.py         # Agent tools implementation
│   │   │   ├── llm.py                 # LLM configurations
│   │   │   └── document_loader.py     # Document processing utilities
│   │   ├── api/
│   │   │   └── v1/
│   │   │       └── agent.py           # FastAPI streaming endpoints
│   │   ├── core/
│   │   │   ├── config.py              # Application configuration
│   │   │   └── logging_config.py      # Logging setup
│   │   ├── database/
│   │   │   └── connection.py          # Database connections
│   │   └── main.py                    # FastAPI application entry point
│   ├── documents/                     # Static document serving
│   ├── data/                          # Sample data and ingestion files
│   ├── run_ingestion.py               # Document ingestion pipeline
│   └── requirements.txt               # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat.jsx               # Main chat interface
│   │   │   └── Auth.jsx               # Authentication component
│   │   ├── App.jsx                    # Main application component
│   │   └── main.jsx                   # React entry point
│   ├── package.json                   # Node.js dependencies
│   └── vite.config.js                 # Vite configuration with proxy
└── README.md
```

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL database
- OpenAI API key

### Backend Setup

1. **Clone and navigate to backend**:
   ```bash
   cd backend
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment configuration**:
   Create `.env` file in the backend directory:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   DATABASE_URL=postgresql://username:password@localhost:5432/lyfegen_db
   API_KEY=lyfegen-ai-task-2024
   ```

5. **Database setup**:
   - Create PostgreSQL database
   - Run ingestion pipeline to populate data:
   ```bash
   python run_ingestion.py
   ```

6. **Start backend server**:
   ```bash
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. **Navigate to frontend**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start development server**:
   ```bash
   npm run dev
   ```

4. **Access application**:
   Open http://localhost:5173 in your browser

## 🔑 Authentication

The application uses API key authentication:
- Default API key: `lyfegen-ai-task-2024`
- Keys are stored in browser localStorage
- Authentication persists across browser sessions

## 💬 Usage

### Basic Chat
1. Enter the API key when prompted
2. Ask questions about the document knowledge base
3. View real-time streaming responses with source citations

### File Upload
1. Click the paperclip icon to upload a file
2. Supported formats: PDF, DOCX, TXT
3. Ask questions about the uploaded document
4. The agent will prioritize uploaded content for relevant queries

### Example Queries
- "What is the immunotherapy program about?"
- "What happens to non-responders in the treatment?"
- "Can you summarize the key findings from this document?"

## 🔧 API Endpoints

### POST `/v1/query-stream`
Streaming chat endpoint with file upload support.

**Form Data:**
- `session_id`: Unique session identifier
- `query`: User's question
- `api_key`: Authentication key
- `file`: Optional file upload

**Response:** Server-Sent Events stream with:
- Status updates: `{"type": "status", "content": "Running: tool_name"}`
- Final response: `{"type": "final_response", "content": "answer", "sources": [...]}`
- Errors: `{"type": "error", "content": "error_message"}`

### GET `/documents/{filename}`
Serves static documents for source citations.

## 🧠 Agent Architecture

The LangGraph agent follows this workflow:

1. **Summarization**: Summarizes conversation history for context
2. **Context Preparation**: Includes uploaded file content if available
3. **Tool Selection**: Chooses appropriate tools based on the query
4. **Tool Execution**: Runs selected tools (retrieval, SQL queries, etc.)
5. **Response Generation**: Creates final human-readable response
6. **Source Attribution**: Adds document links and citations

### Available Tools
- `retrieve_relevant_chunks`: Semantic search across document chunks
- `retrieve_full_documents`: Access complete documents
- `query_structured_data`: Natural language to SQL conversion
- `summarize_discussion`: Conversation context management

## 🎨 Frontend Features

### Real-time Chat Interface
- Streaming status updates during agent processing
- Markdown rendering for formatted responses
- File upload with drag-and-drop support
- Responsive design for mobile and desktop

### Authentication Flow
- Secure API key entry with password masking
- Persistent authentication across sessions
- Clean logout functionality

### Visual Indicators
- 🤔 Status updates during processing
- ✅ Final responses with source links
- ❌ Error handling with user-friendly messages
- 📎 File attachment indicators

## 🔍 Troubleshooting

### Common Issues

**Backend won't start:**
- Check Python version (3.11+ required)
- Verify all dependencies installed
- Ensure database connection is configured
- Check OpenAI API key is valid

**Frontend connection issues:**
- Verify backend is running on port 8000
- Check proxy configuration in `vite.config.js`
- Ensure API key matches backend configuration

**File upload not working:**
- Check file format (PDF, DOCX, TXT only)
- Verify file size is reasonable
- Check backend logs for processing errors

**Streaming not displaying:**
- Check browser console for JavaScript errors
- Verify Server-Sent Events are not blocked
- Check network tab for proper response format

## 📝 Development Notes

### Key Technical Decisions
- **Server-Sent Events** for real-time streaming instead of WebSockets
- **FormData** for file uploads with API key authentication
- **LangGraph** for complex agent workflows with tool orchestration
- **Vite proxy** for development CORS handling
- **In-memory conversation storage** for session management

### Performance Considerations
- Document chunking for efficient retrieval
- Vector similarity search for semantic matching
- Conversation summarization to manage context length
- Streaming responses to improve perceived performance

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is part of the Lyfegen AI task and is intended for evaluation purposes. 