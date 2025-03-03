import React, { useState } from 'react'

// The VITE_DAILY_ROOM_URL variable is exposed by Vite from your environment (.env)
const dailyRoomUrl = import.meta.env.VITE_DAILY_ROOM_URL

function App() {
  const [isListening, setIsListening] = useState(false)

  // When the user taps the button, we simulate starting the conversation.
  // Actual audio streaming is handled by the hidden Daily iframe.
  const handleButtonClick = () => {
    // Toggle listening state for visual feedback (e.g. animate avatar)
    setIsListening(true)
    // Optionally, you might integrate with Daily's JS SDK here for more control.
    // For the PoC, joining the call via the hidden iframe is enough.
  }

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gray-100">
      <div className="mb-8">
        <img
          src="/src/assets/avatar.png"
          alt="Voice Agent Avatar"
          className={`w-40 h-40 rounded-full shadow-lg transition-all duration-500 ${
            isListening ? 'animate-pulse' : ''
          }`}
        />
      </div>
      <button
        onClick={handleButtonClick}
        className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-full focus:outline-none"
      >
        {isListening ? 'Listening…' : 'Tap to Speak'}
      </button>
      {/* Hidden Daily iframe that joins the call for audio transport */}
      <iframe
        title="daily-call"
        src={dailyRoomUrl}
        allow="camera; microphone; autoplay; encrypted-media"
        style={{ display: 'none' }}
      ></iframe>
    </div>
  )
}

export default App
