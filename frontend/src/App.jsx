import React, { useState, useEffect } from "react";
import "./App.css";

const LoadingScreen = () => (
  <div className="loading-container">
    <div className="jarvis-core">
      <div className="ring"></div>
      <div className="inner-core"></div>
      <div className="pulse"></div>
    </div>
    <div className="loading-text">
      <h1>🌟 Booting up J.A.R.V.I.S...</h1>
      <p>
        Waking your AI companion • Sharpening its mind • Setting up for smart
        discovery... ⚡
      </p>
    </div>
  </div>
);

export default function App() {
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [typedResponse, setTypedResponse] = useState("");
  const [listening, setListening] = useState(false);
  const [recognition, setRecognition] = useState(null);
  const [typing, setTyping] = useState(false);

  // New states for backend interaction
  const [fetchingData, setFetchingData] = useState(false);
  const [response, setResponse] = useState("");

  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 2500);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (!("webkitSpeechRecognition" in window)) return;

    const recog = new window.webkitSpeechRecognition();
    recog.lang = "en-US";
    recog.continuous = false;
    recog.interimResults = false;

    recog.onstart = () => {
      setListening(true);
      setTypedResponse("🎤 Jarvis is listening...");
      setQuery("");
    };

    recog.onresult = (event) => {
      const transcript = event.results[0][0].transcript.trim();
      setQuery(transcript);
      handleResponse(transcript);
    };

    recog.onerror = () => {
      setTypedResponse("⚠️ Could not detect clear speech. Try again.");
      setListening(false);
    };

    recog.onend = () => setListening(false);
    setRecognition(recog);
  }, []);

  const handleMicClick = () => {
    if (!recognition) return;
    if (listening) recognition.stop();
    else {
      setTypedResponse("");
      setQuery("");
      recognition.start();
    }
  };

  const showTypingEffect = (text) => {
    setTypedResponse("");
    setTyping(true);
    let i = 0;
    const interval = setInterval(() => {
      setTypedResponse((prev) => prev + text.charAt(i));
      i++;
      if (i >= text.length) {
        clearInterval(interval);
        setTyping(false);
      }
    }, 25);
  };

  // When backend response state updates, play typing effect
  useEffect(() => {
    if (response && response.trim()) {
      showTypingEffect(response);
    }
  }, [response]);

  const handleResponse = (message) => {
    if (!message.trim()) return;
    setTypedResponse("");
    setTyping(true);

    // Simulate processing delay then call backend
    setTimeout(() => {
      // local immediate feedback (keeps previous simulated message)
      showTypingEffect(
        `🧠 Jarvis received: "${message}" — querying AI core...`
      );

      // send to backend after a short pause so the above message is visible
      sendToBackend(message);
    }, 800);
  };

  // New function to send query to backend (as requested)
  const sendToBackend = async (message) => {
    try {
      setFetchingData(true);
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: message }),
      });

      const data = await res.json();
      setResponse(data.answer);
    } catch (error) {
      setResponse("⚠️ Connection lost — please check your backend server.");
    } finally {
      setFetchingData(false);
    }
  };

  const handleTyping = (e) => setQuery(e.target.value);

  const handleKeyDown = (e) => {
    if (e.key === "Enter") handleResponse(query);
  };

  if (loading) return <LoadingScreen />;

  return (
    <div className="jarvis-layout">
      <div className="jarvis-logo">J.A.R.V.I.S.</div>

      <div className="jarvis-container">
        <h1 className="title">Ask Anything</h1>

        {listening && (
          <div className="listening-banner">
            🎧 Jarvis is Listening...
            <div className="voice-bars">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}

        <div className="input-wrapper">
          <input
            type="text"
            className="input-box"
            placeholder="Type or speak your question..."
            value={query}
            onChange={handleTyping}
            onKeyDown={handleKeyDown}
            disabled={listening}
          />
        </div>

        <div className="button-group">
          <button
            className={`mic-btn ${listening ? "listening" : ""}`}
            onClick={handleMicClick}
          >
            🎙
          </button>
          <button onClick={() => handleResponse(query)} className="exec-btn">
            Execute
          </button>
        </div>

        <div className="response-box scrollable-response">
          <h3>AI Response</h3>

          {(typing || fetchingData) && (
            <div className="ai-loading-indicator">
              <div className="ai-ring"></div>
              <div className="ai-ring-glow"></div>
              <p className="ai-loading-text">
                {fetchingData ? "Fetching from AI core..." : "Analyzing..."}
              </p>
            </div>
          )}

          <div className="response-content">
            <p>{typedResponse}</p>
          </div>
        </div>
      </div>
    </div>
  );
}