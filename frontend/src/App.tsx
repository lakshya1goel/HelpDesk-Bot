import { useState, useRef, useEffect } from 'react'
import { Room, RoomEvent, RemoteTrack, Track } from 'livekit-client'
import './App.css'

function App() {
  const [isConnected, setIsConnected] = useState(false)
  const [isMicOn, setIsMicOn] = useState(false)
  const [audioLevel, setAudioLevel] = useState(0)
  const [callDuration, setCallDuration] = useState(0)
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected')
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)

  const streamRef = useRef<MediaStream | null>(null)
  const animationRef = useRef<number>(0)
  const callTimerRef = useRef<number | null>(null)
  const speakingTimeoutRef = useRef<number | null>(null)
  const roomRef = useRef<Room | null>(null)

  const formatCallDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  const startCallTimer = () => {
    setCallDuration(0)
    callTimerRef.current = window.setInterval(() => {
      setCallDuration(prev => prev + 1)
    }, 1000)
  }

  const stopCallTimer = () => {
    if (callTimerRef.current) {
      clearInterval(callTimerRef.current)
      callTimerRef.current = null
    }
    setCallDuration(0)
  }

  const requestMicrophoneAccess = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: { 
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        } 
      })
      streamRef.current = stream
      setIsMicOn(true)

      // Create audio context for visual feedback
      const audioContext = new AudioContext()
      const analyser = audioContext.createAnalyser()
      const microphone = audioContext.createMediaStreamSource(stream)
      microphone.connect(analyser)

      analyser.fftSize = 256
      const dataArray = new Uint8Array(analyser.frequencyBinCount)

      const updateAudioLevel = () => {
        if (!streamRef.current) return

        analyser.getByteFrequencyData(dataArray)
        const average = dataArray.reduce((a, b) => a + b) / dataArray.length
        setAudioLevel(average)

        // Detect speaking
        if (average > 20) {
          setIsSpeaking(true)
          if (speakingTimeoutRef.current) {
            clearTimeout(speakingTimeoutRef.current)
          }
          speakingTimeoutRef.current = window.setTimeout(() => {
            setIsSpeaking(false)
          }, 500)
        }

        animationRef.current = requestAnimationFrame(updateAudioLevel)
      }
      updateAudioLevel()

      return true

    } catch (error) {
      console.error('Error accessing microphone:', error)
      alert('Unable to access microphone. Please check your permissions.')
      return false
    }
  }

  const connectToSupport = async () => {
    if (!isConnected) {
      setConnectionStatus('connecting')

      try {
        // Get room token from your backend API
        const response = await fetch('http://localhost:8000/api/token', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        })

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const { token, url, session_id } = await response.json()
        console.log(`Starting support session: ${session_id}`)
        setSessionId(session_id)

        // Request microphone access first
        const micAccess = await requestMicrophoneAccess()
        if (!micAccess) {
          setConnectionStatus('disconnected')
          return
        }

        // Connect to LiveKit room
        const newRoom = new Room({
          // Configure room options
          adaptiveStream: true,
          dynacast: true,
        })

        // Set up event listeners
        newRoom.on(RoomEvent.Connected, () => {
          console.log('Connected to LiveKit room')
          setIsConnected(true)
          setConnectionStatus('connected')
          startCallTimer()
        })

        newRoom.on(RoomEvent.Disconnected, () => {
          console.log('Disconnected from LiveKit room')
          setIsConnected(false)
          setConnectionStatus('disconnected')
          setSessionId(null)
          stopCallTimer()
        })

        // Listen for remote audio (AI agent speaking)
        newRoom.on(RoomEvent.TrackSubscribed, (track: RemoteTrack) => {
          if (track.kind === Track.Kind.Audio) {
            console.log('AI agent audio track received')
            const audioElement = track.attach()
            audioElement.volume = 1.0
            document.body.appendChild(audioElement)
          }
        })

        // Handle track unsubscribed
        newRoom.on(RoomEvent.TrackUnsubscribed, (track: RemoteTrack) => {
          if (track.kind === Track.Kind.Audio) {
            track.detach()
          }
        })

        // Connect to room
        await newRoom.connect(url, token)

        // Enable microphone (no camera)
        await newRoom.localParticipant.setMicrophoneEnabled(true)

        roomRef.current = newRoom

      } catch (error) {
        console.error('Connection failed:', error)
        setConnectionStatus('disconnected')
        alert(`Failed to connect to support: ${error instanceof Error ? error.message : 'Unknown error'}`)
      }
    } else {
      // Disconnect
      if (roomRef.current) {
        await roomRef.current.disconnect()
        roomRef.current = null
      }

      setIsConnected(false)
      setConnectionStatus('disconnected')
      setSessionId(null)
      stopCallTimer()
      await stopMicrophone()
      console.log('Call ended')
    }
  }

  const stopMicrophone = async () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
      streamRef.current = null
    }
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current)
    }
    if (speakingTimeoutRef.current) {
      clearTimeout(speakingTimeoutRef.current)
    }
    setIsMicOn(false)
    setAudioLevel(0)
    setIsSpeaking(false)
  }

  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
      }
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
      if (callTimerRef.current) {
        clearInterval(callTimerRef.current)
      }
      if (speakingTimeoutRef.current) {
        clearTimeout(speakingTimeoutRef.current)
      }
      if (roomRef.current) {
        roomRef.current.disconnect()
      }
    }
  }, [])

  return (
    <div className="phone-container">
      <div className="phone-interface">
        <div className="phone-content">
          {/* Header */}
          <div className="phone-header">
          <div className="call-info">
            <div className={`contact-avatar ${isSpeaking ? 'speaking' : ''}`}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2C13.1 2 14 2.9 14 4C14 5.1 13.1 6 12 6C10.9 6 10 5.1 10 4C10 2.9 10.9 2 12 2ZM12 14.2C10.5 14.2 9.3 13.5 8.7 12.3L7 17H9L10.2 14H13.8L15 17H17L15.3 12.3C14.7 13.5 13.5 14.2 12 14.2ZM8 10C8 11.1 8.9 12 10 12H14C15.1 12 16 11.1 16 10V8C16 6.9 15.1 6 14 6H10C8.9 6 8 6.9 8 8V10Z" fill="currentColor"/>
              </svg>
              {isSpeaking && (
                <div className="speaking-rings">
                  <div className="ring ring-1"></div>
                  <div className="ring ring-2"></div>
                  <div className="ring ring-3"></div>
                </div>
              )}
            </div>
            <div className="contact-details">
              <h2 className="contact-name">DeskHelp Support</h2>
              <p className="contact-status">
                {connectionStatus === 'connecting' && 'Connecting...'}
                {connectionStatus === 'connected' && `Connected • ${formatCallDuration(callDuration)} ${sessionId ? `• Session: ${sessionId}` : ''}`}
                {connectionStatus === 'disconnected' && 'Available 24/7'}
              </p>
            </div>

            {connectionStatus === 'connecting' && (
              <div className="connecting-animation">
                <div className="connecting-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Main Content */}
        <div className="phone-content">
          {!isConnected ? (
            <div className="pre-call-info">
              <div className="service-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M20 15.5C18.75 15.5 17.55 15.3 16.43 14.93C16.08 14.82 15.69 14.9 15.41 15.17L13.21 17.37C10.38 15.93 8.06 13.62 6.62 10.79L8.82 8.58C9.1 8.31 9.18 7.92 9.07 7.57C8.7 6.45 8.5 5.25 8.5 4C8.5 3.45 8.05 3 7.5 3H4C3.45 3 3 3.45 3 4C3 13.39 10.61 21 20 21C20.55 21 21 20.55 21 20V16.5C21 15.95 20.55 15.5 20 15.5Z" fill="currentColor"/>
                </svg>
              </div>
              <div className="call-text">
                <h3>Professional Support</h3>
                <p>Connect with our expert support team for immediate assistance</p>
                <p className="api-status">Backend API: Ready • LiveKit: Ready</p>
              </div>
            </div>
          ) : (
            <div className="call-active-info">
              {/* Audio Visualizer */}
              {isMicOn && (
                <div className="audio-visualizer-container">
                  <div className="audio-waves">
                    {[...Array(7)].map((_, i) => (
                      <div 
                        key={i}
                        className={`wave-bar ${isSpeaking ? 'active' : ''}`}
                        style={{
                          height: isSpeaking ? `${15 + (audioLevel * (i + 1) * 0.3)}px` : '8px',
                          animationDelay: `${i * 0.1}s`
                        }}
                      />
                    ))}
                  </div>
                  <p className="visualizer-text">
                    {isSpeaking ? 'Speaking...' : 'Listening...'}
                  </p>
                </div>
              )}

              <div className="call-status">
                <div className="status-indicator">
                  <div className="status-dot connected"></div>
                  <span>Connected to AI Support Agent</span>
                  {sessionId && <span className="session-info"> • Session: {sessionId}</span>}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Controls */}
        <div className="phone-controls">
          <div className="primary-controls">
            <button 
              className={`call-btn ${isConnected ? 'end-call' : 'start-call'} ${connectionStatus === 'connecting' ? 'connecting' : ''}`}
              onClick={connectToSupport}
              disabled={connectionStatus === 'connecting'}
            >
              {connectionStatus === 'connecting' ? (
                <div className="spinner"></div>
              ) : isConnected ? (
                <>
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 9C10.5 9 9.26 9.78 8.65 10.87C8.24 11.25 8 11.61 8 12C8 12.39 8.24 12.75 8.65 13.13C9.26 14.22 10.5 15 12 15C13.5 15 14.74 14.22 15.35 13.13C15.76 12.75 16 12.39 16 12C16 11.61 15.76 11.25 15.35 10.87C14.74 9.78 13.5 9 12 9ZM20.1 15.5C18.75 15.5 17.55 15.3 16.43 14.93C16.08 14.82 15.69 14.9 15.41 15.17L13.21 17.37C10.38 15.93 8.06 13.62 6.62 10.79L8.82 8.58C9.1 8.31 9.18 7.92 9.07 7.57C8.7 6.45 8.5 5.25 8.5 4C8.5 3.45 8.05 3 7.5 3H4C3.45 3 3 3.45 3 4C3 13.39 10.61 21 20 21C20.55 21 21 20.55 21 20V16.5C21 15.95 20.55 15.5 20.1 15.5Z" fill="currentColor" transform="rotate(135 12 12)"/>
                  </svg>
                  <span>End Call</span>
                </>
              ) : (
                <>
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M20.01 15.38C18.78 15.38 17.59 15.18 16.48 14.82C16.13 14.7 15.74 14.79 15.47 15.06L13.9 17.03C11.07 15.68 8.42 13.13 7.01 10.2L8.96 8.54C9.23 8.26 9.31 7.87 9.2 7.52C8.83 6.41 8.64 5.22 8.64 3.99C8.64 3.45 8.19 3 7.65 3H4.19C3.65 3 3 3.24 3 3.99C3 13.28 10.73 21 20.01 21C20.72 21 21 20.37 21 19.82V16.37C21 15.83 20.55 15.38 20.01 15.38Z" fill="currentColor"/>
                  </svg>
                  <span>Call Support</span>
                </>
              )}
            </button>
          </div>
        </div>
        </div>

        {/* Footer */}
        <div className="phone-footer">
          <p className="footer-text">
            {isConnected 
              ? 'Microphone is active and ready for conversation with AI agent' 
              : 'Click to connect and start speaking with our AI support agent'
            }
          </p>
        </div>
      </div>
    </div>
  )
}

export default App
