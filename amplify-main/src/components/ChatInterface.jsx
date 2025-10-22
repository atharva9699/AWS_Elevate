import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { v4 as uuidv4 } from 'uuid';
import API_CONFIG from '../config';
import '../styles/ChatInterface.css';
import axios from 'axios';

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState('');
  const [showDetails, setShowDetails] = useState(false); // 🔹 New state
  const messagesEndRef = useRef(null);

  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef(null);

  const [isPolling, setIsPolling] = useState(false);
  const [lastCreatedAt, setLastCreatedAt] = useState(null);
  const [receivedFinalResponse, setReceivedFinalResponse] = useState(false);
  const pollingIntervalRef = useRef(null);

  const suggestions = [
    "My username is Charles, tell me about my recommended cert.",
    "I want to become a hands-on GenAI engineer, which cert should I pursue?",
    "Teach me the basics of S3 for beginners.",
    "My username is Ansley, quiz me on IAM policies with 2 questions."
    
  ];

  // --- Speech Recognition setup ---
  useEffect(() => {
    if (!SpeechRecognition) {
      console.log("Speech recognition not supported in this browser.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map(result => result[0].transcript)
        .join('');
      setInputValue(transcript);
    };

    recognition.onerror = (event) => {
      console.error("Speech recognition error:", event.error);
    };

    recognition.onend = () => setIsListening(false);

    recognitionRef.current = recognition;
  }, []);

  useEffect(() => {
    setSessionId(`session-${Date.now()}`);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // --- Polling logic ---
  const pollMessages = async () => {
    try {
      const params = new URLSearchParams({
        session_id: sessionId,
        limit: '20'
      });

      if (lastCreatedAt) params.append('since_created_at', lastCreatedAt);

      const response = await axios.get(`${API_CONFIG.API_URL}/messages?${params.toString()}`, {
        headers: { 'x-api-key': API_CONFIG.API_KEY }
      });

      const newMessages = response.data.messages || [];

      if (newMessages.length > 0) {
        let hasFinalResponse = false;

        newMessages.forEach((msg) => {
          const cleanedMessageContent = msg.message_content.split('<sources>')[0].replace(/\n{2,}/g, '\n').trim();

          const botMessage = {
            id: uuidv4(),
            text: cleanedMessageContent,
            sender: 'bot',
            messageType: msg.message_type,
            timestamp: msg.created_at,
            showToUser: msg.show_to_user // 🔹 Capture show_to_user flag
          };
          setMessages((prev) => [...prev, botMessage]);

          if (msg.message_type === 'FINAL_RESPONSE') hasFinalResponse = true;
        });

        const latestTimestamp = newMessages[0].created_at;
        setLastCreatedAt(latestTimestamp);

        if (hasFinalResponse) {
          setReceivedFinalResponse(true);
          stopPolling();
        }
      }
    } catch (error) {
      console.error('Error polling messages:', error);
    }
  };

  const startPolling = () => {
    if (pollingIntervalRef.current) clearInterval(pollingIntervalRef.current);

    setIsPolling(true);
    setReceivedFinalResponse(false);
    pollingIntervalRef.current = setInterval(pollMessages, 3000);
  };

  const stopPolling = () => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
    setIsPolling(false);
  };

  useEffect(() => stopPolling, []);

  const sendMessage = async (e, messageText) => {
    if (e) e.preventDefault();

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    }

    const messageToSend = messageText || inputValue.trim();
    if (!messageToSend) return;

    const userMessage = { id: uuidv4(), text: messageToSend, sender: 'user' };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setLoading(true);

    try {
      axios.post(
        API_CONFIG.API_URL + "/chat",
        { message: messageToSend, sessionId: sessionId },
        {
          headers: {
            'Content-Type': 'application/json',
            'x-api-key': API_CONFIG.API_KEY
          },
          timeout: 120000
        }
      ).catch((error) => {
        console.error('Error sending message:', error);
        const errorMessage = {
          id: uuidv4(),
          text: `Error sending message: ${error.message}`,
          sender: 'error'
        };
        setMessages((prev) => [...prev, errorMessage]);
      });

      setReceivedFinalResponse(false);
      if (!pollingIntervalRef.current) startPolling();
    } finally {
      setLoading(false);
    }
  };

  const handleVoiceInput = () => {
    if (!recognitionRef.current) return;
    if (isListening) recognitionRef.current.stop();
    else recognitionRef.current.start();
    setIsListening(!isListening);
  };

  const handleSuggestionClick = (suggestion) => {
    sendMessage(null, suggestion);
  };

  const clearChat = () => {
    stopPolling();
    setMessages([]);
    setSessionId(`session-${Date.now()}-${Math.floor(1000 + Math.random() * 9000)}`);
    setLastCreatedAt(null);
    setReceivedFinalResponse(false);
  };

  // 🔹 Filter messages based on showDetails toggle
  const visibleMessages = messages.filter(
    (msg) => showDetails || msg.showToUser !== false
  );

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h2>AWS Elevate (v1.3)</h2>
        <div className="header-buttons">
          {isPolling && <span className="polling-indicator">⏱ Polling...</span>}
          <button className="btn btn-sm btn-outline-secondary" onClick={clearChat}>
            Clear Chat
          </button>
          {/* 🔹 New toggle */}
          <label style={{ marginLeft: '10px' }}>
            <input
              type="checkbox"
              checked={showDetails}
              onChange={() => setShowDetails(!showDetails)}
            />{' '}
            Show Details
          </label>
        </div>
      </div>

      <div className="chat-messages">
        {visibleMessages.length === 0 ? (
          <div className="welcome-state">
            <h1>Welcome to AWS Certification Coach!</h1>
            <p className="text-muted">What's your name and how can I help you?</p>
          </div>
        ) : (
          visibleMessages.map((message) => (
            <div
              key={message.id}
              className={`message ${message.sender} ${
                message.messageType === 'FINAL_RESPONSE' ? 'final-response' : ''
              }`}
            >
              <div
                className={`message-content message-${message.sender} ${
                  message.messageType === 'FINAL_RESPONSE'
                    ? 'final-response-content'
                    : ''
                }`}
              >
                <ReactMarkdown>{message.text}</ReactMarkdown>
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={sendMessage} className="chat-input-form">
        <div className="input-group">
          <input
            type="text"
            className="form-control"
            placeholder={isListening ? "Listening..." : "Ask me something..."}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            disabled={loading}
          />

          {SpeechRecognition && (
            <button
              type="button"
              className={`btn voice-btn ${isListening ? 'listening' : ''}`}
              onClick={handleVoiceInput}
            >
              🎤
            </button>
          )}

          <button
            className="btn btn-primary"
            type="submit"
            disabled={loading || !inputValue.trim()}
          >
            {loading ? '...' : 'Send'}
          </button>
        </div>
      </form>

      {messages.length === 0 && (
        <div className="suggestion-buttons">
          {suggestions.map((text, index) => (
            <button key={index} className="suggestion-btn" onClick={() => handleSuggestionClick(text)}>
              {text}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default ChatInterface;
