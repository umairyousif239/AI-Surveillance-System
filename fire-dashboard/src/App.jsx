import { useEffect, useState } from "react";

const API = "http://127.0.0.1:8000";

/* ================= CARD COMPONENT ================= */

function Card({ title, children, className = "" }) {
  return (
    <div
      className={`bg-gray-800 rounded-2xl p-6 shadow-xl border border-gray-700 ${className}`}
    >
      <h2 className="text-lg font-semibold mb-4 text-gray-200">
        {title}
      </h2>
      {children}
    </div>
  );
}

/* ================= DATA FRESHNESS INDICATOR ================= */

function Freshness({ timestamp }) {
  const [age, setAge] = useState(0);

  useEffect(() => {
    if (!timestamp) return;

    const updateAge = () => {
      setAge(Date.now() - new Date(timestamp).getTime());
    };

    updateAge();
    const interval = setInterval(updateAge, 1000);
    return () => clearInterval(interval);
  }, [timestamp]);

  if (!timestamp) return <span className="text-red-500">●</span>;

  let color = "text-red-500";
  if (age < 1000) color = "text-green-400";
  else if (age < 5000) color = "text-yellow-400";

  return (
    <span className={`${color} font-medium`}>
      ● {Math.round(age / 1000)}s
    </span>
  );
}

/* ================= THERMAL GRID ================= */

function ThermalGrid({ data }) {
  if (!data || data.length !== 64) {
    return <p>No thermal data</p>;
  }

  // 🔥 Fixed temperature scale
  const MIN_TEMP = 20;   // lowest expected ambient
  const MAX_TEMP = 50;   // fire-relevant upper bound

  const clamp = (val, min, max) => Math.min(Math.max(val, min), max);

  const normalize = (value) => {
    const clamped = clamp(value, MIN_TEMP, MAX_TEMP);
    return (clamped - MIN_TEMP) / (MAX_TEMP - MIN_TEMP);
  };

  return (
    <div className="flex items-start gap-6">

      {/* 8x8 Thermal Grid */}
      <div className="w-64 h-64 grid grid-cols-8 rounded-lg overflow-hidden shadow-inner">
        {data.map((value, i) => {
          const intensity = normalize(value);
          const red = Math.floor(255 * intensity);
          const blue = Math.floor(255 * (1 - intensity));

          return (
            <div
              key={i}
              className="w-full h-full"
              style={{
                backgroundColor: `rgb(${red},0,${blue})`
              }}
            />
          );
        })}
      </div>

      {/* Fixed Scale Legend */}
      <div className="flex flex-col items-center h-64 justify-between">

        {/* Max */}
        <span className="text-sm text-gray-300">
          {MAX_TEMP}°C
        </span>

        {/* Gradient */}
        <div
          className="w-6 flex-1 my-2 rounded-md"
          style={{
            background: "linear-gradient(to top, blue, cyan, yellow, red)"
          }}
        />

        {/* Min */}
        <span className="text-sm text-gray-300">
          {MIN_TEMP}°C
        </span>

      </div>
    </div>
  );
}


/* ================= CONFIDENCE BAR ================= */

function ConfidenceBar({ value }) {
  const percentage = Math.min(Math.max(value * 100, 0), 100);

  return (
    <div className="w-full">
      <div className="flex justify-between text-sm mb-1">
        <span>Confidence</span>
        <span>{percentage.toFixed(1)}%</span>
      </div>

      <div className="w-full h-3 bg-gray-700 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-blue-500 via-yellow-400 to-red-500 transition-all duration-300"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
/* ================= LOGIN COMPONENTS ================= */

function Login ({ setToken }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");

    // FastAPI's OAuth2 auth strictly requires form data, not JSON!
    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);

    try {
      const response = await fetch(`${API}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        // securely vault the token and update the app state
        localStorage.setItem("token", data.access_token);
        setToken(data.access_token);
      } else {
        setError(data.detail || "Invalid credentials");
      }
    } catch {
      setError("Cannot connect to server. Check the FastAPI status.");
    }
  };
  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4 font-sans text-gray-100">
      <Card title="System Login" className="w-full max-w-md border-gray-700 bg-gray-800">
        <form onSubmit={handleLogin} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Admin Username</label>
            <input 
              type="text" 
              value={username} 
              onChange={(e) => setUsername(e.target.value)}
              className="w-full bg-gray-900 border border-gray-700 rounded-lg p-3 text-gray-200 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
              required 
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Password</label>
            <input 
              type="password" 
              value={password} 
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-gray-900 border border-gray-700 rounded-lg p-3 text-gray-200 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
              required 
            />
          </div>
          
          {error && <p className="text-red-400 text-sm font-medium bg-red-900/20 p-2 rounded">{error}</p>}
          
          <button 
            type="submit" 
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-lg transition-all mt-2 shadow-lg shadow-blue-900/20"
          >
            Authenticate
          </button>
        </form>
      </Card>
    </div>
  );
}


/* ================= MAIN APP ================= */

export default function App() {
  // check local storage for saved token on boot
  const [token, setToken] = useState(localStorage.getItem("token"));

  const [sensor, setSensor] = useState(null);
  const [vision, setVision] = useState(null);
  const [alert, setAlert] = useState(null);
  const [history, setHistory] = useState([]);

  // kicks user out and deletes token on logout
  const handleLogout = () => {
    localStorage.removeItem("token");
    setToken(null);
  };

  useEffect(() => {
    if (!token) return; // stop fetching data if user logs out

    const fetchData = () => {
      // Creating the VIP pass Header
      const headers = { "Authorization": `Bearer ${token}` };

      // helper function to attach headers and catch expired tokens
      const fetchWithAuth = (url, setter) => {
        fetch(url, { headers })
        .then(res => {
          if (res.status === 401) {
            handleLogout();
            throw new Error("Unauthorized");
          }
          return res.json();
        })
        .then(setter)
        .catch(() => setter(null));
      };
      fetchWithAuth(`${API}/sensors/latest`, setSensor);
      fetchWithAuth(`${API}/vision/latest`, setVision);
      fetchWithAuth(`${API}/alerts/latest`, setAlert);
      fetchWithAuth(`${API}/alerts/history`, setHistory);
    };

    fetchData();
    const interval = setInterval(fetchData, 1000);
    return () => clearInterval(interval);
  }, [token]); // react re-runs this loop whenever the token changes

  // The Gatekeeper: if there is no token, show the logic screen
  if (!token) {
    return <Login setToken={setToken} />;
  }

  const fireActive = vision?.detected;
  const alertActive = alert && (alert.status === "NEW" || alert.status === "ACTIVE" || alert.status === "AlertStatus.NEW" || alert.status === "AlertStatus.ACTIVE");

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-8">
      {/* Header with Logout Button */}
      <div className="flex justify-between items-center mb-10">
        <h1 className="text-3xl font-bold">
          🔥 AI Fire and Smoke Surveillance System
        </h1>
        <button 
          onClick={handleLogout} 
          className="bg-red-600/80 hover:bg-red-600 px-4 py-2 rounded-lg font-bold text-sm transition-colors border border-red-500"
        >
          Logout
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

        {/* LIVE CAMERA */}
        <Card
          title="Live Camera"
          className="lg:col-span-2 lg:row-span-2"
        >
          <img
            src={`${API}/vision/video_feed`}
            alt="Live Feed"
            className="rounded-xl w-full border border-gray-700"
          />
        </Card>

        {/* THERMAL WITH LEGEND */}
        <Card title="Thermal Camera (8x8)">
          {sensor?.thermal ? (
            <ThermalGrid data={sensor.thermal} />
          ) : (
            <p>No thermal data</p>
          )}
        </Card>

        {/* VISION WITH CONFIDENCE BAR */}
        <Card
          title="Vision AI"
          className={
            fireActive
              ? "border-2 border-red-500 shadow-red-500/30"
              : ""
          }
        >
          {vision ? (
            <div className="space-y-4">

              <p className="text-lg">
                Fire Detected:{" "}
                <span className={fireActive ? "text-red-400 font-bold" : ""}>
                  {fireActive ? "🔥 YES" : "No"}
                </span>
              </p>

              <ConfidenceBar value={vision.confidence || 0} />

              <p>
                Updated:{" "}
                <Freshness timestamp={vision.timestamp} />
              </p>

            </div>
          ) : (
            <p>No vision data</p>
          )}
        </Card>

        {/* CURRENT ALERT */}
        <Card
          title="Current Alert"
          className={
            alertActive
              ? "border-2 border-red-600 animate-pulse"
              : ""
          }
        >
          {alertActive ? (
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <p>Status: <span className="font-bold text-red-400">{alert.status}</span></p>
                {/* 1. SEVERITY BADGE */}
                {alert.severity && (
                  <span className={`text-xs px-2 py-1 rounded font-bold ${
                    alert.severity === 'HIGH' ? 'bg-red-900 text-red-200' : 
                    alert.severity === 'MEDIUM' ? 'bg-yellow-900 text-yellow-200' : 
                    'bg-blue-900 text-blue-200'
                  }`}>
                    {alert.severity} SEVERITY
                  </span>
                )}
              </div>
              
              <p>Type: <span className="font-semibold">{alert.type}</span></p>
              
              <div className="flex justify-between items-center">
                <p>Confidence: {alert.confidence}</p>
                <p className="text-sm">
                  Updated: <Freshness timestamp={alert.updated_at} />
                </p>
              </div>

              {/* 2. ACTIVE TRIGGERS (Optional detail block) */}
              {alert.signals && (
                <div className="mt-4 pt-3 border-t border-gray-700 text-sm">
                  <p className="text-gray-400 mb-1">Active Triggers:</p>
                  <div className="flex flex-wrap gap-2 text-xs">
                    {alert.signals.vision_fire && <span className="bg-gray-700 px-2 py-1 rounded text-red-300">📸 Vision AI</span>}
                    {alert.signals.smoke && <span className="bg-gray-700 px-2 py-1 rounded text-gray-300">💨 Smoke</span>}
                    {alert.signals.flame && <span className="bg-gray-700 px-2 py-1 rounded text-orange-300">🔥 IR Flame</span>}
                    {(alert.signals.max_temp >= 50 || alert.signals.delta_temp >= 15) && 
                      <span className="bg-gray-700 px-2 py-1 rounded text-pink-300">🌡️ Thermal Spike</span>
                    }
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500 pb-4">
              <p>No active threats</p>
            </div>
          )}
        </Card>

        {/* ALERT HISTORY */}
        <Card title="Alert History">
          {history.length > 0 ? (
            <ul className="space-y-2 text-sm">
              {history.slice(0, 5).map((a, i) => {
                
                const displayStatus = a.status.replace("AlertStatus.", "");
                
                let timestampToUse = a.created_at; 
                if (displayStatus === "RESOLVED" && a.resolved_at) {
                  timestampToUse = a.resolved_at;
                } else if (displayStatus === "ACTIVE" && a.updated_at) {
                  timestampToUse = a.updated_at;
                }

                const timeString = timestampToUse 
                  ? new Date(timestampToUse).toLocaleTimeString() 
                  : "--:--";

                // Determine severity color
                const sevColor = a.severity === 'HIGH' ? 'text-red-500' : 
                                 a.severity === 'MEDIUM' ? 'text-yellow-500' : 'text-blue-500';

                return (
                  <li
                    key={i}
                    className="border-b border-gray-700 pb-2 flex justify-between items-center"
                  >
                    <span className="flex items-center gap-2">
                      <span title={`${a.severity} Severity`} className={`${sevColor} text-[10px]`}>⬤</span>
                      <span className="font-semibold text-gray-200">{a.type}</span> 
                      
                      {/* Source Tag */}
                      <span className="text-[10px] bg-gray-700 px-1.5 py-0.5 rounded text-gray-300">
                        {a.source}
                      </span>

                      {/* NEW: Confidence Badge */}
                      <span className="text-[10px] bg-gray-800 border border-gray-600 px-1.5 py-0.5 rounded text-gray-400" title="Confidence Score">
                        {a.confidence}
                      </span>
                      
                      <span className="text-gray-400">|</span> 
                      
                      <span className={
                        displayStatus === "ACTIVE" ? "text-red-400 font-semibold animate-pulse" : 
                        displayStatus === "RESOLVED" ? "text-green-400" : "text-yellow-400"
                      }>
                        {displayStatus}
                      </span>
                    </span>
                    <span className="text-gray-500 text-xs">
                      {timeString}
                    </span>
                  </li>
                );
              })}
            </ul>
          ) : (
            <p className="text-gray-500">No alerts yet</p>
          )}
        </Card>

        {/* SENSORS */}
        <Card title="Sensors">
          {sensor ? (
            <div className="space-y-4">
              
              {/* Flame Status */}
              <div className="flex justify-between items-center pb-2 border-b border-gray-700">
                <span className="text-gray-400">IR Flame Sensor</span>
                <span className={sensor.flame ? "text-orange-400 font-bold bg-orange-900/30 px-2 py-1 rounded" : "text-gray-300"}>
                  {sensor.flame ? "🔥 DETECTED" : "Clear"}
                </span>
              </div>

              {/* MQ135 Gas Bar */}
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-400">Air Quality (MQ135)</span>
                  <span className={sensor.mq135_raw >= 300 ? "text-red-400 font-bold" : "text-gray-300"}>
                    {sensor.mq135_raw} <span className="text-xs text-gray-500">/ 500</span>
                  </span>
                </div>
                <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden border border-gray-700">
                  <div
                    className={`h-full transition-all duration-300 ${
                      sensor.mq135_raw >= 300 ? 'bg-red-500' : 
                      sensor.mq135_raw >= 150 ? 'bg-yellow-500' : 'bg-green-500'
                    }`}
                    style={{ width: `${Math.min((sensor.mq135_raw / 500) * 100, 100)}%` }}
                  />
                </div>
              </div>

              {/* Thermal Data */}
              <div className="flex justify-between items-center text-sm pt-2">
                <span className="text-gray-400">Thermal Max</span>
                <span className="font-mono">{sensor.thermal ? Math.max(...sensor.thermal).toFixed(1) : "N/A"} °C</span>
              </div>

              {/* Freshness (FIXED) */}
              <div className="pt-2 text-xs border-t border-gray-700 mt-2">
                <span className="text-green-400 font-medium flex items-center gap-2 mt-2">
                  <span className="animate-pulse">●</span> Live Stream
                </span>
              </div>
              
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500 pb-4">
              <p>Waiting for sensor telemetry...</p>
            </div>
          )}
        </Card>

      </div>
    </div>
  );
}
