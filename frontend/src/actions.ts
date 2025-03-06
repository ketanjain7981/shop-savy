export const fetch_start_agent = async (
  serverUrl: string
) => {
  // Ensure we don't have double slashes in the URL
  const url = serverUrl.endsWith('/') ? `${serverUrl}connect` : `${serverUrl}/connect`;
  
  try {
    // No need to send room URL as it's generated by the backend
    const req = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({}),
    });

    const data = await req.json();

    if (!req.ok) {
      console.error("Error connecting to agent:", data);
      return { error: true, detail: data.detail || "Failed to connect" };
    }
    return data;
  } catch (error) {
    console.error("Exception connecting to agent:", error);
    return { error: true, detail: "Network error connecting to server" };
  }
};
