import React, { useState, useRef, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import ChatMessage from './components/ChatMessage';
import ChatInput from './components/ChatInput';

const BACKEND_URL = import.meta.env.DEV ? 'http://127.0.0.1:8000' : '';

function App() {
  const [messages, setMessages] = useState([
    { role: 'system', content: 'Hello! I am your AI Healthcare Assistant. How can I help you today?' }
  ]);
  const chatEndRef = useRef(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (query) => {
    setMessages(prev => [...prev, { role: 'user', content: query }]);
    setMessages(prev => [...prev, { role: 'assistant', isLoading: true }]);

    try {
      const res = await fetch(`${BACKEND_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });
      const data = await res.json();
      
      setMessages(prev => {
        const newMsgs = [...prev];
        newMsgs.pop(); // remove loading message
        if (res.ok) {
          newMsgs.push({
            role: 'assistant',
            content: data.response,
            sosDetails: data.sos_details,
            contextChunks: data.retrieved_context
          });
        } else {
          newMsgs.push({ role: 'assistant', content: 'Error: ' + JSON.stringify(data) });
        }
        return newMsgs;
      });
    } catch (e) {
      setMessages(prev => {
        const newMsgs = [...prev];
        newMsgs.pop();
        newMsgs.push({ role: 'assistant', content: 'Network Error: ' + e.message });
        return newMsgs;
      });
    }
  };

  const handleUpload = async (files) => {
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      setMessages(prev => [...prev, { role: 'assistant', content: `Uploading document: ${file.name}...` }]);
      const formData = new FormData();
      formData.append('file', file);
      
      try {
        const res = await fetch(`${BACKEND_URL}/upload`, { method: 'POST', body: formData });
        if (res.ok) {
          setMessages(prev => [...prev, { role: 'assistant', content: `✅ Successfully processed and embedded ${file.name}.` }]);
        } else {
          setMessages(prev => [...prev, { role: 'assistant', content: `❌ Error uploading ${file.name}.` }]);
        }
      } catch (e) {
        setMessages(prev => [...prev, { role: 'assistant', content: `❌ Network Error uploading ${file.name}.` }]);
      }
    }
  };

  const handleIngest = async (e) => {
    if (e) e.preventDefault();
    setMessages(prev => [...prev, { role: 'assistant', content: 'Triggering base dataset ingestion... This may take a few minutes.' }]);
    
    try {
      const res = await fetch(`${BACKEND_URL}/ingest`, { method: 'POST' });
      const data = await res.json();
      if (res.ok) {
        setMessages(prev => [...prev, { role: 'assistant', content: `✅ Dataset ingested successfully.` }]);
      } else {
        setMessages(prev => [...prev, { role: 'assistant', content: `❌ Ingestion failed: ${JSON.stringify(data)}` }]);
      }
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', content: `❌ Network Error during ingestion.` }]);
    }
  };

  const handleClear = (e) => {
    if (e) e.preventDefault();
    setMessages([{ role: 'system', content: 'Hello! I am your AI Healthcare Assistant. How can I help you today?' }]);
  };

  return (
    <div className="bg-background text-on-background font-body-md text-body-md antialiased overflow-hidden">
      <Sidebar onIngest={handleIngest} onUpload={handleUpload} onClear={handleClear} />
      <Header />
      
      <main className="ml-64 pt-16 h-screen flex flex-col bg-surface-bright">
        <div className="flex-1 overflow-y-auto px-margin-desktop py-xl flex flex-col gap-gutter max-w-4xl mx-auto w-full">
          {messages.map((msg, idx) => (
            <ChatMessage key={idx} message={msg} />
          ))}
          <div ref={chatEndRef} />
        </div>
        
        <ChatInput onSend={handleSend} />
      </main>
    </div>
  );
}

export default App;
