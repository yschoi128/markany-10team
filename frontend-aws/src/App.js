import React, { useState, useRef, useEffect } from 'react';
import './App.css';

const API_BASE_URL = 'http://3.36.46.71:8001';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedImage, setSelectedImage] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [showSettings, setShowSettings] = useState(false);
  const [userInfo, setUserInfo] = useState({
    name: '',
    age: '',
    gender: '',
    height: '',
    weight: '',
    goal: 'health_maintenance'
  });
  
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const sendMessage = async () => {
    if ((!input.trim() && !selectedImage) || isLoading) return;
    
    const userMessage = { 
      type: 'user', 
      content: input,
      image: selectedImage,
      timestamp: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setSelectedImage(null);
    setSelectedFile(null);
    setIsLoading(true);
    
    try {
      const formData = new FormData();
      formData.append('user_id', 'user_123');
      formData.append('message', input);
      
      if (selectedFile) {
        formData.append('image', selectedFile);
      }
      
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        body: formData
      });
      
      const data = await response.json();
      
      if (data.success && data.data.success) {
        const aiMessage = {
          type: 'ai',
          content: data.data.response,
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, aiMessage]);
      } else {
        throw new Error(data.data?.error || '응답 처리 중 오류가 발생했습니다.');
      }
    } catch (error) {
      console.error('Error:', error);
      const errorMessage = {
        type: 'ai',
        content: '죄송합니다. 오류가 발생했습니다: ' + error.message,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const createUserProfile = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/mcp/tools/call`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: 'create_user_profile',
          arguments: {
            user_id: 'user_123',
            name: userInfo.name,
            age: parseInt(userInfo.age),
            gender: userInfo.gender,
            height: parseFloat(userInfo.height),
            weight: parseFloat(userInfo.weight),
            health_goal: userInfo.goal
          }
        })
      });
      
      const data = await response.json();
      const result = JSON.parse(data.content[0].text);
      
      if (result.success) {
        alert(`프로필이 생성되었습니다!\nBMI: ${result.bmi}\n목표 칼로리: ${result.target_calories}kcal`);
        setShowSettings(false);
      } else {
        alert('프로필 생성에 실패했습니다: ' + result.error);
      }
    } catch (error) {
      console.error('Error creating profile:', error);
      alert('프로필 생성 중 오류가 발생했습니다.');
    }
  };

  const handleImageSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
      const reader = new FileReader();
      reader.onload = (e) => {
        setSelectedImage(e.target.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const removeImage = () => {
    setSelectedImage(null);
    setSelectedFile(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="App">
      <div className="chat-container">
        <div className="chat-header">
          <h1>🤖 AI 식단 코치</h1>
          <button 
            className="settings-btn" 
            onClick={() => setShowSettings(true)}
          >
            ⚙️
          </button>
        </div>
        
        <div className="messages">
          {messages.map((message, index) => (
            <div key={index} className={`message ${message.type}`}>
              <div className="message-content">
                {message.content}
                {message.image && (
                  <img src={message.image} alt="Uploaded" style={{maxWidth: '300px', borderRadius: '8px'}} />
                )}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="message ai">
              <div className="message-content">AI가 응답을 생성하고 있습니다...</div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        
        <div className="input-container">
          {selectedImage && (
            <div className="image-preview">
              <img src={selectedImage} alt="Preview" style={{maxWidth: '200px', borderRadius: '8px'}} />
              <button onClick={removeImage} style={{marginLeft: '10px'}}>❌</button>
            </div>
          )}
          
          <div className="input-wrapper">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="메시지를 입력하세요..."
              disabled={isLoading}
            />
            
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleImageSelect}
              accept="image/*"
              style={{ display: 'none' }}
            />
            
            <button onClick={() => fileInputRef.current?.click()}>📎</button>
            <button onClick={sendMessage} disabled={isLoading || (!input.trim() && !selectedImage)}>
              ➤
            </button>
          </div>
        </div>
        
        {showSettings && (
          <div className="settings-modal">
            <div className="settings-content">
              <h2>프로필 설정</h2>
              
              <input
                type="text"
                placeholder="이름"
                value={userInfo.name}
                onChange={(e) => setUserInfo({...userInfo, name: e.target.value})}
              />
              
              <input
                type="number"
                placeholder="나이"
                value={userInfo.age}
                onChange={(e) => setUserInfo({...userInfo, age: e.target.value})}
              />
              
              <select
                value={userInfo.gender}
                onChange={(e) => setUserInfo({...userInfo, gender: e.target.value})}
              >
                <option value="">성별 선택</option>
                <option value="male">남성</option>
                <option value="female">여성</option>
              </select>
              
              <input
                type="number"
                placeholder="키 (cm)"
                value={userInfo.height}
                onChange={(e) => setUserInfo({...userInfo, height: e.target.value})}
              />
              
              <input
                type="number"
                placeholder="체중 (kg)"
                value={userInfo.weight}
                onChange={(e) => setUserInfo({...userInfo, weight: e.target.value})}
              />
              
              <select
                value={userInfo.goal}
                onChange={(e) => setUserInfo({...userInfo, goal: e.target.value})}
              >
                <option value="health_maintenance">건강 유지</option>
                <option value="weight_loss">체중 감량</option>
                <option value="muscle_gain">근육 증가</option>
                <option value="body_profile">체형 관리</option>
              </select>
              
              <div className="settings-buttons">
                <button onClick={() => setShowSettings(false)}>취소</button>
                <button onClick={createUserProfile}>저장</button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;