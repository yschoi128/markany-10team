import React, { useState, useRef } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [menuOpen, setMenuOpen] = useState(false);
  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);

  const sendMessage = async () => {
    if (!input.trim()) return;
    
    const userMessage = { text: input, sender: 'user' };
    setMessages(prev => [...prev, userMessage]);
    const currentInput = input;
    setInput('');
    
    try {
      const formData = new FormData();
      formData.append('user_id', 'user123');
      formData.append('message', currentInput);
      
      const response = await fetch('http://3.36.46.71:8001/chat', {
        method: 'POST',
        mode: 'cors',
        body: formData
      });
      
      const data = await response.json();
      const aiResponse = data.data?.response || data.data?.message || data.message || '응답을 받을 수 없습니다.';
      setMessages(prev => [...prev, { text: aiResponse, sender: 'ai' }]);
    } catch (error) {
      console.error('API 호출 오류 상세:', {
        message: error.message,
        name: error.name,
        stack: error.stack,
        cause: error.cause
      });
      console.error('전체 에러 객체:', error);
      setMessages(prev => [...prev, { text: `서버 연결 실패: ${error.message}`, sender: 'ai' }]);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (file && file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = async (e) => {
        const imageMessage = { text: '', image: e.target.result, sender: 'user' };
        setMessages(prev => [...prev, imageMessage]);
        
        try {
          const formData = new FormData();
          formData.append('user_id', 'user123');
          formData.append('message', '이미지를 분석해주세요');
          formData.append('image', file);
          
          const response = await fetch('http://3.36.46.71:8001/chat', {
            method: 'POST',
            mode: 'cors',
            body: formData
          });
          
          const data = await response.json();
          const aiResponse = data.data?.response || data.data?.message || data.message || '이미지를 처리했습니다!';
          setMessages(prev => [...prev, { text: aiResponse, sender: 'ai' }]);
        } catch (error) {
          console.error('이미지 업로드 오류 상세:', {
            message: error.message,
            name: error.name,
            stack: error.stack,
            cause: error.cause
          });
          console.error('전체 에러 객체:', error);
          setMessages(prev => [...prev, { text: `이미지 업로드 실패: ${error.message}`, sender: 'ai' }]);
        }
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
