import React, { useState, useEffect, useRef } from 'react';
import { Paperclip, Send, Bot, User, Settings, Check, X, File as FileIcon, Loader, Star, Copy, ThumbsUp, ThumbsDown } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { v4 as uuidv4 } from 'uuid';

const Chat = ({ apiKey, onLogout }) => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [sessionId, setSessionId] = useState(() => uuidv4());
    const [file, setFile] = useState(null);
    const [status, setStatus] = useState('idle');
    const messagesEndRef = useRef(null);
    const fileInputRef = useRef(null);
    const [fileName, setFileName] = useState('');

    useEffect(() => {
        setMessages([
            {
                sender: 'bot',
                text: "Hello! I'm the Lyfegen Document Intelligence agent. You can ask me questions about the documents in my knowledge base, or upload a PDF to ask questions about a specific document.",
                sources: [],
                isFinal: true
            }
        ]);
    }, []);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);
    
    const handleFileChange = (e) => {
     const file = e.target.files[0];
     if (file) {
        setFile(file);
        setFileName(file.name);
     }
   };
 
   const removeFile = () => {
     setFile(null);
     setFileName('');
     fileInputRef.current.value = null;
   }

    const handleSendMessage = async () => {
        if (input.trim() === '' && !file) return;

        const userMessage = { sender: 'user', text: input, file: file?.name };
        const currentFile = file;
        
        setMessages(prev => [...prev, userMessage, { sender: 'bot', text: 'Thinking...', sources: [], isFinal: false }]);
        setStatus('thinking');
        setInput('');
        setFile(null);
        setFileName('');
        if (fileInputRef.current) {
            fileInputRef.current.value = null;
        }

        const formData = new FormData();
        formData.append('session_id', sessionId);
        formData.append('query', input);
        formData.append('api_key', apiKey);
        if (currentFile) {
            formData.append('file', currentFile);
        }

        // Debug logging
        console.log('=== SENDING REQUEST ===');
        console.log('Session ID:', sessionId);
        console.log('Query:', input);
        console.log('API Key:', apiKey);
        console.log('File:', currentFile?.name || 'None');
        console.log('FormData entries:');
        for (let [key, value] of formData.entries()) {
            console.log(`  ${key}:`, value);
        }

        try {
            console.log('Making request to /v1/query-stream...');
            const response = await fetch('/v1/query-stream', {
                method: 'POST',
                body: formData,
            });

            console.log('Response status:', response.status);
            console.log('Response headers:', Object.fromEntries(response.headers.entries()));

            if (!response.ok) {
                console.log('Response not OK, trying to parse error...');
                const errorData = await response.json().catch(() => ({ detail: 'Unknown server error' }));
                console.log('Error data:', errorData);
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) {
                    console.log('Stream ended');
                    break;
                }

                buffer += decoder.decode(value, { stream: true });
                const parts = buffer.split('\n\n');
                buffer = parts.pop() || '';

                for (const part of parts) {
                    if (!part.startsWith('data: ')) continue;
                    
                    const jsonStr = part.substring(6);
                    if (!jsonStr) continue;

                    console.log('Raw JSON string:', jsonStr);

                    try {
                        const data = JSON.parse(jsonStr);
                        console.log('Parsed stream data:', data);
                        console.log('Data type:', data.type);
                        console.log('Data content:', data.content);
                        
                        setMessages(prev => {
                            const newMessages = [...prev];
                            const lastIndex = newMessages.length - 1;
                            
                            if (data.type === 'status') {
                                newMessages[lastIndex] = {
                                    ...newMessages[lastIndex],
                                    text: `🤔 ${data.content}`,
                                    isFinal: false
                                };
                            } else if (data.type === 'final_response') {
                                newMessages[lastIndex] = {
                                    ...newMessages[lastIndex],
                                    text: data.content,
                                    sources: data.sources || [],
                                    isFinal: true
                                };
                                setStatus('idle');
                            } else if (data.type === 'error') {
                                newMessages[lastIndex] = {
                                    ...newMessages[lastIndex],
                                    text: `❌ Error: ${data.content}`,
                                    isFinal: true
                                };
                                setStatus('idle');
                            }
                            
                            return newMessages;
                        });
                    } catch (e) {
                        console.error("Failed to parse stream data chunk:", jsonStr, e);
                    }
                }
            }
        } catch (error) {
            console.error("Failed to send message:", error);
            const errorMessage = error.response?.data?.detail || error.message || "An unknown error occurred.";
            setMessages(prev => prev.map((msg, index) => {
                if (index !== prev.length - 1) return msg;
                return { 
                    ...msg, 
                    text: `Failed to get response: ${errorMessage}`, 
                    isFinal: true 
                };
            }));
            setStatus('idle');
        } finally {
            setStatus('idle');
            // Remove the automatic "Finished." text since we now handle final responses properly
        }
    };

    return (
        <div className="flex flex-col h-screen bg-gray-900 text-white font-sans">
            {/* Header */}
            <header className="flex-shrink-0 flex justify-between items-center p-4 border-b border-gray-700/50 shadow-md">
                <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-indigo-600 rounded-full flex items-center justify-center text-white font-bold text-xl">
                        L
                    </div>
                    <h1 className="text-xl font-bold text-gray-200">Lyfegen AI</h1>
                </div>
                <button onClick={onLogout} className="p-2 rounded-full hover:bg-gray-700/50 transition-colors">
                    <Settings className="h-6 w-6 text-gray-400" />
                </button>
            </header>

            {/* Chat Area */}
            <main className="flex-1 overflow-y-auto p-6 space-y-8">
                {messages.map((msg, index) => (
                    <Message key={index} sender={msg.sender} text={msg.text} sources={msg.sources} isFinal={msg.isFinal} />
                ))}
                <div ref={messagesEndRef} />
            </main>

            {/* Input Area */}
            <footer className="flex-shrink-0 p-4 border-t border-gray-700/50 shadow-lg bg-gray-800/70 backdrop-blur-md">
                {fileName && (
                    <div className="mb-2 flex items-center gap-2 text-sm bg-gray-700/50 rounded-lg p-2 max-w-xs">
                        <FileIcon className="h-4 w-4 text-gray-400 flex-shrink-0" />
                        <span className="text-white truncate" title={fileName}>{fileName}</span>
                        <button onClick={removeFile} className="ml-auto text-gray-400 hover:text-white flex-shrink-0">
                            <X className="h-4 w-4" />
                        </button>
                    </div>
                )}
                <form onSubmit={(e) => { e.preventDefault(); handleSendMessage(); }} className="flex items-center gap-3">
                    <label htmlFor="file-upload" className="flex-shrink-0 cursor-pointer text-gray-400 hover:text-indigo-400 transition-colors">
                        <Paperclip className="h-6 w-6" />
                    </label>
                    <input id="file-upload" type="file" ref={fileInputRef} onChange={handleFileChange} className="hidden" />
                    
                    <textarea
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Ask a question about your documents..."
                        className="flex-1 bg-gray-700/50 border border-transparent rounded-lg p-3 pr-12 resize-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all text-white placeholder-gray-400"
                        rows="1"
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                handleSendMessage();
                            }
                        }}
                    />
                    <button
                        type="submit"
                        className="flex-shrink-0 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-900/50 disabled:cursor-not-allowed text-white font-bold p-2.5 rounded-full transition-colors"
                        disabled={status === 'thinking' || (!input.trim() && !file)}
                    >
                        <Send className="h-5 w-5" />
                    </button>
                </form>
            </footer>
        </div>
    );
};

const Message = ({ sender, text, sources, isFinal }) => {
    return (
        <div className={`flex items-start gap-4 ${sender === 'user' ? 'justify-end' : ''}`}>
             {sender === 'bot' && (
                <div className="flex-shrink-0 h-10 w-10 rounded-full bg-gray-700 flex items-center justify-center">
                    <Bot className="h-7 w-7 text-indigo-400" />
                </div>
            )}
            <div className={`w-full max-w-2xl px-5 py-4 rounded-2xl shadow-md ${sender === 'bot' ? 'bg-gray-800' : 'bg-blue-600'}`}>
                <div className="prose prose-invert max-w-none text-white">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>
                </div>
                {!isFinal && sender === 'bot' && (
                    <div className="flex items-center justify-center mt-3">
                         <Loader className="h-5 w-5 animate-spin text-gray-400" />
                    </div>
                )}
                {sources && sources.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-gray-700/50">
                        <h4 className="text-sm font-semibold text-gray-400 mb-2">Sources:</h4>
                        <div className="space-y-2">
                            {sources.map((source, i) => <Source key={i} source={source} />)}
                        </div>
                    </div>
                )}
            </div>
             {sender === 'user' && (
                <div className="flex-shrink-0 h-10 w-10 rounded-full bg-gray-700 flex items-center justify-center">
                    <User className="h-7 w-7 text-blue-400" />
                </div>
            )}
        </div>
    );
};

const Source = ({ source }) => (
    <div className="bg-gray-700/50 p-3 rounded-lg text-xs transition-colors hover:bg-gray-700">
        <div className="font-mono text-indigo-300 truncate mb-1" title={source.metadata.path || 'Unknown Document'}>
            <FileIcon className="h-4 w-4 inline-block mr-2" />
            {source.metadata.path ? source.metadata.path.split(/[\\/]/).pop() : 'Unknown Document'}
        </div>
        <p className="text-gray-300 line-clamp-2">{source.page_content}</p>
    </div>
);

export default Chat;