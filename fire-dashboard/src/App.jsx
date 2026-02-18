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

  const min = Math.min(...data);
  const max = Math.max(...data);

  const normalize = (value) => {
    return (value - min) / (max - min || 1);
  };

  return (
    <div className="w-64 h-64 grid grid-cols-8 rounded-lg overflow-hidden">
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
  );
}

/* ================= MAIN APP ================= */

export default function App() {
  const [sensor, setSensor] = useState(null);
  const [vision, setVision] = useState(null);
  const [alert, setAlert] = useState(null);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    const fetchData = () => {
      fetch(`${API}/sensors/latest`)
        .then(r => r.json())
        .then(setSensor)
        .catch(() => setSensor(null));

      fetch(`${API}/vision/latest`)
        .then(r => r.json())
        .then(setVision)
        .catch(() => setVision(null));

      fetch(`${API}/alerts/latest`)
        .then(r => r.json())
        .then(setAlert)
        .catch(() => setAlert(null));

      fetch(`${API}/alerts/history`)
        .then(r => r.json())
        .then(setHistory)
        .catch(() => setHistory([]));
    };

    fetchData();
    const interval = setInterval(fetchData, 1000);
    return () => clearInterval(interval);
  }, []);

  const fireActive = vision?.detected;
  const alertActive = alert && alert.status !== "NO_ALERT";

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-8">
      <h1 className="text-3xl font-bold mb-10">
        🔥 Fire Detection Dashboard
      </h1>

      {/* ================= NEW GRID LAYOUT ================= */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

        {/* ========== LIVE CAMERA (LEFT SIDE, 2 ROWS) ========== */}
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

        {/* ========== THERMAL (TOP RIGHT) ========== */}
        <Card title="Thermal Camera (8x8)">
          {sensor?.thermal ? (
            <div className="flex justify-center">
              <ThermalGrid data={sensor.thermal} />
            </div>
          ) : (
            <p>No thermal data</p>
          )}
        </Card>

        {/* ========== VISION (BOTTOM RIGHT) ========== */}
        <Card
          title="Vision AI"
          className={
            fireActive
              ? "border-2 border-red-500 shadow-red-500/30"
              : ""
          }
        >
          {vision ? (
            <div className="space-y-3">
              <p className="text-lg">
                Fire Detected:{" "}
                <span className={fireActive ? "text-red-400 font-bold" : ""}>
                  {fireActive ? "🔥 YES" : "No"}
                </span>
              </p>

              <p>
                Confidence:{" "}
                {vision.confidence
                  ? vision.confidence.toFixed(3)
                  : "0.000"}
              </p>

              <p>
                Updated:{" "}
                <Freshness timestamp={vision.timestamp} />
              </p>
            </div>
          ) : (
            <p>No vision data</p>
          )}
        </Card>

        {/* ========== SENSORS ========== */}
        <Card title="Sensors">
          {sensor ? (
            <div className="space-y-3">
              <p>
                Flame: {sensor.flame ? "🔥 DETECTED" : "No flame"}
              </p>
              <p>MQ135: {sensor.mq135_raw}</p>
              <p>
                Thermal Max:{" "}
                {sensor.thermal
                  ? Math.max(...sensor.thermal).toFixed(2)
                  : "N/A"}
              </p>
              <p>
                Updated:{" "}
                <Freshness timestamp={sensor.timestamp} />
              </p>
            </div>
          ) : (
            <p>No sensor data</p>
          )}
        </Card>

        {/* ========== CURRENT ALERT ========== */}
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
              <p>Status: {alert.status}</p>
              <p>Type: {alert.type}</p>
              <p>Source: {alert.source}</p>
              <p>Confidence: {alert.confidence}</p>
              <p>
                Updated:{" "}
                <Freshness timestamp={alert.updated_at} />
              </p>
            </div>
          ) : (
            <p>No active alert</p>
          )}
        </Card>

        {/* ========== ALERT HISTORY ========== */}
        <Card title="Alert History">
          {history.length > 0 ? (
            <ul className="space-y-2 text-sm">
              {history.slice(0, 5).map((a, i) => (
                <li
                  key={i}
                  className="border-b border-gray-700 pb-2"
                >
                  {a.type} | {a.status}
                </li>
              ))}
            </ul>
          ) : (
            <p>No alerts yet</p>
          )}
        </Card>

      </div>
    </div>
  );
}
