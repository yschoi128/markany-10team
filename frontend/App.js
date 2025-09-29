import React, { useState, useRef } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [menuOpen, setMenuOpen] = useState(false);
  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);

  const sendMessage = () => {
    if (!input.trim()) return;
    
    setMessages([...messages, 
      { text: input, sender: 'user' },
      { text: '안녕하세요! 어떻게 도와드릴까요?', sender: 'ai' }
    ]);
    setInput('');
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file && file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setMessages(prev => [...prev, 
          { text: '', image: e.target.result, sender: 'user' },
          { text: '이미지를 확인했습니다!', sender: 'ai' }
        ]);
      };
      reader.readAsDataURL(file);
    }
  };

  const takePhoto = () => {
    cameraInputRef.current.click();
    setMenuOpen(false);
  };

  const uploadPhoto = () => {
    fileInputRef.current.click();
    setMenuOpen(false);
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>AI PT쌤</h1>
        <button 
          className="hamburger-btn"
          onClick={() => setMenuOpen(!menuOpen)}
        >
          ☰
        </button>
        {menuOpen && (
          <div className="menu-dropdown">
            <div onClick={takePhoto}>📷 사진 촬영</div>
            <div onClick={uploadPhoto}>📁 사진 업로드</div>
            <div>새 채팅</div>
            <div>설정</div>
            <div>도움말</div>
          </div>
        )}
      </div>
      
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.sender}`}>
            <div className="message-content">
              {msg.image && <img src={msg.image} alt="업로드된 이미지" />}
              {msg.text}
            </div>
          </div>
        ))}
      </div>
      
      <div className="input-container">
        <div className="input-wrapper">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="오늘 어떤 도움을 드릴까요?"
          />
          <button onClick={sendMessage} className="send-btn">↑</button>
        </div>
      </div>
      
      <input
        ref={cameraInputRef}
        type="file"
        accept="image/*"
        capture="environment"
        onChange={handleFileUpload}
        style={{display: 'none'}}
      />
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileUpload}
        style={{display: 'none'}}
      />
    </div>
  );
}

export default App;
