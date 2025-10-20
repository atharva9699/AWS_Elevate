import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { v4 as uuidv4 } from 'uuid';
import API_CONFIG from '../config';
import '../styles/ChatInterface.css';
import axios from 'axios';

// Check for browser's Speech Recognition API
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState('');
  const messagesEndRef = useRef(null);

  // --- State for voice input ---
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef(null);

  // --- State for polling ---
  const [isPolling, setIsPolling] = useState(false);
  const [lastCreatedAt, setLastCreatedAt] = useState(null);
  const [receivedFinalResponse, setReceivedFinalResponse] = useState(false);
  const pollingIntervalRef = useRef(null);

  const suggestions = [
    "My username is Charles, tell me about my recommended cert.",
    "What is the price of AWS Cloud Practitioner?",
    "Test my knowledge on my cert.",
    "I want study material on CCP."
  ];

  // Setup Speech Recognition on component mount
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
        .map(result => result[0])
        .map(result => result.transcript)
        .join('');
      setInputValue(transcript);
    };

    recognition.onerror = (event) => {
      console.error("Speech recognition error:", event.error);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;
  }, []);

  useEffect(() => {
    setSessionId(`session-${Date.now()}`);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Polling function to fetch messages
  const pollMessages = async () => {
    try {
      const params = new URLSearchParams({
        //add sessionId if needed
        session_id: sessionId,
        limit: '20'
      });

      console.log('Polling messages with lastCreatedAt:', lastCreatedAt);
      if (lastCreatedAt) {
        params.append('since_created_at', lastCreatedAt);
      }

      const response = await axios.get(
        `${API_CONFIG.API_URL}/messages?${params.toString()}`,
        {
          headers: {
            'x-api-key': API_CONFIG.API_KEY
          }
        }
      );

      const newMessages = response.data.messages || [];

      if (newMessages.length > 0) {
        let hasFinalResponse = false;

        // Add bot messages to the chat
        newMessages.forEach((msg) => {
          // Strip away <sources> tag and everything after it
          const cleanedMessageContent = msg.message_content.split('<sources>')[0].trim();

          const botMessage = {
            id: uuidv4(),
            text: cleanedMessageContent,
            sender: 'bot',
            messageType: msg.message_type,
            timestamp: msg.created_at
          };
          setMessages((prev) => [...prev, botMessage]);

          // Check if this message is a FINAL_RESPONSE
          if (msg.message_type === 'FINAL_RESPONSE') {
            hasFinalResponse = true;
          }
        });

        // Update lastCreatedAt to the latest message's timestamp
        const latestTimestamp = newMessages[0].created_at;
        console.log('Updating lastCreatedAt to:', latestTimestamp);
        setLastCreatedAt(latestTimestamp);

        // If we received a FINAL_RESPONSE, stop polling
        if (hasFinalResponse) {
          console.log('FINAL_RESPONSE received, stopping polling');
          setReceivedFinalResponse(true);
          stopPolling();
        }
      }
    } catch (error) {
      console.error('Error polling messages:', error);
    }
  };

  // Start polling after chat message is sent
  const startPolling = () => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }

    setIsPolling(true);
    setReceivedFinalResponse(false);
    pollingIntervalRef.current = setInterval(() => {
      pollMessages();
    }, 7000); // Poll every 7 seconds
  };

  // Stop polling
  const stopPolling = () => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
    setIsPolling(false);
  };

  // Cleanup polling on component unmount
  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, []);

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
      // Fire and forget - don't wait for response
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

      // Reset final response flag and start polling
      setReceivedFinalResponse(false);
      if (!pollingIntervalRef.current) {
        startPolling();
      }
    } finally {
      setLoading(false);
    }
  };

  const handleVoiceInput = () => {
    if (!recognitionRef.current) return;

    if (isListening) {
      recognitionRef.current.stop();
    } else {
      recognitionRef.current.start();
    }
    setIsListening(!isListening);
  };

  const handleSuggestionClick = (suggestion) => {
    sendMessage(null, suggestion);
  };

  const clearChat = () => {
    stopPolling();
    setMessages([]);
    // Add a 4 digit random number to sessionId for uniqueness
    setSessionId(`session-${Date.now()}-${Math.floor(1000 + Math.random() * 9000)}`);
    setLastCreatedAt(null);
    setReceivedFinalResponse(false);
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h2>AWS Elevate (v1.3)</h2>
        <div>
          {isPolling && <span className="polling-indicator">⏱ Polling...</span>}
          <button className="btn btn-sm btn-outline-secondary" onClick={clearChat}>
            Clear Chat
          </button>
        </div>
      </div>

      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="welcome-state">
            <h1>Welcome to AWS Certification Coach!</h1>
            <p className="text-muted">What's your name and how can I help you?</p>
          </div>
        ) : (
          messages.map((message) => (
            <div key={message.id} className={`message ${message.sender} ${message.messageType === 'FINAL_RESPONSE' ? 'final-response' : ''}`}>
              <div className={`message-content message-${message.sender} ${message.messageType === 'FINAL_RESPONSE' ? 'final-response-content' : ''}`}>
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