import { useState } from "react";
import { useDaily } from "@daily-co/daily-react";
import { ArrowRight, Ear, Loader2 } from "lucide-react";

import Session from "./components/Session";
import { Configure, RoomSetup } from "./components/Setup";
import { Alert } from "./components/ui/alert";
import { Button } from "./components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "./components/ui/card";
import { fetch_start_agent } from "./actions";

type State =
  | "idle"
  | "configuring"
  | "requesting_agent"
  | "connecting"
  | "connected"
  | "started"
  | "finished"
  | "error";

const status_text = {
  configuring: "Let's go!",
  requesting_agent: "Requesting agent...",
  requesting_token: "Requesting token...",
  connecting: "Connecting to room...",
};

import { useAppConfig, getEnvConfig } from "./config";

// Get server URL from environment
const { serverUrl: envServerUrl } = getEnvConfig();
let serverUrl = envServerUrl;
if (serverUrl && !serverUrl.endsWith("/")) serverUrl += "/";

// Query string for room URL
const roomQs = new URLSearchParams(window.location.search).get("room_url");
const checkRoomUrl = (url: string | null): boolean =>
  !!(url && /^(https?:\/\/[^.]+(\.staging)?\.daily\.co\/[^/]+)$/.test(url));

export default function App() {
  const daily = useDaily();
  
  // Fetch configuration from the backend
  const { config, loading: configLoading } = useAppConfig(serverUrl);
  
  // Show config options (from backend or fallback to env)
  const showConfigOptions = config.show_config;
  
  // Mic mode (from backend or fallback to env)
  const isOpenMic = config.open_mic;
  
  // Auto room creation based on config from backend
  const autoRoomCreation = !config.manual_room_entry;

  const [state, setState] = useState<State>(
    showConfigOptions ? "idle" : "configuring"
  );
  const [error, setError] = useState<string | null>(null);
  const [startAudioOff, setStartAudioOff] = useState<boolean>(false);
  const [roomUrl, setRoomUrl] = useState<string | null>(roomQs || null);
  const [roomError, setRoomError] = useState<boolean>(
    (roomQs && checkRoomUrl(roomQs)) || false
  );

  function handleRoomUrl() {
    if ((autoRoomCreation && serverUrl) || checkRoomUrl(roomUrl)) {
      setRoomError(false);
      setState("configuring");
    } else {
      setRoomError(true);
    }
  }

  async function start() {
    console.log('Start function called');
    console.log('Daily:', daily ? 'exists' : 'null');
    console.log('Room URL:', roomUrl);
    console.log('Auto room creation:', autoRoomCreation);
    console.log('Config:', config);
    
    if (!daily) {
      console.error('Daily object is not initialized');
      setError('Daily object is not initialized. Please refresh the page and try again.');
      setState("error");
      return;
    }
    
    // If manual room entry is required (autoRoomCreation is false) and no room URL is provided
    if (!autoRoomCreation && !roomUrl) {
      console.log('No room URL and auto room creation is disabled');
      setError('Please enter a valid room URL or enable auto room creation in the backend config');
      setState("error");
      return;
    }

    let data;

    // Request agent to start, or join room directly
    if (serverUrl) {
      // If we have a server URL and either auto room creation is enabled or a room URL is provided
      if (autoRoomCreation || roomUrl) {
        console.log('Requesting agent with server URL:', serverUrl);
        // Request a new agent to join the room
        setState("requesting_agent");

        try {
          console.log('Calling fetch_start_agent with:', { roomUrl, serverUrl });
          // We're not sending roomUrl anymore as the backend generates it
          data = await fetch_start_agent(null, serverUrl);
          console.log('Response from fetch_start_agent:', data);

          if (data.error) {
            console.error('Error from fetch_start_agent:', data.detail);
            setError(data.detail);
            setState("error");
            return;
          }
        } catch (e) {
          console.error('Exception in fetch_start_agent:', e);
          setError(`Unable to connect to the bot server at '${serverUrl}'`);
          setState("error");
          return;
        }
      } else {
        console.log('Not calling backend because autoRoomCreation is disabled and no roomUrl provided');
      }
    } else {
      console.log('No server URL provided, skipping backend call');
    }

    // Join the daily session, passing through the url and token
    setState("connecting");

    try {
      // The backend returns 'url' but we're looking for 'room_url'
      const roomToJoin = data?.url || data?.room_url || roomUrl;
      console.log('Joining room:', roomToJoin);
      console.log('With token:', data?.token || "");
      
      await daily.join({
        url: roomToJoin,
        token: data?.token || "",
        videoSource: false,
        startAudioOff: startAudioOff,
      });
    } catch (e) {
      console.error('Error joining room:', e);
      setError(`Unable to join room: '${data?.url || data?.room_url || roomUrl}'`);
      setState("error");
      return;
    }
    // Away we go...
    setState("connected");
  }

  async function leave() {
    await daily?.leave();
    await daily?.destroy();
    setState(showConfigOptions ? "idle" : "configuring");
  }

  if (state === "error") {
    return (
      <Alert intent="danger" title="An error occurred">
        {error}
      </Alert>
    );
  }

  if (state === "connected") {
    return (
      <Session
        onLeave={() => leave()}
        openMic={isOpenMic}
        startAudioOff={startAudioOff}
      />
    );
  }

  // Debug state
  console.log('Current state:', state);
  console.log('Button would be disabled:', state !== "configuring");
  console.log('Daily object:', daily ? 'exists' : 'null');
  console.log('Room URL:', roomUrl);
  console.log('Auto room creation:', autoRoomCreation);
  console.log('Server URL:', serverUrl);
  
  if (state !== "idle") {
    return (
      <Card shadow className="animate-appear max-w-lg">
        <CardHeader>
          <CardTitle>Configure your devices</CardTitle>
          <CardDescription>
            Please configure your microphone and speakers below
          </CardDescription>
        </CardHeader>
        <CardContent stack>
          <div className="flex flex-row gap-2 bg-primary-50 px-4 py-2 md:p-2 text-sm items-center justify-center rounded-md font-medium text-pretty">
            <Ear className="size-7 md:size-5 text-primary-400" />
            Works best in a quiet environment with a good internet.
          </div>
          <Configure
            startAudioOff={startAudioOff}
            handleStartAudioOff={() => setStartAudioOff(!startAudioOff)}
          />
        </CardContent>
        <CardFooter>
          <Button
            key="start"
            fullWidthMobile
            onClick={() => {
              console.log('Start button clicked');
              start();
            }}
            disabled={state !== "configuring"}
          >
            {state !== "configuring" && <Loader2 className="animate-spin" />}
            {status_text[state as keyof typeof status_text] || "Let's go!"}
          </Button>
        </CardFooter>
      </Card>
    );
  }

  return (
    <Card shadow className="animate-appear max-w-lg">
      <CardHeader>
        <CardTitle>Pipecat {import.meta.env.VITE_APP_TITLE}</CardTitle>
        <CardDescription>Check configuration below</CardDescription>
      </CardHeader>
      <CardContent stack>
        <RoomSetup
          serverUrl={serverUrl}
          roomQs={roomQs}
          roomQueryStringValid={checkRoomUrl(roomQs)}
          handleCheckRoomUrl={(url) => setRoomUrl(url)}
          roomError={roomError}
        />
      </CardContent>
      <CardFooter>
        <Button
          id="nextBtn"
          fullWidthMobile
          key="next"
          disabled={
            !!((roomQs && !roomError) || (autoRoomCreation && !serverUrl))
          }
          onClick={() => handleRoomUrl()}
        >
          Next <ArrowRight />
        </Button>
      </CardFooter>
    </Card>
  );
}
