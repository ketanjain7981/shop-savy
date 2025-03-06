import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom/client";
import { DailyProvider } from "@daily-co/daily-react";

import Header from "./components/ui/header.tsx";
import { TooltipProvider } from "./components/ui/tooltip.tsx";
import App from "./App.tsx";
import Splash from "./Splash.tsx";
import { useAppConfig, getEnvConfig } from "./config.ts";

import "./global.css"; // Note: Core app layout can be found here

// Get environment variables
const { serverUrl } = getEnvConfig();

// We'll set the initial splash page state from env var, but it will be updated
// once we fetch the config from the backend in the Layout component
const showSplashPage = import.meta.env.VITE_SHOW_SPLASH ? true : false;

// Show warning on Firefox
// @ts-expect-error - Firefox is not supported
const isFirefox: boolean = typeof InstallTrigger !== "undefined";

export const Layout = () => {
  // Initialize with environment variable, then update from backend config
  const [showSplash, setShowSplash] = useState<boolean>(showSplashPage);
  
  // Fetch configuration from the backend
  const { config, loading } = useAppConfig(serverUrl);
  
  // Update splash screen setting when config is loaded
  useEffect(() => {
    if (!loading) {
      setShowSplash(config.show_splash);
    }
  }, [loading, config]);

  if (showSplash) {
    return <Splash handleReady={() => setShowSplash(false)} />;
  }

  return (
    <DailyProvider
      dailyConfig={{
        // Ensure Daily is properly initialized
        // @ts-ignore
        experimentalChromeVideoTrackOptimizations: true,
        // Ensure audio is properly handled
        useDevicePreferencesApi: true,
      }}
    >
      <TooltipProvider>
        <main>
          <Header />
          <div id="app">
            <App />
          </div>
        </main>
        <aside id="tray" />
      </TooltipProvider>
    </DailyProvider>
  );
};

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    {isFirefox && (
      <div className="bg-red-500 text-white text-sm font-bold text-center p-2 fixed t-0 w-full">
        Voice activity detection not supported in Firefox. For best results,
        please use Chrome or Edge.
      </div>
    )}
    <Layout />
  </React.StrictMode>
);
