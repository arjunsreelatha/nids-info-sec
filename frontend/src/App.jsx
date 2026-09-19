import { useEffect, useState } from "react";
import { IS_MOCK, loadEvents } from "./api.js";
import Overview from "./components/Overview.jsx";
import Charts from "./components/Charts.jsx";
import EventsTable from "./components/EventsTable.jsx";
import DetectionDetail from "./components/DetectionDetail.jsx";

export default function App() {
  const [events, setEvents] = useState([]);
  const [selectedId, setSelectedId] = useState(null);

  useEffect(() => { loadEvents().then(setEvents); }, []);
  const selected = events.find((e) => e.id === selectedId);

  return (
    <main>
      <header>
        <h1>Hybrid RF + Autoencoder NIDS</h1>
        {IS_MOCK && <span className="mock">MOCK DATA - not real detections</span>}
      </header>
      <Overview events={events} />
      <Charts events={events} />
      <div className="grid">
        <EventsTable events={events} selectedId={selectedId} onSelect={setSelectedId} />
        <DetectionDetail event={selected} />
      </div>
    </main>
  );
}
